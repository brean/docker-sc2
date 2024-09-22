import datetime
# use json to store for web-visualization
import json
import os
import random
from pathlib import Path

from websockets.sync.client import connect

# use opencv to visualize the map
import cv2
import numpy as np

from sc2 import maps
from sc2.bot_ai import BotAI
from sc2.data import Difficulty, Race, Result
from sc2.ids.unit_typeid import UnitTypeId
from sc2.main import run_game
from sc2.player import Bot, Computer

BASE_DIR = Path(__file__).parent.absolute() / 'data'
RED = 2
GREEN = 1
BLUE = 0

# Based on the original CannonRush that comes with burnysc2, MIT licensed


class CannonRushBot(BotAI):
    def __init__(self, websocket):
        super().__init__()
        self.websocket = websocket
        self.img_num = 0
        self.map_saved = False
        self.json_game_data = []
        self.map_data = None

    def mark_pixel(self, img, items, color):
        for item in items:
            x, y = item.position_tuple
            img[int(x)][int(y)] = color

    def _parse_position(self, item):
        return [p for p in item.position_tuple]

    def items_to_list(self, items):
        data = []
        for item in items:
            pos = self._parse_position(item)
            data.append(pos + [item.type_id.value])
        return data

    def int_result(self, result):
        return {
            Result.Tie: 0,
            Result.Victory: 1,
            Result.Defeat: 2,
            Result.Undecided: -1,
        }[result]

    async def on_end(self, game_result):
        now = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        info_data = {
            'result': self.int_result(game_result),
            'steps': len(self.json_game_data),
            'game_data': now
        }
        # game info
        with open(str(BASE_DIR / 'replays' / f'info_{now}.json'), 'w') as fd:
            json.dump(info_data, fd)
        # game data
        with open(str(BASE_DIR / 'replays' / f'data_{now}.json'), 'w') as fd:
            json.dump(self.json_game_data, fd)
        info_data['type'] = 'game_ended'
        await self.send_json(info_data)
        await super().on_end(game_result)

    async def send_json(self, data):
        self.websocket.send(json.dumps(data))

    async def send_map(self):
        height, width = self.game_info.map_size
        await self.send_json({
            'type': 'map',
            'width': width,
            'height': height,
            'mineral_field': self.items_to_list(self.mineral_field)
        })

    async def send_state(self, iteration=-1):
        """Send system state to server."""
        if iteration == 0:
            await self.send_map()
        await self.send_json({
            'type': 'step',
            'iteration': iteration,
            'units': self.items_to_list(self.units),
            'structures': self.items_to_list(self.structures),
            'enemy_units': self.items_to_list(self.enemy_units),
            'enemy_structures': self.items_to_list(self.enemy_structures)
        })

    async def visualize_map(self):
        height, width = self.game_info.map_size
        img = np.zeros((height, width, 3), np.uint8)
        self.mark_pixel(img, self.mineral_field, [255, 50, 50])
        self.mark_pixel(img, self.enemy_units, [30, 30, 255])
        self.mark_pixel(img, self.enemy_structures, [50, 50, 235])
        self.mark_pixel(img, self.units, [30, 255, 30])
        self.mark_pixel(img, self.structures, [50, 235, 50])
        self.img_num += 1
        print(f'{self.img_num}.png')
        cv2.imwrite(f'{self.img_num}.png', img)
        return

    def save_state(self):
        # store state in JSON format (we might want to use some serialization
        # later).
        if not self.map_data:
            self.map_data = self.save_map()
        data = [
            self.items_to_list(self.units),
            self.items_to_list(self.structures),
            self.items_to_list(self.enemy_structures),
            self.items_to_list(self.enemy_units)
        ]
        self.json_game_data.append(data)

    def save_map(self, map_name=None):
        if not map_name:
            map_name = self.game_info.map_name
        # store map as Web-readable json-dict
        filename = BASE_DIR / 'maps' / f'{map_name}.json'
        if filename.exists():
            return None
        data = [
            [x for x in self.game_info.map_size],
            self.items_to_list(self.mineral_field),
        ]
        with open(str(filename), 'w') as fp:
            json.dump(data, fp, indent=2)
        return data

    async def on_step(self, iteration):
        # await self.visualize_map()
        # send data to the custom websocket server
        self.save_state()
        await self.send_state(iteration)

        if iteration == 0:
            await self.chat_send("(probe)(pylon)(cannon)(cannon)(gg)")

        if not self.townhalls:
            # Attack with all workers if we don't have any nexuses left,
            # attack-move on enemy spawn (doesn't work on 4 player map)
            # so that probes auto attack on the way
            for worker in self.workers:
                worker.attack(self.enemy_start_locations[0])
            return
        else:
            nexus = self.townhalls.random

        # Make probes until we have 16 total
        if self.supply_workers < 16 and nexus.is_idle:
            if self.can_afford(UnitTypeId.PROBE):
                nexus.train(UnitTypeId.PROBE)

        # If we have no pylon, build one near starting nexus
        elif not self.structures(UnitTypeId.PYLON) and \
                self.already_pending(UnitTypeId.PYLON) == 0:
            if self.can_afford(UnitTypeId.PYLON):
                await self.build(UnitTypeId.PYLON, near=nexus)

        # If we have no forge, build one near the pylon that is closest to
        # our starting nexus
        elif not self.structures(UnitTypeId.FORGE):
            pylon_ready = self.structures(UnitTypeId.PYLON).ready
            if pylon_ready:
                if self.can_afford(UnitTypeId.FORGE):
                    await self.build(
                        UnitTypeId.FORGE,
                        near=pylon_ready.closest_to(nexus))

        # If we have less than 2 pylons, build one at the enemy base
        elif self.structures(UnitTypeId.PYLON).amount < 2:
            if self.can_afford(UnitTypeId.PYLON):
                pos = self.enemy_start_locations[0].towards(
                    self.game_info.map_center, random.randrange(8, 15))
                await self.build(UnitTypeId.PYLON, near=pos)

        # If we have no cannons but at least 2 completed pylons, automatically
        # find a placement location and build them near enemy start location
        elif not self.structures(UnitTypeId.PHOTONCANNON):
            if self.structures(UnitTypeId.PYLON).ready.amount >= 2 and \
                    self.can_afford(UnitTypeId.PHOTONCANNON):
                pylon = self.structures(UnitTypeId.PYLON).closer_than(
                    20, self.enemy_start_locations[0]).random
                await self.build(UnitTypeId.PHOTONCANNON, near=pylon)

        # Decide if we should make pylon or cannons, then build them at
        # random location near enemy spawn
        elif self.can_afford(UnitTypeId.PYLON) and \
                self.can_afford(UnitTypeId.PHOTONCANNON):
            # Ensure "fair" decision
            for _ in range(20):
                pos = self.enemy_start_locations[0].random_on_distance(
                    random.randrange(5, 12))
                building = UnitTypeId.PHOTONCANNON if \
                    self.state.psionic_matrix.covers(pos) else \
                    UnitTypeId.PYLON
                await self.build(building, near=pos)


def main():
    # debug which map we are loading
    print(f'load map {os.environ["MAP"]}')

    # save replay in user path to directly run local sc2 for debugging
    now = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

    # replay_path = f'/root/Documents/StarCraftII/Accounts/'
    # account_id = os.listdir(replay_path)[0]
    # replay_path += account_id
    # replay_path += '/'
    # replay_path += os.listdir(replay_path)[0]
    replays_dir = BASE_DIR / 'replays'
    if not replays_dir.exists():
        os.mkdir(replays_dir)
    replay_path = replays_dir / f'{now}.sc2replay'
    print(f'save replay as {replay_path}')
    # TODO: start paused, wait for connection and only start when the client
    # tells us to or when we have an autostart flag set.
    with connect("ws://localhost:8000/sc_client") as websocket:
        run_game(
            maps.get(os.environ['MAP']),
            [
                Bot(
                    Race.Protoss,
                    CannonRushBot(websocket),
                    name="CheeseCannon"),
                Computer(Race.Protoss, Difficulty.Medium)
            ],
            realtime=False,
            save_replay_as=replay_path
        )


if __name__ == "__main__":
    main()
