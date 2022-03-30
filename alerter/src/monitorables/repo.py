from typing import Optional, Dict


class GitHubRepo:
    def __init__(self, repo_name: str, repo_id: str, parent_id: str) -> None:
        self._repo_name = repo_name
        self._repo_id = repo_id
        self._parent_id = parent_id

        # Metrics
        self._no_of_releases = None
        self._last_monitored = None

    def __str__(self) -> str:
        return self.repo_name

    @property
    def repo_name(self) -> str:
        return self._repo_name

    @property
    def repo_id(self) -> str:
        return self._repo_id

    @property
    def parent_id(self) -> str:
        return self._parent_id

    @property
    def no_of_releases(self) -> Optional[int]:
        return self._no_of_releases

    @property
    def last_monitored(self) -> Optional[float]:
        return self._last_monitored

    def set_repo_name(self, repo_name: str) -> None:
        self._repo_name = repo_name

    def set_parent_id(self, parent_id: str) -> None:
        self._parent_id = parent_id

    def set_no_of_releases(self, no_of_releases: Optional[int]) -> None:
        self._no_of_releases = no_of_releases

    def set_last_monitored(self, last_monitored: Optional[float]) -> None:
        self._last_monitored = last_monitored

    def reset(self) -> None:
        self.set_no_of_releases(None)
        self.set_last_monitored(None)


class DockerHubRepo:
    def __init__(self, repo_namespace: str, repo_name: str, repo_id: str,
                 parent_id: str) -> None:
        self._repo_namespace = repo_namespace
        self._repo_name = repo_name
        self._repo_id = repo_id
        self._parent_id = parent_id

        # Metrics
        self._tags = None
        self._last_monitored = None

    def __str__(self) -> str:
        return self._repo_namespace + '/' + self._repo_name

    @property
    def repo_namespace(self) -> str:
        return self._repo_namespace

    @property
    def repo_name(self) -> str:
        return self._repo_name

    @property
    def repo_id(self) -> str:
        return self._repo_id

    @property
    def parent_id(self) -> str:
        return self._parent_id

    @property
    def tags(self) -> Optional[Dict]:
        return self._tags

    @property
    def last_monitored(self) -> Optional[float]:
        return self._last_monitored

    def set_repo_namespace(self, repo_namespace: str) -> None:
        self._repo_namespace = repo_namespace

    def set_repo_name(self, repo_name: str) -> None:
        self._repo_name = repo_name

    def set_parent_id(self, parent_id: str) -> None:
        self._parent_id = parent_id

    def set_tags(self, tags: Optional[Dict]) -> None:
        self._tags = tags

    def set_last_monitored(self, last_monitored: Optional[float]) -> None:
        self._last_monitored = last_monitored

    def reset(self) -> None:
        self.set_tags(None)
        self.set_last_monitored(None)
