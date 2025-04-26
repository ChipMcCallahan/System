from dataclasses import dataclass, field
from typing import Optional, Dict, Any


@dataclass
class SystemNode:
    ID: Optional[int] = None
    ParentID: Optional[int] = None
    Name: str = ""
    Description: Optional[str] = None
    Notes: Optional[str] = None
    Tags: Optional[Dict[str, Any]] = field(default_factory=dict)
    Metadata: Optional[Dict[str, Any]] = field(default_factory=dict)
    Status: Optional[str] = None
    Importance: int = 0
