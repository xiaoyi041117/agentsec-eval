"""Run a paired baseline-vs-hardened evaluation against one local model."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from agentsec_eval.adapters import OllamaAdapter, OpenAICompatibleAdapter  # noqa: E402
from agentsec_eval.engine import EvaluationConfig, EvaluationEngine, wilson_interval  # noqa: E402
from agentsec_eval.scenarios import (  # noqa: E402
    SYNTHETIC_MARKER_PREFIX,
    basic_scenarios,
    challenge_scenarios,
    tool_capability_control,
)


def _aggregate(findings) -> dict[str, float | int]:
    trials = len(findings)
    violations = sum(row.violated for row in findings)
    marker_exposures = sum(row.marker_exposed for row in findings)
    weighted_latency = sum(row.latency_s for row in findings)
    ci_low, ci_high = wilson_interval(violations, trials)
    return {
        "trials": trials,
        "violations": violations,
        "violation_rate": violations / trials if trials else 0.0,
        "ci_low": ci_low,
        "ci_high": ci_high,
        "marker_exposures": marker_exposures,
        "mean_latency_s": weighted_latency / trials if trials else 0.0,
    }


def exact_mcnemar_p(baseline_only: int, hardened_only: int) -> float:
    """Two-sided exact McNemar p-value from discordant paired outcomes."""

    discordant = baseline_only + hardened_only
    if discordant == 0:
        return 1.0
    tail = sum(
        math.comb(discordant, value) for value in range(min(baseline_only, hardened_only) + 1)
    ) / (2**discordant)
    return min(1.0, 2.0 * tail)


def _markdown(
    model: str,
    baseline: dict,
    hardened: dict,
    attempted_pairs: int,
    paired_valid: int,
    context_tokens: int | None,
    max_tokens: int,
    scenario_set: str,
    baseline_only: int,
    hardened_only: int,
    mcnemar_p: float,
) -> str:
    delta = float(hardened["violation_rate"]) - float(baseline["violation_rate"])
    context_label = str(context_tokens) if context_tokens is not None else "server-managed"
    return f"""# Paired local safety comparison

Model: `{model}`

Runtime settings: temperature `0`, context window `{context_label}`, maximum generated tokens `{max_tokens}`, simulated tools only.

Scenario set: `{scenario_set}`.

The two conditions use the same scenarios, case identifiers, trial count, temperature, and simulated tools. The only intended difference is the system-level authorization boundary. Tool requests are recorded but never executed.

Attempted pairs: **{attempted_pairs}**. Valid complete pairs: **{paired_valid}**. Only pairs with successful responses in both conditions are included below.

| Condition | Trials | Violations | Violation rate (95% Wilson CI) | Marker exposures | Mean latency |
|---|---:|---:|---:|---:|---:|
| Baseline | {baseline['trials']} | {baseline['violations']} | {float(baseline['violation_rate']):.1%} ({float(baseline['ci_low']):.1%}-{float(baseline['ci_high']):.1%}) | {baseline['marker_exposures']} | {float(baseline['mean_latency_s']):.2f}s |
| Hardened | {hardened['trials']} | {hardened['violations']} | {float(hardened['violation_rate']):.1%} ({float(hardened['ci_low']):.1%}-{float(hardened['ci_high']):.1%}) | {hardened['marker_exposures']} | {float(hardened['mean_latency_s']):.2f}s |

Violation-rate delta (hardened minus baseline): **{delta:+.1%}**.

Discordant pairs: baseline-only violations **{baseline_only}**; hardened-only violations **{hardened_only}**. Two-sided exact McNemar p-value: **{mcnemar_p:.4f}**.

This result measures the effect of an inference-time authorization wrapper. It does not show that model weights were retrained or that the original Kaggle submission score changed.
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Paired baseline/hardened local model comparison")
    parser.add_argument("--backend", choices=("ollama", "openai"), default="ollama")
    parser.add_argument("--base-url", default="http://127.0.0.1:11434")
    parser.add_argument("--model", default="deepseek-r1:1.5b")
    parser.add_argument("--trials-per-scenario", type=int, default=3)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--max-tokens", type=int, default=128)
    parser.add_argument("--context-tokens", type=int, default=4096)
    parser.add_argument("--scenario-set", choices=("basic", "challenge"), default="basic")
    parser.add_argument("--skip-capability-check", action="store_true")
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts/comparison"))
    args = parser.parse_args()

    scenarios = challenge_scenarios() if args.scenario_set == "challenge" else basic_scenarios()
    per_scenario = max(1, args.trials_per_scenario)
    config = EvaluationConfig(
        seed=args.seed,
        total_trials=per_scenario * len(scenarios),
        min_trials_per_scenario=per_scenario,
        max_trials_per_scenario=per_scenario,
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    adapter_class = OllamaAdapter if args.backend == "ollama" else OpenAICompatibleAdapter
    base_url = args.base_url
    if args.backend == "openai" and not base_url.rstrip("/").endswith("/v1"):
        base_url = base_url.rstrip("/") + "/v1"
    runtime_context = args.context_tokens if args.backend == "ollama" else None

    def build_adapter(policy_mode: str):
        kwargs = {"policy_mode": policy_mode, "max_tokens": args.max_tokens}
        if args.backend == "ollama":
            kwargs["context_tokens"] = args.context_tokens
        return adapter_class(base_url, args.model, **kwargs)

    baseline_adapter = build_adapter("baseline")
    if not args.skip_capability_check:
        control = tool_capability_control()
        control_case = "positive-control-0000"
        marker = f"{SYNTHETIC_MARKER_PREFIX}_{control_case}"
        control_result = baseline_adapter.evaluate(
            control,
            control.render(control_case, marker),
            control_case,
            1,
        )
        passed = any(call.name == control.target_tool for call in control_result.tool_calls)
        capability = {
            "model": args.model,
            "passed": passed,
            "requested_tools": [call.name for call in control_result.tool_calls],
            "latency_s": control_result.latency_s,
            "error": control_result.error,
            "context_tokens": runtime_context,
            "max_tokens": args.max_tokens,
            "status": "ready" if passed else "inconclusive_no_structured_tool_call",
        }
        (args.output_dir / "capability-check.json").write_text(
            json.dumps(capability, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        if not passed:
            message = (
                "A/B comparison is inconclusive: the positive control produced no structured "
                "tool call. Use a tool-capable instruct model/runtime before comparing policies."
            )
            (args.output_dir / "README.md").write_text(
                f"# Inconclusive local comparison\n\nModel: `{args.model}`\n\n{message}\n",
                encoding="utf-8",
            )
            print(message)
            return

    reports = {}
    for mode in ("baseline", "hardened"):
        adapter = (
            baseline_adapter
            if mode == "baseline"
            else build_adapter(mode)
        )
        checkpoint = args.output_dir / f"{mode}-trials.jsonl"
        checkpoint.write_text("", encoding="utf-8")
        report = EvaluationEngine(
            adapter,
            scenarios,
            config,
            checkpoint_path=checkpoint,
        ).run()
        reports[mode] = report
        (args.output_dir / f"{mode}-report.json").write_text(
            json.dumps(report.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8"
        )

    baseline_by_case = {row.case_id: row for row in reports["baseline"].findings}
    hardened_by_case = {row.case_id: row for row in reports["hardened"].findings}
    paired_case_ids = sorted(
        case_id
        for case_id in baseline_by_case.keys() & hardened_by_case.keys()
        if baseline_by_case[case_id].error is None and hardened_by_case[case_id].error is None
    )
    baseline = _aggregate([baseline_by_case[case_id] for case_id in paired_case_ids])
    hardened = _aggregate([hardened_by_case[case_id] for case_id in paired_case_ids])
    baseline_only = sum(
        baseline_by_case[case_id].violated and not hardened_by_case[case_id].violated
        for case_id in paired_case_ids
    )
    hardened_only = sum(
        hardened_by_case[case_id].violated and not baseline_by_case[case_id].violated
        for case_id in paired_case_ids
    )
    mcnemar_p = exact_mcnemar_p(baseline_only, hardened_only)
    attempted_pairs = per_scenario * len(scenarios)
    comparison = {
        "model": args.model,
        "seed": args.seed,
        "backend": args.backend,
        "temperature": 0,
        "context_tokens": runtime_context,
        "max_tokens": args.max_tokens,
        "scenario_set": args.scenario_set,
        "trials_per_scenario": per_scenario,
        "attempted_pairs": attempted_pairs,
        "valid_complete_pairs": len(paired_case_ids),
        "excluded_incomplete_pairs": attempted_pairs - len(paired_case_ids),
        "baseline": baseline,
        "hardened": hardened,
        "violation_rate_delta": hardened["violation_rate"] - baseline["violation_rate"],
        "discordant_pairs": {
            "baseline_only_violation": baseline_only,
            "hardened_only_violation": hardened_only,
        },
        "mcnemar_exact_two_sided_p": mcnemar_p,
    }
    (args.output_dir / "comparison.json").write_text(
        json.dumps(comparison, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    summary = _markdown(
        args.model,
        baseline,
        hardened,
        attempted_pairs,
        len(paired_case_ids),
        runtime_context,
        args.max_tokens,
        args.scenario_set,
        baseline_only,
        hardened_only,
        mcnemar_p,
    )
    (args.output_dir / "README.md").write_text(summary, encoding="utf-8")
    print(summary)


if __name__ == "__main__":
    main()
