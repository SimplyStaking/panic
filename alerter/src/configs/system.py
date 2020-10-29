class SystemConfig:
    def __init__(self, system_id: str, parent_id: str, system_name: str,
                 monitor_system: bool, node_exporter_url: str) -> None:
        self._system_id = system_id
        self._parent_id = parent_id
        self._system_name = system_name
        self._monitor_system = monitor_system
        self._node_exporter_url = node_exporter_url

    def __str__(self) -> str:
        return self.system_name

    @property
    def system_id(self) -> str:
        return self._system_id

    @property
    def parent_id(self) -> str:
        return self._parent_id

    @property
    def system_name(self) -> str:
        return self._system_name

    @property
    def monitor_system(self) -> bool:
        return self._monitor_system

    @property
    def node_exporter_url(self) -> str:
        return self._node_exporter_url

    def set_system_id(self, system_id: str) -> None:
        self._system_id = system_id

    def set_parent_id(self, parent_id: str) -> None:
        self._parent_id = parent_id

    def set_system_name(self, system_name: str) -> None:
        self._system_name = system_name

    def set_monitor_system(self, monitor_system: bool) -> None:
        self._monitor_system = monitor_system

    def set_node_exporter_url(self, node_exporter_url: str) -> None:
        self._node_exporter_url = node_exporter_url
