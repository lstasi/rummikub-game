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


# Engine-specific exceptions

class GameNotFoundError(GameStateError):
    """Raised when attempting to access a non-existent game."""
    pass


class GameFullError(GameStateError):
    """Raised when attempting to add a player to a full game."""
    pass


class GameNotStartedError(GameStateError):
    """Raised when attempting gameplay actions before game starts."""
    pass


class GameFinishedError(GameStateError):
    """Raised when attempting actions on a completed game."""
    pass


class NotPlayersTurnError(GameStateError):
    """Raised when a player attempts an action out of turn."""
    pass


class PlayerNotInGameError(GameStateError):
    """Raised when an unknown player attempts an action."""
    pass


class InitialMeldNotMetError(ValidationError):
    """Raised when a player's first play doesn't meet the 30-point requirement."""
    pass


class InvalidMoveError(ValidationError):
    """Raised when a move is invalid for a specific reason."""
    
    def __init__(self, message: str, reason: str | None = None):
        super().__init__(message)
        self.reason = reason


class TileNotOwnedError(ValidationError):
    """Raised when a player attempts to use tiles they don't own."""
    pass


class PoolEmptyError(ValidationError):
    """Raised when attempting to draw from an empty pool."""
    pass


class InvalidBoardStateError(ValidationError):
    """Raised when the resulting board state has invalid combinations."""
    pass


class JokerRetrievalError(JokerAssignmentError):
    """Raised when joker retrieval attempt is invalid."""
    pass


class JokerNotReusedError(JokerAssignmentError):
    """Raised when a retrieved joker is not reused in the same turn."""
    pass