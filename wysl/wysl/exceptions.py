"""Exception classes."""


class UserTerminationException(Exception):
    """Exception to be raised when a user requests to end the game."""


class CameraError(Exception):
    """Exception to be raised when there is a problem with the camera feed."""
