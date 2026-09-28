# Legacy competition artifacts

This directory preserves two source-equivalent snapshots from the AI Agent Security - Multi-Step Tool Attacks competition:

- `SECRET_MARKER.py` contains the earlier marker-dependent exfiltration strategy.
- `CD_original.py` contains the later non-marker GPT-OSS/Gemma CD submission, including its embedded attack modules, model-specific profile search, replay-trace selection, and Kaggle inference-server entry point.

Line endings and trailing whitespace may be normalized for the public repository; executable statements were not intentionally changed.

It is preserved because it documents an important negative result in the project history: the marker-dependent exfiltration path achieved a public score above 95 but received zero under hidden-defense replay. That failure motivated the later move toward a marker-independent confused-deputy path and, eventually, the side-effect-free evaluation framework in this repository.

## Important boundary

These files are not part of the installable `agentsec_eval` package, are not imported by the command-line tools, and are not run by CI. They depend on the external competition-only `aicomp_sdk`; `CD_original.py` also starts the competition's `kaggle_evaluation` inference server when run in its intended notebook environment. Inside the original authorized sandbox, they can ask the environment to perform tool actions.

Do not run or adapt it against systems you do not own or lack explicit permission to test. The modern framework under `src/agentsec_eval/` is the default public implementation and records simulated tool calls without executing them.

## Why include it

- It makes the project iteration auditable instead of presenting only the final design.
- It demonstrates the difference between public leaderboard performance and hidden-defense transferability.
- It provides context for the capability gate, safety boundary, and uncertainty-aware reporting in the engineering refactor.
- It lets reviewers compare a competition-specific optimizer with a portable evaluation system.

The external SDK, evaluator, model weights, fixtures, and competition data are not included, so these snapshots are not independently executable from this repository.
