from dataclasses import dataclass


@dataclass
class Map:
    name: str = ''
    width: int = 0
    height: int = 0
    mineral_fields: list = None
