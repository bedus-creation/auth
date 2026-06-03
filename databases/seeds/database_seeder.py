from fastapi_startkit.masoniteorm.seeds import Seeder

from .identity_seeder import IdentitySeeder


class DatabaseSeeder(Seeder):
    async def run(self):
        await self.call(IdentitySeeder)
