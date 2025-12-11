# Compatibility alias - mlbridge_pb2 was renamed to rimgym_pb2
# This file provides backwards compatibility for imports that reference mlbridge_pb2
# The actual generated protobuf file is rimgym_pb2.py
from . import rimgym_pb2 as _rimgym_pb2

# Re-export all public symbols from rimgym_pb2
CommandMessage = _rimgym_pb2.CommandMessage
CommandType = _rimgym_pb2.CommandType
StateMessage = _rimgym_pb2.StateMessage
RichStateMessage = _rimgym_pb2.RichStateMessage
EmptyMessage = _rimgym_pb2.EmptyMessage
TickMessage = _rimgym_pb2.TickMessage
AckMessage = _rimgym_pb2.AckMessage
Action = _rimgym_pb2.Action
Entity = _rimgym_pb2.Entity

# Expose the module for cases where the full module is accessed
DESCRIPTOR = _rimgym_pb2.DESCRIPTOR
