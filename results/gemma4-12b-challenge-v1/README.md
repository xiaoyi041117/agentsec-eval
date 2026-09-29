# Paired local safety comparison

Model: `gemma4:12b`

Runtime settings: temperature `0`, context window `2048`, maximum generated tokens `512`, simulated tools only.

Scenario set: `challenge`.

The two conditions use the same scenarios, case identifiers, trial count, temperature, and simulated tools. The only intended difference is the system-level authorization boundary. Tool requests are recorded but never executed.

Attempted pairs: **12**. Valid complete pairs: **12**. Only pairs with successful responses in both conditions are included below.

| Condition | Trials | Violations | Violation rate (95% Wilson CI) | Marker exposures | Mean latency |
|---|---:|---:|---:|---:|---:|
| Baseline | 12 | 5 | 41.7% (19.3%-68.0%) | 5 | 10.24s |
| Hardened | 12 | 1 | 8.3% (1.5%-35.4%) | 1 | 8.06s |

Violation-rate delta (hardened minus baseline): **-33.3 percentage points**, equivalent to an observed relative reduction of **80%**.

Discordant pairs: baseline-only violations **4**; hardened-only violations **0**. Two-sided exact McNemar p-value: **0.1250**.

This result measures the effect of an inference-time authorization wrapper. It does not show that model weights were retrained or that the original Kaggle submission score changed.

Both conditions were run by `compare_local.py` using the same engineering framework and Gemma checkpoint. The baseline did not execute `legacy/CD_original.py`; this is not an original-CD-versus-refactored-CD experiment.
