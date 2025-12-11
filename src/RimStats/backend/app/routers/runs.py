"""Run management endpoints"""

from fastapi import APIRouter, HTTPException, Request, status

from app.models import RunInfo

router = APIRouter()


@router.get("/runs", response_model=dict)
async def list_runs(request: Request) -> dict:
    """List all registered training runs"""
    run_manager = request.app.state.run_manager
    runs = await run_manager.list_runs()
    return {"runs": runs, "total": len(runs)}


@router.post("/runs", response_model=dict, status_code=status.HTTP_201_CREATED)
async def register_run(run_info: RunInfo, request: Request) -> dict:
    """Register a new training run"""
    run_manager = request.app.state.run_manager
    run_id = await run_manager.register_run(run_info)
    return {"run_id": run_id, "status": "pending"}


@router.get("/runs/{run_id}", response_model=RunInfo)
async def get_run(run_id: str, request: Request) -> RunInfo:
    """Get details about a specific run"""
    run_manager = request.app.state.run_manager
    run_info = await run_manager.get_run(run_id)
    if run_info is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Run {run_id} not found"
        )
    return run_info


@router.delete("/runs/{run_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unregister_run(run_id: str, request: Request) -> None:
    """Stop tracking a run"""
    run_manager = request.app.state.run_manager
    await run_manager.unregister_run(run_id)
