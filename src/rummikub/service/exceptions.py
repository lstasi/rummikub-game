"""Service-specific exceptions for the game service layer."""


class ServiceError(Exception):
    """Base service layer exception."""
    pass


class GameNotFoundError(ServiceError):
    """Game ID not found in Redis."""
    pass


class ConcurrentModificationError(ServiceError):
    """Game was modified by another player while operation was in progress."""
    pass