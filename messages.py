from dataclasses import dataclass, field
from typing import List, Set, Tuple


@dataclass
class ServerData:
    server_name: str
    region: str
    map: str
    mission: str
    mission_name: str
    completed: bool
    status: str
    player_count: int
    player_max_count: int
    wave: int
    max_wave: int
    address: str


@dataclass
class ServerDataList:
    data: List[ServerData]


@dataclass
class CurrentServerData:
    region: str = ""
    map: str = ""
    mission: str = ""
    mission_name: str = ""
    wave: int = 0
    max_wave: int = 0
    player_count: int = 0
    player_max_count: int = 0
    player_steam_ids: Set[int] = field(default_factory=set)
    uncompleted_missions: List[Tuple[str, str, int]] = field(default_factory=list)

    def is_empty(self):
        return self.region == ""
