"""
Provider initializer registry.

Replaces a hand-maintained if/elif chain with a plain dict populated by a
`@register_provider("name")` decorator. `agents/llm.py` still owns the
concrete `_init_*` functions (moving each one into its own file is a larger,
lower-priority refactor — see the parity notes) but no longer needs an
if/elif branch per provider to dispatch to them: registering a new provider
is one decorator, not an edit to a growing conditional.
"""
from typing import Callable, Dict, List

_INITIALIZERS: Dict[str, Callable] = {}


def register_provider(name: str) -> Callable[[Callable], Callable]:
    """Decorator: register `fn` as the initializer for provider `name`."""
    key = name.lower().strip()

    def decorator(fn: Callable) -> Callable:
        _INITIALIZERS[key] = fn
        return fn

    return decorator


def get_initializer(name: str) -> Callable:
    """Look up the initializer function for `name`. Raises KeyError if unregistered."""
    key = name.lower().strip()
    if key not in _INITIALIZERS:
        raise KeyError(f"No initializer registered for provider '{name}'. Registered: {sorted(_INITIALIZERS)}")
    return _INITIALIZERS[key]


def registered_providers() -> List[str]:
    """Every provider name with a registered initializer, sorted."""
    return sorted(_INITIALIZERS)
