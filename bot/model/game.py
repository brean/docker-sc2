import datetime
from dataclasses import dataclass


@dataclass
class GameStep:
    iteration: int
    units: list
    structures: list
    enemy_units: list
    enemy_structures: list


@dataclass
class GameInfo:
    game_id: str = None
    bot_name: str = 'unknown'
    map: str = 'unknown'
    opponent_name: str = 'unknown'
    started: datetime.datetime = 0
    finished: datetime.datetime = 0
    result: int = 0  # default to tie
    steps: int = 0
