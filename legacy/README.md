# Legacy competition artifact

`SECRET_MARKER.py` is a source-equivalent snapshot of an earlier submission strategy for the AI Agent Security - Multi-Step Tool Attacks competition. Line endings and trailing whitespace were normalized for the public repository; executable statements were not changed.

It is preserved because it documents an important negative result in the project history: the marker-dependent exfiltration path achieved a public score above 95 but received zero under hidden-defense replay. That failure motivated the later move toward a marker-independent confused-deputy path and, eventually, the side-effect-free evaluation framework in this repository.

## Important boundary

This file is not part of the installable `agentsec_eval` package, is not imported by the command-line tools, and is not run by CI. It depends on the external competition-only `aicomp_sdk`. Inside the original authorized sandbox, it can ask the environment to perform an `http.post` action.

Do not run or adapt it against systems you do not own or lack explicit permission to test. The modern framework under `src/agentsec_eval/` is the default public implementation and records simulated tool calls without executing them.

## Why include it

- It makes the project iteration auditable instead of presenting only the final design.
- It demonstrates the difference between public leaderboard performance and hidden-defense transferability.
- It provides context for the capability gate, safety boundary, and uncertainty-aware reporting in the engineering refactor.
- It lets reviewers compare a competition-specific optimizer with a portable evaluation system.

The external SDK and competition environment are not included, so this snapshot is not independently executable from this repository.
