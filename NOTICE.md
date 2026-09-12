# Publication notice

This repository contains two distinct bodies of work:

1. `legacy/SECRET_MARKER.py` is a historical competition artifact that depends on the external `aicomp_sdk` and may request tool actions inside the competition sandbox.
2. `src/agentsec_eval/` is a post-competition engineering refactor. Its adapters expose simulated tools and never execute model-requested side effects.

The reported GPT-OSS 20B and Qwen3-8B runs are new local-model experiments performed with the engineering framework. They are not official competition results, reproductions of the original leaderboard score, or evidence that either model is safe in every deployment.

Public release remains subject to the original competition rules and to the author's rights in the submitted solution code. The external competition SDK, model weights, private traces, credentials, and protected benchmark data are not distributed in this repository.
