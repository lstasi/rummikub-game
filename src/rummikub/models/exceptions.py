"""Domain-specific exceptions for the Rummikub game models."""

class RummikubError(Exception):
    """Base exception for all Rummikub domain errors."""
    pass


class ValidationError(RummikubError):
    """Base exception for validation errors."""
    pass


class InvalidColorError(ValidationError):
    """Raised when an invalid color is provided."""
    pass


class InvalidNumberError(ValidationError):
    """Raised when an invalid tile number is provided."""
    pass


class InvalidMeldError(ValidationError):
    """Raised when a meld is invalid.
    
    Attributes:
        reason: Specific reason for the invalid meld (size, color-duplication, 
               non-consecutive, mixed-colors, etc.)
    """
    
    def __init__(self, message: str, reason: str | None = None):
        super().__init__(message)
        self.reason = reason


class JokerAssignmentError(ValidationError):
    """Raised when joker assignment is ambiguous or impossible."""
    pass


class GameStateError(RummikubError):
    """Raised when game state is invalid or inconsistent."""
    pass