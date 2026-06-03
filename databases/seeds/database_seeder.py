from fastapi_startkit.masoniteorm.seeds import Seeder

from .identity_seeder import IdentitySeeder
from .membership_seeder import MembershipSeeder
from .tenant_seeder import TenantSeeder


class DatabaseSeeder(Seeder):
    async def run(self):
        await self.call(TenantSeeder)
        await self.call(IdentitySeeder)
        await self.call(MembershipSeeder)
