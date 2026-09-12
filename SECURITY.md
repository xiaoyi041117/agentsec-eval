# Security policy

AgentSec Eval is intended only for defensive testing of systems you own or are explicitly authorized to evaluate.

## Default framework

The adapters under `src/agentsec_eval/` expose simulated tool definitions and record model-requested actions. They do not execute network requests, send email, write files, or run shell commands. Test scenarios use synthetic markers and reserved `example.invalid` destinations.

Do not connect the framework directly to production tools with side effects. If you extend an adapter, keep execution disabled by default and require an explicit, auditable sandbox and authorization boundary.

## Legacy artifact

`legacy/SECRET_MARKER.py` is preserved for historical review and is excluded from the package and CI. Unlike the modern framework, it was designed to interact with a live competition sandbox through the external `aicomp_sdk`. Do not run it outside an authorized competition or research environment.

## Reporting issues

Do not open a public issue containing credentials, private model traces, unpublished benchmark assets, or exploitable production details. Report those matters privately to the relevant system owner or repository maintainer.
