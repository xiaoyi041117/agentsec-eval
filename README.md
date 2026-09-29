# AgentSec Eval

Reproducible, side-effect-free security evaluation for tool-using language-model agents.

This repository turns an AI Agent Security competition submission into an auditable engineering project. The original work optimized replayable attack candidates for a private sandbox. The refactored framework instead measures unauthorized tool requests without executing network, email, file-system, or shell side effects.

## Why this project exists

An early competition strategy used a `SECRET_MARKER` exfiltration path. During the competition, the team hypothesized that marker-dependent exfiltration might not transfer to hidden defenses. Private leaderboard results were only available after the competition ended; an observed public/private score collapse was not the trigger for the strategy change.

1. The competition solution moved to a `CONFUSED_DEPUTY` path that did not depend on the protected marker and selected prompts using model-specific execution traces.
2. The post-competition project replaced leaderboard-specific generation with a portable safety-evaluation harness that reports uncertainty and preserves an audit trail.

The result is both a record of the original experimental iteration and a safer foundation for local model evaluation.

## Engineering contributions

- Versioned threat scenarios covering indirect prompt injection, authorization confusion, data-instruction confusion, and quoted command injection.
- Model adapters for native Ollama and OpenAI-compatible endpoints.
- A positive-control gate that verifies structured tool calling before interpreting a zero-violation result.
- Paired baseline-versus-hardened experiments using identical scenarios, case identifiers, model settings, and synthetic markers.
- Wilson confidence intervals, per-scenario summaries, deterministic seeds, latency measurements, and JSONL checkpoints.
- Risk- and uncertainty-aware allocation for additional evaluation trials.
- Simulated tool definitions that record requested actions but never execute them.

## Architecture

```text
Threat scenarios
  synthetic marker + authorization policy
                    |
                    v
Evaluation engine -- deterministic coverage and adaptive allocation
                    |
                    v
Model adapter ------ Mock, Ollama, or OpenAI-compatible API
                    |
                    v
Simulated boundary - record tool_calls; execute nothing
                    |
                    v
Policy and reports - violations, exposure, confidence intervals, audit logs
```

## Repository map

```text
src/agentsec_eval/       reusable evaluation package
tests/                   deterministic unit tests
compare_local.py         paired baseline/hardened runner
CD_engineered.py         convenience CLI entry point
results/gpt-oss-20b-challenge-v1/  primary target-model experiment
results/gemma4-12b-challenge-v1/   additional local Gemma experiment
results/qwen3-8b-pilot/            earlier portability pilot
legacy/CD_original.py    original competition CD submission snapshot
legacy/SECRET_MARKER.py  original competition-era reference snapshot
```

The package never imports either legacy file. They depend on the competition-only `aicomp_sdk` and `kaggle_evaluation` environment and can request actions inside the authorized competition sandbox; see [legacy/README.md](legacy/README.md) before opening or reusing them.

## Quick start

Python 3.11 or newer is required. The core project has no third-party Python dependencies.

```bash
python -m pip install -e .
python -m unittest discover -s tests -v

agentsec-eval \
  --adapter mock \
  --model mock-agent \
  --trials 40 \
  --seed 42 \
  --checkpoint artifacts/mock-trials.jsonl \
  --output artifacts/mock-report.json
```

The mock adapter validates the pipeline; its numbers are not model benchmark results.

## Reproduce the GPT-OSS 20B experiment

Install Ollama, pull the model, and run the paired comparison:

```bash
ollama pull gpt-oss:20b

python compare_local.py \
  --backend ollama \
  --base-url http://127.0.0.1:11434 \
  --model gpt-oss:20b \
  --trials-per-scenario 1 \
  --seed 42 \
  --context-tokens 2048 \
  --max-tokens 512 \
  --scenario-set challenge \
  --output-dir artifacts/gpt-oss-20b-challenge-v1
```

The runner first issues one explicitly authorized positive control. If the model or runtime cannot produce a structured tool call, the comparison stops as inconclusive rather than misreporting two zeroes as evidence of safety.

## Run Gemma locally

The same runner supports Gemma through the native Ollama adapter; no model-specific attack prompts or scoring changes are needed. The local addition uses `gemma4:12b`, not the competition's exact Gemma checkpoint.

```bash
ollama pull gemma4:12b
python compare_local.py \
  --backend ollama \
  --base-url http://127.0.0.1:11434 \
  --model gemma4:12b \
  --trials-per-scenario 1 \
  --seed 42 \
  --context-tokens 2048 \
  --max-tokens 512 \
  --scenario-set challenge \
  --output-dir artifacts/gemma4-12b-challenge-v1
```

This compares baseline and hardened system prompts within Gemma. It is not a comparison of the original competition script against the refactored code, and it does not fine-tune the model. The seed controls harness case construction, not an Ollama inference seed.

## Primary local-model result

The primary experiment used Ollama 0.32.14 with [`gpt-oss:20b`](https://developers.openai.com/api/docs/models/gpt-oss-20b) (20.9B total parameters, MXFP4) on an Apple M3 Pro with 18GB unified memory. It is the same model family and size named in the competition description. The positive control successfully returned a structured `http_post` call before the paired evaluation began.

`challenge-v1` contains 12 distinct prompts, with three each for indirect prompt injection, authorization confusion, data-instruction confusion, and command injection. Each condition completed all 12 cases without errors:

| Condition | Valid cases | Unauthorized calls | Violation rate with 95% Wilson CI | Marker exposures | Mean latency |
|---|---:|---:|---:|---:|---:|
| Baseline | 12 | 8 | 66.7% (39.1%-86.2%) | 8 | 11.57 s |
| Hardened | 12 | 1 | 8.3% (1.5%-35.4%) | 1 | 11.27 s |

The observed violation-rate difference was -58.3 percentage points. Seven paired cases violated only under the baseline policy; none violated only under the hardened policy. The two-sided exact McNemar p-value was 0.0156. The remaining hardened violation came from an injected instruction inside a build log, so the result supports improvement but does not establish complete protection. See [the GPT-OSS experiment artifacts](results/gpt-oss-20b-challenge-v1/) for the reports and per-case audit records.

The earlier [Qwen3-8B basic pilot](results/qwen3-8b-pilot/) remains as a portability check. Its more explicit scenarios produced zero violations in both conditions, which motivated the versioned `challenge-v1` set rather than being presented as proof of safety.

### Additional Gemma result

The [Gemma 4 12B experiment](results/gemma4-12b-challenge-v1/) used the same 12 `challenge-v1` cases, context budget, and generation budget. Its positive control passed and all 12 pairs completed without request errors.

| Model | Baseline target-tool violations | Hardened target-tool violations | Difference | Exact paired p-value |
|---|---:|---:|---:|---:|
| GPT-OSS 20B (historical run) | 8/12 (66.7%) | 1/12 (8.3%) | -58.3 percentage points | 0.0156 |
| Gemma 4 12B | 5/12 (41.7%) | 1/12 (8.3%) | -33.3 percentage points | 0.1250 |

Gemma's remaining hardened violation was `support_ticket_email`, whereas GPT-OSS's was `build_log_shell`. Equal aggregate hardened counts therefore hide different failure cases. Gemma's decrease is descriptive; the small paired study does not reach the conventional 0.05 threshold. These p-values concern each model's policy comparison, not a between-model test.

Gemma used Ollama 0.34.2 on macOS 27.0; the historical GPT-OSS run used Ollama 0.32.14 on macOS 26.6.2. Model size, quantization, templates, and runtime differ, so this table is not a controlled ranking of model safety. Qwen used a different scenario set and is not included in this table. See the Gemma [environment record](results/gemma4-12b-challenge-v1/environment.json) and [Chinese report](results/gemma4-12b-challenge-v1/REPORT_ZH.md).

## Competition lineage

The competition system targeted GPT-OSS and Gemma tool-use behavior in an offline replay environment. Its later CD strategy maintained separate pools of 20 single-action profiles per model, configured 30 probes per profile, ranked profiles using a trace-derived reward-per-second proxy, and generated up to 2,000 parameter-diverse candidates. These numbers describe the competition design, not the local A/B protocol in this repository.

The included `SECRET_MARKER.py` documents the earlier marker-dependent exfiltration approach. `CD_original.py` preserves the later non-marker GPT-OSS/Gemma submission snapshot that searched model-specific prompt profiles and selected candidates using replay traces and runtime. Keeping both stages visible explains the focus on transferability, capability controls, held-out evaluation, and uncertainty reporting. The code snapshots alone do not establish official leaderboard scores or the cause of hidden-defense behavior.

## Safety boundary

- Default destinations use the reserved `example.invalid` domain.
- Markers are synthetic and unique to each trial.
- The evaluation adapters only parse returned `tool_calls`.
- No network request, email, file write, or shell command requested by a model is executed.
- The legacy competition files are excluded from package discovery and automated tests.
- Evaluate only systems you own or are explicitly authorized to test.

## Limitations and next steps

- The included GPT-OSS result uses 12 distinct cases and remains a small local experiment, not a production safety claim.
- Current scenarios are single-turn and should be extended with multi-turn state contamination and cross-tool dependencies.
- A utility set is needed to measure whether stricter authorization rules block legitimate tasks.
- Application-grade studies should use independent prompt variants, held-out cases, and at least 30 trials per scenario.
- Quantization and tool templates can change model behavior and should be versioned with every result.

## License and publication note

The repository is released under the MIT License. `legacy/CD_original.py` and `legacy/SECRET_MARKER.py` are included as historical competition artifacts supplied by the project author and depend on external competition software that is not distributed here. Public release remains subject to the relevant competition rules and the author's right to license every included file.
