"""AgentPause simulator: deterministic agent scenarios, a simulated user, and experiments.

Every action in every scenario is SIMULATED. Nothing here sends email, spends money,
deletes files, or changes calendars.
"""

from .ablation import ABLATABLE, SignalAblation
from .engine import EngineConfig, EngineError, EpisodeEngine, EpisodeState, ErrorEvent, StepResult
from .experiment import (
    ConditionSpec,
    ExperimentConfig,
    ExperimentResult,
    PolicySpec,
    build_policy,
    run_episode,
    run_experiment,
)
from .export import RECORD_COLUMNS, rows_to_csv, write_result
from .metrics import METRICS, EpisodeSummary, aggregate, metric_catalog, paired_comparison, summarize
from .scenario import Scenario, ScenarioError, list_scenarios, load_scenario, load_scenario_file, parse_scenario
from .user import CardTruth, HumanResponse, SimulatedUser, SimulatedUserParams

__version__ = "0.1.0"

__all__ = [
    "ABLATABLE",
    "METRICS",
    "RECORD_COLUMNS",
    "CardTruth",
    "ConditionSpec",
    "EngineConfig",
    "EngineError",
    "EpisodeEngine",
    "EpisodeState",
    "EpisodeSummary",
    "ErrorEvent",
    "ExperimentConfig",
    "ExperimentResult",
    "HumanResponse",
    "PolicySpec",
    "Scenario",
    "ScenarioError",
    "SignalAblation",
    "SimulatedUser",
    "SimulatedUserParams",
    "StepResult",
    "aggregate",
    "build_policy",
    "list_scenarios",
    "load_scenario",
    "load_scenario_file",
    "metric_catalog",
    "paired_comparison",
    "parse_scenario",
    "rows_to_csv",
    "run_episode",
    "run_experiment",
    "summarize",
    "write_result",
]
