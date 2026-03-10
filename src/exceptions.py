"""Custom exceptions for Tableau permissions management."""

class InvalidUserException(Exception):
    """Raised when a user does not exist."""

    def __init__(self, message: str = "The user does not exist.") -> None:
        self.message = message
        super().__init__(self.message)


class TooManyGroupsException(Exception):
    """Raised when a user is in too many groups."""

    def __init__(self, message: str = "The user is in too many groups.") -> None:
        self.message = message
        super().__init__(self.message)


class NoDefaultGroupException(Exception):
    """Raised when a user is not in the Default group."""

    def __init__(self, message: str = "The user is not in the Default group.") -> None:
        self.message = message
        super().__init__(self.message)


class IncorrectExecutiveMemberException(Exception):
    """Raised when a user should not be in the Executive group."""

    def __init__(self, message: str = "The user should not be in the Executive group.") -> None:
        self.message = message
        super().__init__(self.message)
