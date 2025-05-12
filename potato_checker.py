import multiprocessing
from collections import defaultdict
from time import sleep
from typing import Dict, Any, Iterable

import requests

from messages import *
from settings import *

# Constants
SERVER_URL = "https://potato.tf/api/serverstatus"
PROGRESS_URL = "https://potato.tf/api/waveprogress?steamid="
REFRESH_DELAY_IN_SECONDS = 10


def load_servers() -> List[Dict[str, Any]]:
    return requests.get(SERVER_URL).json()


def load_uncompleted_missions(steam_id: int = USER_STEAM_ID) -> Dict[str, Set[str]]:
    uncompleted = defaultdict(set)
    progress = requests.get(f"{PROGRESS_URL}{steam_id}").json()['waveProgress']
    for mission in progress:
        if False in mission['waveProgress']:
            uncompleted[mission['map']].add(mission['mission'])
    return uncompleted


def is_relevant_server(server: Dict[str, Set[str]]) -> bool:
    return server['region'] not in IGNORED_REGIONS


def is_current_server(server: Dict[str, Set[str]]) -> bool:
    return USER_STEAM_ID in server['steamIds']


def player_needs_mission(uncompleted: Dict[str, Set[str]], mission: str) -> bool:
    for ms in uncompleted.values():
        if mission in ms:
            return True
    return False


def get_player_count(server: Dict[str, Any]) -> int:
    return max(server['playersRed'] + server['playersBlu'] + server['playersConnecting'], len(server['steamIds']))


def get_max_players(server: Dict[str, Any]) -> int:
    return max(server['playersMax'], 6)


class DefaultDict(defaultdict):
    def __missing__(self, key):
        return key


class PotatoChecker:
    def __init__(self, message_queue: multiprocessing.Queue):
        self.message_queue = message_queue
        self.map_to_nice_name = DefaultDict()
        self.mission_to_nice_name = DefaultDict()
        self.user_uncompleted_missions = load_uncompleted_missions()
        self._load_maps_and_missions()

    def _load_maps_and_missions(self):
        all_missions = requests.get(f"{PROGRESS_URL}{USER_STEAM_ID}").json()['waveProgress']
        for mission in all_missions:
            self.map_to_nice_name[mission['map']] = mission['mapNiceName']
            self.mission_to_nice_name[mission['mission']] = mission['missionNiceName']

    def _to_server_data_list(self, servers: Iterable[Dict[str, Any]]) -> ServerDataList:
        to_data = lambda s: ServerData(s['serverName'],
                                       s['region'],
                                       self.map_to_nice_name[s['mapNoVersion']],
                                       self.mission_to_nice_name[s['mission']],
                                       s['mission'],
                                       not s['mission'] in self.user_uncompleted_missions[s['mapNoVersion']],
                                       s['status'],
                                       get_player_count(s),
                                       get_max_players(s),
                                       s['wave'],
                                       s['maxWave'],
                                       s['address'])
        return ServerDataList(list(map(to_data, servers)))

    def _to_current_server_data(self, server: Dict[str, Any], previous_data: CurrentServerData) -> CurrentServerData:
        map_no_version = server['mapNoVersion']
        map_nice_name = self.map_to_nice_name[map_no_version]
        mission_nice_name = self.mission_to_nice_name[server['mission']]
        steam_ids = set(server['steamIds'])

        # Load uncompleted missions for other players if the map or mission changed, or if a player joins or leaves,
        # otherwise keep the loaded data from the previous iteration
        if (previous_data.is_empty() or
                previous_data.map != map_nice_name or
                previous_data.mission != mission_nice_name or
                previous_data.player_steam_ids != steam_ids):
            uncompleted_missions_for_current_map = []
            other_players_uncompleted_missions = []
            for steam_id in server['steamIds']:
                if steam_id == USER_STEAM_ID:
                    continue
                other_players_uncompleted_missions.append(load_uncompleted_missions(steam_id))

            for m in self.user_uncompleted_missions[map_no_version]:
                needed_by_other_players = 0
                for other_player_uncompleted in other_players_uncompleted_missions:
                    if m in other_player_uncompleted[map_no_version]:
                        needed_by_other_players += 1
                uncompleted_missions_for_current_map.append((self.mission_to_nice_name[m], m, needed_by_other_players))
        else:
            uncompleted_missions_for_current_map = previous_data.uncompleted_missions

        return CurrentServerData(server['region'],
                                 map_nice_name,
                                 mission_nice_name,
                                 server['mission'],
                                 server['wave'],
                                 server['maxWave'],
                                 get_player_count(server),
                                 get_max_players(server),
                                 steam_ids,
                                 uncompleted_missions_for_current_map)

    def mainloop(self) -> None:
        current_server = CurrentServerData()

        while True:
            all_servers = load_servers()

            matching_servers = filter(is_relevant_server, all_servers)
            self.message_queue.put(self._to_server_data_list(matching_servers))

            new_current_server = next((self._to_current_server_data(s, current_server)
                                       for s in all_servers if is_current_server(s)),
                                      CurrentServerData())

            # Reload user progress on map or mission change, and on reset of wave
            if not current_server.is_empty():
                if (new_current_server.map != current_server.map or
                        new_current_server.mission != current_server.mission or
                        new_current_server.wave < current_server.wave):
                    self.user_uncompleted_missions = load_uncompleted_missions()
            current_server = new_current_server

            self.message_queue.put(current_server)

            sleep(REFRESH_DELAY_IN_SECONDS)
