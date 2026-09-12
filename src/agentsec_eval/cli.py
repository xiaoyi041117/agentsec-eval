from __future__ import annotations

import argparse
import json
from pathlib import Path

from .adapters import MockAgentAdapter, OpenAICompatibleAdapter
from .engine import EvaluationConfig, EvaluationEngine
from .scenarios import default_scenarios


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Side-effect-free AI agent tool-use safety evaluation")
    parser.add_argument("--adapter", choices=("mock", "openai"), default="mock")
    parser.add_argument("--model", default="mock-qwen")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000/v1")
    parser.add_argument("--policy-mode", choices=("baseline", "hardened"), default="hardened")
    parser.add_argument("--max-tokens", type=int, default=256)
    parser.add_argument("--trials", type=int, default=40)
    parser.add_argument("--min-trials", type=int, default=5)
    parser.add_argument("--max-trials", type=int, default=50)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=Path, default=Path("report.json"))
    parser.add_argument("--checkpoint", type=Path)
    return parser


def main() -> None:
    args = _parser().parse_args()
    if args.adapter == "openai":
        adapter = OpenAICompatibleAdapter(
            args.base_url,
            args.model,
            policy_mode=args.policy_mode,
            max_tokens=args.max_tokens,
        )
    else:
        adapter = MockAgentAdapter(args.model, args.seed)
    config = EvaluationConfig(
        seed=args.seed,
        total_trials=args.trials,
        min_trials_per_scenario=args.min_trials,
        max_trials_per_scenario=args.max_trials,
    )
    report = EvaluationEngine(
        adapter,
        default_scenarios(),
        config,
        checkpoint_path=args.checkpoint,
    ).run()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {args.output}")
    for row in report.summaries:
        print(
            f"{row.scenario_id}: {row.violations}/{row.trials} "
            f"({row.violation_rate:.1%}, 95% CI {row.ci_low:.1%}-{row.ci_high:.1%})"
        )


if __name__ == "__main__":
    main()
