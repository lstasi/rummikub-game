"""Base classes and common types for Rummikub models."""

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4


def generate_uuid() -> UUID:
    """Generate a new UUID4 for entity identifiers."""
    return uuid4()


@dataclass
class HasId:
    """Base class for entities with UUID identifiers."""
    
    id: UUID = field(default_factory=generate_uuid)


def to_dict(obj: Any) -> Any:
    """Convert a dataclass or simple object to a dictionary for JSON serialization.
    
    Handles UUIDs, enums, datetime, and nested dataclasses recursively.
    """
    if hasattr(obj, '__dataclass_fields__'):
        # Handle dataclasses
        result = {}
        for field_name, field_obj in obj.__dataclass_fields__.items():
            value = getattr(obj, field_name)
            result[field_name] = to_dict(value)
        return result
    elif isinstance(obj, list):
        return [to_dict(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: to_dict(v) for k, v in obj.items()}
    elif isinstance(obj, UUID):
        return str(obj)
    elif isinstance(obj, datetime):
        return obj.isoformat()
    elif hasattr(obj, 'value'):
        # Handle enums
        return obj.value
    else:
        return obj


def to_json(obj: Any, indent: int | None = None) -> str:
    """Convert a dataclass to JSON string."""
    return json.dumps(to_dict(obj), indent=indent)