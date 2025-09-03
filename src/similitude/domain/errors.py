# TODO: These are currently not used.


class SimilitudeError(Exception):
    """Base exception for domain-specific errors."""


class PersistenceError(SimilitudeError):
    """Database or storage layer problems."""


class FilesystemError(SimilitudeError):
    """Unreadable paths, permission issues, long paths, etc."""


class HashingError(SimilitudeError):
    """Problems while computing hashes (pre, strong, similarity)."""


class ConfigurationError(SimilitudeError):
    """Bad CLI args or unusable config (e.g., DB not writable)."""
