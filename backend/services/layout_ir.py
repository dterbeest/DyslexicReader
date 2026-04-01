"""
Intermediate representation for structured document layout.

TextBlock captures a single semantic unit (heading, paragraph, list item).
DocumentLayout holds the ordered sequence of blocks for a document.
"""
from dataclasses import dataclass, field
from enum import Enum


class BlockKind(Enum):
    HEADING = "heading"
    BODY = "body"
    LIST_ITEM = "list_item"
    WHITESPACE = "whitespace"  # explicit vertical gap between sections


@dataclass
class TextBlock:
    kind: BlockKind
    text: str
    indent_level: int = 0        # 0 = body margin; 1+ = list nesting
    heading_level: int = 1       # 1=H1, 2=H2; only meaningful for HEADING blocks
    extra_space_before: bool = False


@dataclass
class DocumentLayout:
    blocks: list[TextBlock] = field(default_factory=list)
