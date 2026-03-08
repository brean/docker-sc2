from pathlib import Path

from . import Persistence


BASE_DIR = Path(__file__).parent.absolute() / 'data'


class PersistenceLocalFiles(Persistence):
    async def run(self, bot):
        pass

    async def save(self, data):
        pass
