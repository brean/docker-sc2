import json
from websockets.sync.client import connect


class WebSocketManager:
    def __init__(self):
        self.websocket = None

    async def run(self, bot):  # bot: CannonRushBot
        """FIXME: move this to the bot_manager!"""
        with connect("ws://localhost:8000/sc_client") as websocket:
            websocket.send(json.dumps({
                'type': 'new_game',
                'started': False,
                'bot_name': 'cheesy_cannon',
                'maps': bot.maps_lst
            }))
            self.websocket = websocket

            while True:
                data = json.loads(websocket.recv())
                if 'type' in data and data['type'] == 'start_game':
                    bot.start_game(data['map'], websocket)
                    break

    async def send_json(self, data):
        self.websocket.send(json.dumps(data))
