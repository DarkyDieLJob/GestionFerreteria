# Compatibility shim so external imports can use `proveedores.models`
# while our concrete models live under `proveedores.adapters.models`.
from .adapters.models import *  # noqa: F401,F403
