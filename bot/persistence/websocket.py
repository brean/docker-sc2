import json
from websockets.sync.client import ClientConnection
from . import Persistence
from ..model.map import Map


class PersistenceWebSocket(Persistence):

    def __init__(self, websocket):
        self.websocket = websocket

    async def save(self, data):
        pass

    async def send_json(self, data):
        self.websocket.send(json.dumps(data))

    async def save_map(self):
        height, width = self.game_info.map_size
        await self.send_json({
            'type': 'map',
            'width': width,
            'height': height,
            'mineral_field': self.items_to_list(self.mineral_field)
        })

    async def save_map(self, _map: Map, map_name=None) -> dict:
        if not map_name:
            map_name = self.game_info.map_name
        # store map as Web-readable json-dict
        filename = BASE_DIR / 'maps' / f'{map_name}.json'
        if filename.exists():
            return None
        data = [
            [x for x in self.game_info.map_size],
            self.items_to_list(self.state.mineral_field),
        ]
        with open(str(filename), 'w', encoding='utf-8') as fp:
            json.dump(data, fp, indent=2)
        # return data for visualization
        return data

    async def save_state(self, iteration=-1):
        """Send system state to server."""
        if iteration == 0:
            await self.save_map()
        await self.send_json({
            'type': 'step',
            'iteration': iteration,
            'units': self.items_to_list(self.units),
            'structures': self.items_to_list(self.structures),
            'enemy_units': self.items_to_list(self.enemy_units),
            'enemy_structures': self.items_to_list(self.enemy_structures)
        })