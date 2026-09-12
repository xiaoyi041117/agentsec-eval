from __future__ import annotations

import json
import tempfile
import unittest
from collections import Counter
from pathlib import Path

from agentsec_eval.adapters import MockAgentAdapter, OllamaAdapter
from agentsec_eval.engine import EvaluationConfig, EvaluationEngine, wilson_interval
from agentsec_eval.scenarios import challenge_scenarios, default_scenarios


class EngineTests(unittest.TestCase):
    def test_ollama_context_floor_is_explicit(self) -> None:
        adapter = OllamaAdapter("http://127.0.0.1:11434", "test", context_tokens=128)
        self.assertEqual(adapter.context_tokens, 512)

    def test_challenge_scenarios_are_versioned(self) -> None:
        scenarios = challenge_scenarios()
        self.assertEqual(len(scenarios), 12)
        self.assertTrue(all("challenge-v1" in row.tags for row in scenarios))
        self.assertEqual(Counter(row.category for row in scenarios), {
            "indirect_prompt_injection": 3,
            "authorization_confusion": 3,
            "data_instruction_confusion": 3,
            "command_injection": 3,
        })

    def test_wilson_interval(self) -> None:
        low, high = wilson_interval(5, 10)
        self.assertLess(low, 0.5)
        self.assertGreater(high, 0.5)

    def test_deterministic_report_counts(self) -> None:
        config = EvaluationConfig(seed=7, total_trials=24, min_trials_per_scenario=3)
        first = EvaluationEngine(MockAgentAdapter(seed=7), default_scenarios(), config).run()
        second = EvaluationEngine(MockAgentAdapter(seed=7), default_scenarios(), config).run()
        self.assertEqual(
            [(row.scenario_id, row.trials, row.violations) for row in first.summaries],
            [(row.scenario_id, row.trials, row.violations) for row in second.summaries],
        )
        self.assertEqual(sum(row.trials for row in first.summaries), 24)

    def test_checkpoint_is_jsonl(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            checkpoint = Path(directory) / "run.jsonl"
            config = EvaluationConfig(total_trials=20, min_trials_per_scenario=5)
            EvaluationEngine(
                MockAgentAdapter(), default_scenarios(), config, checkpoint_path=checkpoint
            ).run()
            rows = [json.loads(line) for line in checkpoint.read_text().splitlines()]
            self.assertEqual(len(rows), 20)
            self.assertTrue(all("scenario_id" in row for row in rows))


if __name__ == "__main__":
    unittest.main()
