from fastapi_startkit.masoniteorm.seeds import Seeder

from app.models.identity import Identity
from app.models.membership import Membership
from app.models.tenant import Tenant


def _pk(value):
    return value.get("id") if isinstance(value, dict) else value


class MembershipSeeder(Seeder):
    async def run(self):
        # email -> tenant slugs the user may access. multi@ is in BOTH (demos SSO).
        grants = {
            "multi@example.com": ["tenant-a", "tenant-b"],
            "only-a@example.com": ["tenant-a"],
            "only-b@example.com": ["tenant-b"],
        }

        for email, slugs in grants.items():
            identity = await Identity.where("email", email).first()
            if identity is None:
                continue
            identity_id = _pk(identity.id)
            for slug in slugs:
                tenant = await Tenant.where("slug", slug).first()
                if tenant is None:
                    continue
                tenant_id = _pk(tenant.id)
                await Membership.first_or_create(
                    {"identity_id": identity_id, "tenant_id": tenant_id},
                    {"identity_id": identity_id, "tenant_id": tenant_id, "role": "member"},
                )
