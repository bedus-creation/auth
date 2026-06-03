from fastapi_startkit.masoniteorm.seeds import Seeder

from app.models.identity import Identity
from app.services import hashing


class IdentitySeeder(Seeder):
    async def run(self):
        # All demo identities share the password "secret".
        identities = [
            {"tenant": "tenant-a", "email": "admin@tenant-a.com", "name": "Tenant A Admin"},
            {"tenant": "tenant-a", "email": "user@tenant-a.com", "name": "Tenant A User"},
            {"tenant": "tenant-b", "email": "admin@tenant-b.com", "name": "Tenant B Admin"},
        ]

        for data in identities:
            await Identity.first_or_create(
                {"tenant": data["tenant"], "email": data["email"]},
                {
                    "tenant": data["tenant"],
                    "email": data["email"],
                    "name": data["name"],
                    "password": hashing.make("secret"),
                    "is_active": True,
                },
            )
