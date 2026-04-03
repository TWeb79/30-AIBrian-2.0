# Motor routes - /api/motor, /api/reflex/check
import asyncio
from fastapi import APIRouter, HTTPException
from api.config import brain
from api.models import MotorCommand, ReflexCheckRequest

router = APIRouter()

@router.post("/reflex/check")
def reflex_check(req: ReflexCheckRequest):
    """Check if motor command passes safety constraints."""
    FORCE_MAX = 10
    ANGLE_MAX = 170
    VEL_MAX = 2
    
    violations = []
    if req.force > FORCE_MAX:
        violations.append(f"force={req.force}N > {FORCE_MAX}N")
    if req.angle > ANGLE_MAX:
        violations.append(f"angle={req.angle}° > {ANGLE_MAX}°")
    if req.velocity > VEL_MAX:
        violations.append(f"velocity={req.velocity}m/s > {VEL_MAX}m/s")
    
    approved = len(violations) == 0
    
    return {
        "approved": approved,
        "reason": "SAFE — command executed" if approved else f"REFLEX_WITHDRAWAL: {'; '.join(violations)}",
        "constraints": {
            "force_max": FORCE_MAX,
            "angle_max": ANGLE_MAX,
            "velocity_max": VEL_MAX
        }
    }


@router.post("/motor")
async def motor(cmd: MotorCommand):
    """Issue motor command."""
    try:
        cmd_data = cmd.model_dump()
    except Exception:
        cmd_data = cmd.dict()
    # Run in thread to avoid blocking
    result = await asyncio.to_thread(brain.issue_motor_command, cmd_data)
    return result