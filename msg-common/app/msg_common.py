from __future__ import annotations

import importlib
import importlib.util
import sys
from pathlib import Path

__path__: list[str] = []
_APP_ROOT = Path(__file__).parent


def _alias(public_name: str, relative_path: str):
    module_name = f"{__name__}.{public_name}"
    spec = importlib.util.spec_from_file_location(module_name, _APP_ROOT / relative_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {module_name}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    sys.modules[f"{__name__}.{public_name}"] = module
    return module


envelope = _alias("envelope", "domain/envelope.py")
bus = _alias("bus", "services/bus.py")

from domain.envelope import EventEnvelope
from services.bus import EventBus, EventHandler, InMemoryEventBus
