from fastapi_startkit.masoniteorm.seeds import Seeder

from app.models.tenant import Tenant


class TenantSeeder(Seeder):
    async def run(self):
        tenants = [
            {"slug": "tenant-a", "name": "Tenant A"},
            {"slug": "tenant-b", "name": "Tenant B"},
        ]
        for data in tenants:
            await Tenant.first_or_create({"slug": data["slug"]}, data)
