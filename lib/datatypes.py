# Data type definitions
from dataclasses import dataclass


@dataclass
class MathIdentifier:
    """A type of Math identifier"""
    hexcode: str
    var: str


@dataclass
class MathConcept:
    """A single Math Concept"""
    description: str
    arity: int
    args_type: list[str]
