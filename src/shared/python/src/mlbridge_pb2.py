# Compatibility alias - mlbridge_pb2 was renamed to rimgym_pb2
# This file provides backwards compatibility for imports that reference mlbridge_pb2
# The actual generated protobuf file is rimgym_pb2.py
from . import rimgym_pb2 as _rimgym_pb2

# Dynamically re-export all public symbols from rimgym_pb2 for full compatibility
import sys as _sys

# Get all public (non-underscore-prefixed) attributes from rimgym_pb2
_public_symbols = [name for name in dir(_rimgym_pb2) if not name.startswith('_')]

# Add all public symbols to the current module's globals
for _name in _public_symbols:
    globals()[_name] = getattr(_rimgym_pb2, _name)

# Set __all__ for wildcard imports
__all__ = _public_symbols
