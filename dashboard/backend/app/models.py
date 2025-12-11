"""Pydantic models for API"""

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class RunStatus(str, Enum):
    """Run status enum"""

    PENDING = "pending"
    ACTIVE = "active"
    STALE = "stale"
    COMPLETED = "completed"
    FAILED = "failed"


class RunInfo(BaseModel):
    """Information about a training run"""

    run_id: str = Field(..., description="Unique run identifier")
    name: str = Field(..., description="Human-readable run name")
    algorithm: str = Field(..., description="RL algorithm (PPO, A2C, DQN)")
    scenario: str = Field(..., description="Game scenario")
    status: RunStatus = Field(..., description="Current run status")
    host: str = Field(..., description="RimWorld host address")
    port: int = Field(..., description="RimWorld TCP port")
    started_at: int = Field(..., description="Unix timestamp of start")
    ended_at: Optional[int] = Field(None, description="Unix timestamp of end")
    colonists: int = Field(0, description="Current colonist count")
    current_reward: float = Field(0.0, description="Most recent reward")
    config: Dict[str, Any] = Field(default_factory=dict, description="Configuration")


class ColonistState(BaseModel):
    """Current state of a colonist"""

    pawn_id: int = Field(..., description="Unique pawn identifier")
    name: str = Field(..., description="Colonist name")
    age: int = Field(..., description="Age in years")
    gender: str = Field(..., description="Male/Female")
    health: float = Field(..., ge=0.0, le=1.0, description="Health percentage")
    mood: float = Field(..., ge=0.0, le=1.0, description="Mood level")
    needs: Dict[str, float] = Field(default_factory=dict, description="Need levels")
    skills: Dict[str, int] = Field(default_factory=dict, description="Skill levels")
    job: str = Field("Idle", description="Current job/activity")
    position: Dict[str, float] = Field(
        default_factory=dict, description="Position (x, y, z)"
    )


class MapState(BaseModel):
    """Current map state"""

    run_id: str
    map_size: Dict[str, int] = Field(default_factory=dict, description="Map dimensions")
    buildings: int = Field(0, description="Building count")
    zones: List[Dict[str, Any]] = Field(
        default_factory=list, description="Zone definitions"
    )
    temperature: float = Field(20.0, description="Average temperature (C)")
    weather: str = Field("Clear", description="Current weather")


class IncidentSeverity(str, Enum):
    """Incident severity levels"""

    MINOR = "minor"
    MAJOR = "major"
    CRITICAL = "critical"


class IncidentEvent(BaseModel):
    """Game incident/event"""

    incident_id: int = Field(..., description="Unique incident identifier")
    run_id: str = Field(..., description="Associated run ID")
    timestamp: int = Field(..., description="Unix timestamp")
    incident_type: str = Field(..., description="Type (raid, fire, death, etc.)")
    severity: IncidentSeverity = Field(..., description="Severity level")
    details: Dict[str, Any] = Field(
        default_factory=dict, description="Additional details"
    )


class TrainingMetrics(BaseModel):
    """Training metrics data point"""

    timestamp: int = Field(..., description="Unix timestamp")
    value: float = Field(..., description="Metric value")


class MetricsResponse(BaseModel):
    """Response for metrics query"""

    run_id: str
    metric: str
    window_start: int
    window_end: int
    data_points: List[TrainingMetrics]
    statistics: Dict[str, float] = Field(
        default_factory=dict, description="Min, max, mean, stddev"
    )


class EpisodeInfo(BaseModel):
    """Episode history entry"""

    episode_num: int = Field(..., description="Episode number")
    total_reward: float = Field(..., description="Total episode reward")
    length: int = Field(..., description="Episode length in steps")
    started_at: int = Field(..., description="Start timestamp")
    ended_at: int = Field(..., description="End timestamp")
    final_colonists: int = Field(..., description="Colonist count at end")
    final_wealth: float = Field(..., description="Colony wealth at end")


class GameState(BaseModel):
    """Complete game state snapshot"""

    run_id: str
    timestamp: int
    frame_id: int = Field(..., description="Game tick number")
    colonists: List[ColonistState] = Field(default_factory=list)
    resources: Dict[str, int] = Field(default_factory=dict)
    threats: List[Dict[str, Any]] = Field(default_factory=list)
    metrics: Dict[str, float] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    """Standard error response"""

    error: Dict[str, Any] = Field(
        ..., description="Error details (code, message, details, timestamp)"
    )
