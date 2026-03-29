from fastapi import APIRouter

from app.core.mvp_registry import AGENT_REGISTRY, MCP_REGISTRY

router = APIRouter(prefix="/api/mvp", tags=["system"])


@router.get("/system/registry")
def get_system_registry():
    return {"agents": AGENT_REGISTRY, "mcp_servers": MCP_REGISTRY}
