"""
Per-request authenticated-user context for MCP tool calls.

McpAuthMiddleware sets the contextvar before delegating to the MCP ASGI app.
Stateless-mode request tasks are spawned from within the request's ASGI call,
and anyio copies the caller's contextvar context at spawn time, so the value
set by the middleware is visible inside tool handlers.

Fallback if an SDK update ever breaks that propagation: stash the user in
scope["state"] instead and read it in tools via the FastMCP Context object
(ctx.request_context.request.scope).
"""
from contextvars import ContextVar

current_mcp_user: ContextVar[dict | None] = ContextVar("current_mcp_user", default=None)


def get_current_user() -> dict:
    """Return the user authenticated by McpAuthMiddleware for this request."""
    user = current_mcp_user.get()
    if user is None:
        raise RuntimeError("No authenticated user in MCP context")
    return user
