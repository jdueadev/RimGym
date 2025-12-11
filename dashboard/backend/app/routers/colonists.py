"""Colonist query endpoints"""

from fastapi import APIRouter, HTTPException, Request, status

router = APIRouter()


@router.get("/runs/{run_id}/colonists", response_model=dict)
async def get_colonists(run_id: str, request: Request) -> dict:
    """Get current colonists for a run"""
    storage = request.app.state.storage_manager

    # Try Redis first
    colonists = await storage.get_colonists(run_id)

    if colonists is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No colonist data found for run {run_id}",
        )

    return {
        "run_id": run_id,
        "timestamp": colonists.get("timestamp", 0),
        "colonists": colonists.get("colonists", []),
    }
