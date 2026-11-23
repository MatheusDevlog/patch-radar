class PatchRadarError(Exception):
    pass


class ExternalServiceError(PatchRadarError):
    pass


class GitHubRateLimitError(ExternalServiceError):
    pass


class RepositoryNotFoundError(PatchRadarError):
    pass


class LLMResponseError(PatchRadarError):
    pass
