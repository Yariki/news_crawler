from fastapi import APIRouter as Router


route = Router(
    prefix="/health",
    tags=["health"],
)

@route.get("/", summary="Health Check", response_description="Health status")
async def health_check():
    """Endpoint to check the health of the application."""
    return {"status": "ok"}