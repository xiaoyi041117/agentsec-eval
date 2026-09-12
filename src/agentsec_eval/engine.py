from __future__ import annotations

import json
import math
import random
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from .adapters import AgentAdapter
from .models import EvaluationReport, Finding, Scenario, ScenarioSummary
from .policy import assess
from .scenarios import SYNTHETIC_MARKER_PREFIX


@dataclass(frozen=True)
class EvaluationConfig:
    seed: int = 42
    total_trials: int = 40
    min_trials_per_scenario: int = 5
    max_trials_per_scenario: int = 50
    max_steps: int = 1
    confidence_z: float = 1.96


def wilson_interval(successes: int, trials: int, z: float = 1.96) -> tuple[float, float]:
    if trials <= 0:
        return 0.0, 1.0
    p = successes / trials
    z2 = z * z
    center = (p + z2 / (2 * trials)) / (1 + z2 / trials)
    radius = z * math.sqrt((p * (1 - p) + z2 / (4 * trials)) / trials) / (1 + z2 / trials)
    return max(0.0, center - radius), min(1.0, center + radius)


class EvaluationEngine:
    """Coverage-first evaluation with risk/uncertainty-guided trial allocation."""

    def __init__(
        self,
        adapter: AgentAdapter,
        scenarios: list[Scenario],
        config: EvaluationConfig | None = None,
        checkpoint_path: Path | None = None,
    ):
        if not scenarios:
            raise ValueError("at least one scenario is required")
        self.adapter = adapter
        self.scenarios = list(scenarios)
        self.config = config or EvaluationConfig()
        self.checkpoint_path = checkpoint_path
        self._rng = random.Random(self.config.seed)

    def _case_id(self, scenario: Scenario, trial_index: int) -> str:
        salt = self._rng.getrandbits(32)
        return f"{scenario.scenario_id[:8]}-{trial_index:04d}-{salt:08x}"

    def _append_checkpoint(self, finding: Finding) -> None:
        if self.checkpoint_path is None:
            return
        self.checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
        with self.checkpoint_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(asdict(finding), ensure_ascii=False) + "\n")

    def _priority(self, scenario: Scenario, findings: list[Finding]) -> float:
        rows = [row for row in findings if row.scenario_id == scenario.scenario_id and row.error is None]
        violations = sum(row.violated for row in rows)
        low, high = wilson_interval(violations, len(rows), self.config.confidence_z)
        uncertainty = high - low
        return high * scenario.severity + uncertainty

    def run(self) -> EvaluationReport:
        started = datetime.now(timezone.utc)
        run_id = uuid.uuid4().hex
        findings: list[Finding] = []
        counts = {scenario.scenario_id: 0 for scenario in self.scenarios}

        minimum_needed = self.config.min_trials_per_scenario * len(self.scenarios)
        if self.config.total_trials < minimum_needed:
            raise ValueError(f"total_trials must be at least {minimum_needed}")

        schedule: list[Scenario] = []
        for _ in range(self.config.min_trials_per_scenario):
            schedule.extend(self.scenarios)

        while len(schedule) < self.config.total_trials:
            eligible = [
                scenario
                for scenario in self.scenarios
                if counts[scenario.scenario_id] + sum(s.scenario_id == scenario.scenario_id for s in schedule)
                < self.config.max_trials_per_scenario
            ]
            if not eligible:
                break
            # The live choice happens after the coverage schedule has been consumed.
            schedule.append(eligible[len(schedule) % len(eligible)])

        for position in range(len(schedule)):
            if position >= minimum_needed:
                eligible = [
                    scenario
                    for scenario in self.scenarios
                    if counts[scenario.scenario_id] < self.config.max_trials_per_scenario
                ]
                if not eligible:
                    break
                scenario = max(eligible, key=lambda item: self._priority(item, findings))
            else:
                scenario = schedule[position]

            trial_index = counts[scenario.scenario_id]
            counts[scenario.scenario_id] += 1
            case_id = self._case_id(scenario, trial_index)
            marker = f"{SYNTHETIC_MARKER_PREFIX}_{case_id}"
            prompt = scenario.render(case_id, marker)
            result = self.adapter.evaluate(scenario, prompt, case_id, self.config.max_steps)
            finding = assess(scenario, result, marker)
            findings.append(finding)
            self._append_checkpoint(finding)

        summaries = []
        for scenario in self.scenarios:
            rows = [row for row in findings if row.scenario_id == scenario.scenario_id]
            valid = [row for row in rows if row.error is None]
            violations = sum(row.violated for row in valid)
            low, high = wilson_interval(violations, len(valid), self.config.confidence_z)
            summaries.append(
                ScenarioSummary(
                    scenario_id=scenario.scenario_id,
                    category=scenario.category,
                    trials=len(valid),
                    violations=violations,
                    violation_rate=violations / len(valid) if valid else 0.0,
                    ci_low=low,
                    ci_high=high,
                    marker_exposures=sum(row.marker_exposed for row in valid),
                    mean_latency_s=(sum(row.latency_s for row in valid) / len(valid)) if valid else 0.0,
                    severity=scenario.severity,
                )
            )

        return EvaluationReport(
            schema_version="1.0",
            run_id=run_id,
            model=self.adapter.model_name,
            seed=self.config.seed,
            started_at=started.isoformat(),
            completed_at=datetime.now(timezone.utc).isoformat(),
            config=asdict(self.config),
            summaries=summaries,
            findings=findings,
        )
