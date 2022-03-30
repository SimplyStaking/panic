class GitHubRepoConfig:
    def __init__(self, repo_id: str, parent_id: str, repo_name: str,
                 monitor_repo: bool, releases_page: str) -> None:
        self._repo_id = repo_id
        self._parent_id = parent_id
        self._repo_name = repo_name
        self._monitor_repo = monitor_repo
        self._releases_page = releases_page

    def __str__(self) -> str:
        return self.repo_name

    @property
    def repo_id(self) -> str:
        return self._repo_id

    @property
    def parent_id(self) -> str:
        return self._parent_id

    @property
    def repo_name(self) -> str:
        return self._repo_name

    @property
    def monitor_repo(self) -> bool:
        return self._monitor_repo

    @property
    def releases_page(self) -> str:
        return self._releases_page

    def set_repo_id(self, repo_id: str) -> None:
        self._repo_id = repo_id

    def set_parent_id(self, parent_id: str) -> None:
        self._parent_id = parent_id

    def set_repo_name(self, repo_name) -> None:
        self._repo_name = repo_name

    def set_monitor_repo(self, monitor_repo) -> None:
        self._monitor_repo = monitor_repo

    def set_releases_page(self, releases_page) -> None:
        self._releases_page = releases_page


class DockerHubRepoConfig:
    def __init__(self, repo_id: str, parent_id: str, repo_namespace: str,
                 repo_name: str, monitor_repo: bool, tags_page: str) -> None:
        self._repo_id = repo_id
        self._parent_id = parent_id
        self._repo_namespace = repo_namespace
        self._repo_name = repo_name
        self._monitor_repo = monitor_repo
        self._tags_page = tags_page

    def __str__(self) -> str:
        return self._repo_namespace + '/' + self._repo_name

    @property
    def repo_id(self) -> str:
        return self._repo_id

    @property
    def parent_id(self) -> str:
        return self._parent_id

    @property
    def repo_namespace(self) -> str:
        return self._repo_namespace

    @property
    def repo_name(self) -> str:
        return self._repo_name

    @property
    def monitor_repo(self) -> bool:
        return self._monitor_repo

    @property
    def tags_page(self) -> str:
        return self._tags_page

    def set_repo_id(self, repo_id: str) -> None:
        self._repo_id = repo_id

    def set_parent_id(self, parent_id: str) -> None:
        self._parent_id = parent_id

    def set_repo_namespace(self, repo_namespace) -> None:
        self._repo_namespace = repo_namespace

    def set_repo_name(self, repo_name) -> None:
        self._repo_name = repo_name

    def set_monitor_repo(self, monitor_repo) -> None:
        self._monitor_repo = monitor_repo

    def set_tags_page(self, tags_page) -> None:
        self._tags_page = tags_page
