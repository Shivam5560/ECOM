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


exceptions = _alias("exceptions", "domain/exceptions.py")
auth = _alias("auth", "domain/auth.py")
http = _alias("http", "services/http.py")
cache = _alias("cache", "services/cache.py")
realtime = _alias("realtime", "services/realtime.py")
models = _alias("models", "domain/models.py")

from domain.auth import CurrentUser, TokenClaims, TokenVerifier
from domain.exceptions import (
    AppError,
    ForbiddenError,
    NotFoundError,
    ServiceCallError,
    ServiceUnavailableError,
    UnauthorizedError,
    ValidationError,
)
from domain.models import AuditEntity, ErrorEnvelope, GridColumn, GridParams, InMemoryRepository, PagedResponse, ResponseEnvelope
from services.cache import InMemoryCacheBackend, cacheable
from services.realtime import RealtimeConnection, RealtimeHub
from services.http import RequestContext, ServiceClient, ServiceResolver, StaticServiceResolver
