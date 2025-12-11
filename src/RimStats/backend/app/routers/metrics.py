"""Metrics query endpoints"""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Request, status

from app.models import MetricsResponse

router = APIRouter()


@router.get("/runs/{run_id}/metrics", response_model=MetricsResponse)
async def get_metrics(
    run_id: str,
    metric: str = Query(..., description="Metric name (reward, sps, loss_actor, etc.)"),
    window: Optional[str] = Query("1h", description="Time window (1h, 6h, 24h)"),
    request: Request = None,
) -> MetricsResponse:
    """Get time-series metrics for a run"""
    storage = request.app.state.storage_manager

    # Parse window to seconds
    window_seconds = _parse_window(window)

    metrics_data = await storage.get_metrics(run_id, metric, window_seconds)

    if metrics_data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No metrics data found for run {run_id}, metric {metric}",
        )

    return metrics_data


@router.get("/runs/{run_id}/episodes", response_model=dict)
async def get_episodes(
    run_id: str, limit: int = Query(10, ge=1, le=100), request: Request = None
) -> dict:
    """Get episode history for a run"""
    storage = request.app.state.storage_manager
    episodes = await storage.get_episodes(run_id, limit)
    return {"run_id": run_id, "episodes": episodes}


def _parse_window(window: str) -> int:
    """Parse window string to seconds"""
    units = {"s": 1, "m": 60, "h": 3600, "d": 86400}
    try:
        value = int(window[:-1])
        unit = window[-1]
        return value * units[unit]
    except (ValueError, KeyError, IndexError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid window format: {window}",
        )
