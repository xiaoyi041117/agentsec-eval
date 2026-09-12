# Qwen3-8B local pilot

This directory contains a real local inference run of the paired safety harness.

## Configuration

- Runtime: Ollama 0.32.14
- Model: `qwen3:8b`
- Local model metadata: 8.2B parameters, Q4_K_M
- Seed: 42
- Threat scenarios: 4
- Trials per scenario and condition: 3
- Attempted pairs: 12
- Valid complete pairs: 12
- Capability control: passed with a structured `http_post` request

The two conditions used the same case identifiers, prompts, model settings, and simulated tools. Only the system-level authorization policy changed.

## Result

| Condition | Trials | Violations | Violation rate | Marker exposures | Mean latency |
|---|---:|---:|---:|---:|---:|
| Baseline | 12 | 0 | 0.0% | 0 | 5.43 s |
| Hardened | 12 | 0 | 0.0% | 0 | 4.88 s |

The pilot detected no difference. With zero events in 12 observations, the approximate 95% Wilson upper bound is 24.2%; therefore, these data do not establish zero risk. The sequential local run also does not support interpreting the latency difference as a performance gain.

## Files

- `capability-check.json`: structured-tool-call positive control.
- `comparison.json`: paired aggregate statistics.
- `baseline-report.json` and `hardened-report.json`: complete evaluation reports.
- `baseline-trials.jsonl` and `hardened-trials.jsonl`: per-case audit records.
- `REPORT_ZH.md`: Chinese interpretation and reproduction notes.

The tools were schemas only. No model-requested network, email, file-system, or shell action was executed.
