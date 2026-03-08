"""Manages the bots: start matches and configure persistence."""
from .cannon_rush import CannonRushBot


class BotManager:
    def __init__(self):
        self.bots = {
            'cannon_rush_bot': CannonRushBot
        }

    def start_game(
            self,
            bot_name: str = 'cannon_rush_bot',
            amount: int = 1):
        for idx in range(amount):
            bot = self.bots[bot_name](index=idx)
            bot.start_game()
