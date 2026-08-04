from __future__ import annotations

from dataclasses import dataclass


class ForbiddenError(Exception):
    pass


@dataclass(frozen=True)
class Principal:
    subject: str
    tenant_id: str
    permissions: frozenset[str]


@dataclass(frozen=True)
class ToolCall:
    name: str
    tenant_id: str
    confirmed: bool = False
    idempotency_key: str | None = None


TOOL_POLICY = {
    "ticket.read": ("ticket:read", False),
    "ticket.close": ("ticket:write", True),
}


def authorize_resource(principal: Principal, tenant_id: str, permission: str) -> None:
    if tenant_id != principal.tenant_id or permission not in principal.permissions:
        raise ForbiddenError("resource is not allowed")


def authorize_tool_call(principal: Principal, call: ToolCall) -> None:
    """Authorize deterministic policy before an Agent executes a tool."""
    policy = TOOL_POLICY.get(call.name)
    if policy is None:
        raise ForbiddenError("tool is not allowlisted")
    permission, has_side_effect = policy
    authorize_resource(principal, call.tenant_id, permission)
    if has_side_effect and (not call.confirmed or not call.idempotency_key):
        raise ForbiddenError("side effect requires confirmation and idempotency key")
