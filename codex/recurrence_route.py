"""Select an established route before considering an interruption."""

from dataclasses import dataclass
from enum import Enum


class State(Enum):
    READY = "ready"
    RECOVERABLE_INPUT = "recoverable_input"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class Route:
    operation: str
    contract: str
    capability: str
    state: State
    evidence: str | None = None
    missing_input: str | None = None


@dataclass(frozen=True)
class Decision:
    action: str
    options: tuple[Route, ...] = ()


def select_route(contract, candidates, allowed, *, repeat=False, explicit=None):
    if contract is None:
        return Decision("fall_through")
    matching = tuple(route for route in candidates
                     if route.contract == contract and route.capability in allowed
                     and route.state is not State.BLOCKED
                     and (explicit is None or route.operation == explicit))
    if repeat and explicit is None:
        proven = tuple(route for route in matching if route.evidence is not None)
        matching = proven or matching
    ready = tuple(route for route in matching if route.state is State.READY)
    if len(ready) == 1:
        return Decision("resume", ready)
    if len(ready) > 1:
        return Decision("compare_routes", ready)
    recoverable = tuple(route for route in matching
                        if route.state is State.RECOVERABLE_INPUT and route.missing_input)
    if recoverable:
        return Decision("collect_input", recoverable)
    return Decision("unresolved")
