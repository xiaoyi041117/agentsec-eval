# Publishing this repository

## Before making it public

1. Confirm that the competition rules permit public release of solution code.
2. Confirm that you own or have permission to license `legacy/SECRET_MARKER.py`.
3. Replace the generic copyright holder in `LICENSE` if you want your legal name shown.
4. Review the staged file list with `git status`.

The repository intentionally excludes model weights, credentials, private benchmark data, local paths, and failed exploratory runs.

## Publish with GitHub CLI

From the repository directory:

```bash
git commit -m "Initial public release"
gh auth login
gh repo create agentsec-eval --public --source=. --remote=origin --push
```

The `gh repo create` command creates external state. Review the repository name and visibility before running it.

## Publish through the GitHub website

1. Create an empty public repository named `agentsec-eval` without generating a README or license.
2. Copy the repository URL.
3. Run:

```bash
git commit -m "Initial public release"
git remote add origin https://github.com/YOUR_USERNAME/agentsec-eval.git
git push -u origin main
```

## Suggested repository description

> Reproducible, side-effect-free security evaluation for tool-using LLM agents, with a paired GPT-OSS 20B experiment and documented competition-to-engineering evolution.

Suggested topics: `ai-safety`, `llm-agents`, `red-teaming`, `tool-use`, `gpt-oss`, `ollama`, `security-evaluation`.
