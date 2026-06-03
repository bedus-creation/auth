from fastapi_startkit.masoniteorm.seeds import Seeder

from app.models.identity import Identity
from app.services import hashing


class IdentitySeeder(Seeder):
    async def run(self):
        # Global users — email unique across the system. Password is "secret".
        identities = [
            {"email": "multi@example.com", "name": "Multi Tenant User"},
            {"email": "only-a@example.com", "name": "Only Tenant A"},
            {"email": "only-b@example.com", "name": "Only Tenant B"},
        ]
        for data in identities:
            await Identity.first_or_create(
                {"email": data["email"]},
                {
                    "email": data["email"],
                    "name": data["name"],
                    "password": hashing.make("secret"),
                    "is_active": True,
                },
            )
