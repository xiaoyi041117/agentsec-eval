# From competition optimization to reproducible evaluation

This note separates the project's three stages so that competition metrics, implementation choices, and post-competition experiments are not conflated.

## Stage 1  Marker-dependent exfiltration

The early `SECRET_MARKER` strategy optimized a high-severity, single-hop `http.post` path. It used live validation, replay-aware time budgeting, candidate filling, and model-latency heuristics inside the authorized competition sandbox.

The approach exceeded 95 on the public leaderboard but scored zero under hidden-defense replay. This was the project's most useful negative result: a strong public score did not establish transferability.

The original snapshot is preserved at [`legacy/SECRET_MARKER.py`](../legacy/SECRET_MARKER.py). It is not part of the modern package and should not be executed outside an authorized environment.

## Stage 2  Marker-independent confused-deputy search

The competition solution then changed attack paths instead of obfuscating the protected marker. Its CD design targeted a single email-tool action and introduced:

- separate pools of 20 single-action profiles for GPT-OSS and Gemma;
- 30 configured probes per profile and 600 interactions per model;
- tool-trace feedback and a reward-per-second proxy for profile selection;
- tail-window consistency checks and latency-aware tie breaking;
- deterministic recipient variation and up to 2,000 candidates per model;
- assertions that generated messages did not contain `SECRET_MARKER`.

These mechanisms were designed around the competition SDK and scoring system. They demonstrate adaptive search and trace-based optimization, but they do not by themselves constitute a deployable safety product.

## Stage 3  Side-effect-free engineering refactor

The current repository reframes the problem as defensive measurement. It replaces live sandbox actions with simulated tool schemas, records only the model's requested calls, and adds portable adapters, typed data models, deterministic trials, audit checkpoints, confidence intervals, and paired policy comparisons.

This stage also adds a capability control: before interpreting a model's zero-violation result, the harness verifies that the model and runtime can emit structured tool calls. This guards against a common false conclusion in agent evaluations.

## Evidence included in this repository

The primary GPT-OSS 20B experiment is a real local inference study, not an official competition score. It used 12 distinct challenge prompts in each paired condition. Unauthorized tool requests fell from 8/12 under the baseline policy to 1/12 under the hardened authorization boundary, a difference of -58.3 percentage points. Seven discordant pairs favored the hardened condition and none favored baseline, producing a two-sided exact McNemar p-value of 0.0156.

This result demonstrates an effect on the included cases, not complete protection or a change to model weights. One build-log injection still triggered `shell_run` under the hardened policy. The earlier Qwen3-8B basic pilot is retained separately as a portability result and as evidence for why scenario difficulty must be versioned.

## What the project demonstrates

- Iteration based on hidden-distribution failure rather than public-score optimization alone.
- Model-specific strategy search informed by execution traces and runtime constraints.
- A transition from benchmark-specific attack generation to a reusable evaluation architecture.
- Experimental controls that distinguish model capability from observed safety behavior.
- Responsible reporting of negative results and statistical uncertainty.
