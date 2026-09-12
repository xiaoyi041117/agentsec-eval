from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class Scenario:
    """A synthetic test case. No tool is ever executed by this package."""

    scenario_id: str
    category: str
    prompt_template: str
    target_tool: str
    severity: int
    description: str
    authorized: bool = False
    tags: tuple[str, ...] = ()

    def render(self, case_id: str, marker: str) -> str:
        return self.prompt_template.format(case_id=case_id, marker=marker)


@dataclass(frozen=True)
class ToolCall:
    name: str
    arguments: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class TrialResult:
    scenario_id: str
    case_id: str
    model: str
    latency_s: float
    tool_calls: tuple[ToolCall, ...] = ()
    response_text: str = ""
    error: str | None = None


@dataclass(frozen=True)
class Finding:
    scenario_id: str
    case_id: str
    category: str
    severity: int
    violated: bool
    marker_exposed: bool
    requested_tools: tuple[str, ...]
    latency_s: float
    error: str | None = None


@dataclass(frozen=True)
class ScenarioSummary:
    scenario_id: str
    category: str
    trials: int
    violations: int
    violation_rate: float
    ci_low: float
    ci_high: float
    marker_exposures: int
    mean_latency_s: float
    severity: int


@dataclass
class EvaluationReport:
    schema_version: str
    run_id: str
    model: str
    seed: int
    started_at: str
    completed_at: str
    config: dict[str, Any]
    summaries: list[ScenarioSummary]
    findings: list[Finding]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
