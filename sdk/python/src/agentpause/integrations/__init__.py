"""Framework integrations (dependency-free)."""

from .guard import ActionBlocked, ActionRejected, InterventionRequired, guard

__all__ = ["ActionBlocked", "ActionRejected", "InterventionRequired", "guard"]
