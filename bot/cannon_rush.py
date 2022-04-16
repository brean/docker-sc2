from sc2.player import Bot, Computer
from sc2.ids.unit_typeid import UnitTypeId
import random
import os
import sys

from sc2 import maps
from sc2.bot_ai import BotAI
from sc2.data import Difficulty, Race
from sc2.main import run_game
import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))


class CannonRushBot(BotAI):

    async def on_step(self, iteration):
        if iteration == 0:
            await self.chat_send("(probe)(pylon)(cannon)(cannon)(gg)")

        if not self.townhalls:
            # Attack with all workers if we don't have any nexuses left, attack-move on enemy spawn (doesn't work on 4 player map) so that probes auto attack on the way
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
        elif not self.structures(UnitTypeId.PYLON) and self.already_pending(UnitTypeId.PYLON) == 0:
            if self.can_afford(UnitTypeId.PYLON):
                await self.build(UnitTypeId.PYLON, near=nexus)

        # If we have no forge, build one near the pylon that is closest to our starting nexus
        elif not self.structures(UnitTypeId.FORGE):
            pylon_ready = self.structures(UnitTypeId.PYLON).ready
            if pylon_ready:
                if self.can_afford(UnitTypeId.FORGE):
                    await self.build(UnitTypeId.FORGE, near=pylon_ready.closest_to(nexus))

        # If we have less than 2 pylons, build one at the enemy base
        elif self.structures(UnitTypeId.PYLON).amount < 2:
            if self.can_afford(UnitTypeId.PYLON):
                pos = self.enemy_start_locations[0].towards(
                    self.game_info.map_center, random.randrange(8, 15))
                await self.build(UnitTypeId.PYLON, near=pos)

        # If we have no cannons but at least 2 completed pylons, automatically find a placement location and build them near enemy start location
        elif not self.structures(UnitTypeId.PHOTONCANNON):
            if self.structures(UnitTypeId.PYLON).ready.amount >= 2 and self.can_afford(UnitTypeId.PHOTONCANNON):
                pylon = self.structures(UnitTypeId.PYLON).closer_than(
                    20, self.enemy_start_locations[0]).random
                await self.build(UnitTypeId.PHOTONCANNON, near=pylon)

        # Decide if we should make pylon or cannons, then build them at random location near enemy spawn
        elif self.can_afford(UnitTypeId.PYLON) and self.can_afford(UnitTypeId.PHOTONCANNON):
            # Ensure "fair" decision
            for _ in range(20):
                pos = self.enemy_start_locations[0].random_on_distance(
                    random.randrange(5, 12))
                building = UnitTypeId.PHOTONCANNON if self.state.psionic_matrix.covers(
                    pos) else UnitTypeId.PYLON
                await self.build(building, near=pos)


def main():
    # debug which map we are loading
    print(f'load map {os.environ["MAP"]}')
    
    # save replay in user path to directly run local sc2 for debugging
    now = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    replay_path = f'/root/Documents/StarCraftII/Accounts/'
    account_id = os.listdir(replay_path)[0]
    replay_path += account_id 
    replay_path += '/'
    replay_path += os.listdir(replay_path)[0]
    replay_path += f'/Replays/Multiplayer/{now}.sc2replay'
    print(f'save replay as {replay_path}')

    run_game(
        maps.get(os.environ['MAP']),
        [Bot(Race.Protoss, CannonRushBot(), name="CheeseCannon"),
         Computer(Race.Protoss, Difficulty.Medium)],
        realtime=False,
        save_replay_as=replay_path
    )


if __name__ == "__main__":
    main()
