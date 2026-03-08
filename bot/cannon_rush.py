import datetime
# use json to store for web-visualization
import json
import os
import random
from pathlib import Path

from .persistence.local_files import PersistenceLocalFiles
from .persistence.websocket import PersistenceWebSocket

from sc2 import maps
from sc2.bot_ai import BotAI
from sc2.data import Difficulty, Race, Result
from sc2.ids.unit_typeid import UnitTypeId
from sc2.main import run_game
from sc2.paths import Paths
from sc2.player import Bot, Computer

# Based on the original CannonRush that comes with burnysc2, MIT licensed
BASE_DIR = Path(__file__).parent.absolute() / 'data'


class CannonRushBot(BotAI):
    def __init__(self, websocket, map_name: str):
        super().__init__()
        self.persistence = [
            # WebSocket and LocalFile
            PersistenceLocalFiles(),
            PersistenceWebSocket(websocket)
        ]
        self.websocket = websocket
        self.map_saved = False
        self.json_game_data = []
        self.map_name = map_name
        self.map_data = None
        self.started = datetime.datetime.now()

    def _parse_position(self, item):
        return [p for p in item.position_tuple]

    def items_to_list(self, items):
        data = []
        for item in items:
            pos = self._parse_position(item)
            data.append(pos + [item.type_id.value])
        return data

    def int_result(self, result: Result) -> int:
        return {
            Result.Tie: 0,
            Result.Victory: 1,
            Result.Defeat: 2,
            Result.Undecided: -1,
        }[result]

    async def on_end(self, game_result):
        # iterate over all persistence and call save
        for persistence in self.persistence:
            await persistence.save(self)
        now = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        file_base = str(now)
        # see GameInfo
        info_data = {
            'game_id': file_base,
            'bot_name': 'CheeseCannon',
            'map': self.map_name,
            'opponent_name': 'pc_protoss_medium',
            'started': self.started,
            'finished': datetime.datetime.now(),
            'result': self.int_result(game_result),
            'steps': len(self.json_game_data),
        }
        # game info
        info_path = str(BASE_DIR / 'replays' / f'info_{file_base}.json')
        with open(info_path, 'w', encoding='utf-8') as fd:
            json.dump(info_data, fd)
        # game data
        game_path = str(BASE_DIR / 'replays' / f'data_{file_base}.json')
        with open(game_path, 'w', encoding='utf-8') as fd:
            json.dump(self.json_game_data, fd)
        info_data['type'] = 'game_ended'
        await self.send_json(info_data)
        await super().on_end(game_result)

    def save_state(self):
        # store state in JSON format (we might want to use some serialization
        # later).
        if not self.map_data:
            self.map_data = self.save_map()
        data = [
            self.items_to_list(self.units),
            self.items_to_list(self.state.structures),
            self.items_to_list(self.state.enemy_structures),
            self.items_to_list(self.state.enemy_units)
        ]
        self.json_game_data.append(data)

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
        elif not self.state.structures(UnitTypeId.PYLON) and \
                self.already_pending(UnitTypeId.PYLON) == 0:
            if self.can_afford(UnitTypeId.PYLON):
                await self.build(UnitTypeId.PYLON, near=nexus)

        # If we have no forge, build one near the pylon that is closest to
        # our starting nexus
        elif not self.state.structures(UnitTypeId.FORGE):
            pylon_ready = self.state.structures(UnitTypeId.PYLON).ready
            if pylon_ready:
                if self.can_afford(UnitTypeId.FORGE):
                    await self.build(
                        UnitTypeId.FORGE,
                        near=pylon_ready.closest_to(nexus))

        # If we have less than 2 pylons, build one at the enemy base
        elif self.state.structures(UnitTypeId.PYLON).amount < 2:
            if self.can_afford(UnitTypeId.PYLON):
                pos = self.enemy_start_locations[0].towards(
                    self.game_info.map_center, random.randrange(8, 15))
                await self.build(UnitTypeId.PYLON, near=pos)

        # If we have no cannons but at least 2 completed pylons, automatically
        # find a placement location and build them near enemy start location
        elif not self.state.structures(UnitTypeId.PHOTONCANNON):
            if self.state.structures(UnitTypeId.PYLON).ready.amount >= 2 and \
                    self.can_afford(UnitTypeId.PHOTONCANNON):
                pylon = self.state.structures(UnitTypeId.PYLON).closer_than(
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


def start_game(map_name=None, websocket=None):
    # debug which map we are loading
    map_name = os.environ['MAP'] if not map_name else map_name
    print(f'load map {map_name}')

    # save replay in user path to directly run local sc2 for debugging
    now = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    replays_dir = BASE_DIR / 'replays'
    if not replays_dir.exists():
        os.mkdir(replays_dir)
    replay_path = replays_dir / f'{now}.sc2replay'
    print(f'save replay as {replay_path}')
    run_game(
        maps.get(map_name),
        [
            Bot(
                Race.Protoss,
                CannonRushBot(websocket, map_name),
                name="CheeseCannon"),
            Computer(Race.Protoss, Difficulty.Medium)
        ],
        realtime=False,
        save_replay_as=replay_path
    )


def maps_list():
    maps_lst = []
    for map_dir in (p for p in Paths.MAPS.iterdir()):
        if map_dir.is_dir():
            if 'Melee' in str(map_dir) or 'mini_games' in str(map_dir):
                continue
            for map_file in (p.name for p in map_dir.iterdir()):
                if map_file.lower().endswith('sc2map'):
                    maps_lst.append(map_file[:-7])
    return maps_lst


def main():
    maps_lst = maps_list()
    # just start a new game on the first map we find
    # Normally the bot_manager should start the game, for debugging!
    # we can run the game from here as well.
    if 'MAP' in os.environ:
        next_map = os.environ['MAP']
    else:
        print('no map given, choosing one randomly from the map pool:')
        next_map = random.choice(maps_lst)
    print(next_map)
    # TODO: async loop
    #start_game(map_name=next_map, websocket=None)


if __name__ == "__main__":
    main()
