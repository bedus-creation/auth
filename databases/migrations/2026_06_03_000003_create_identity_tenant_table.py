"""Create-identity-tenant-table Migration (membership pivot)."""

from fastapi_startkit.masoniteorm import Migration


class CreateIdentityTenantTable(Migration):
    async def up(self):
        """Run the migrations."""
        async with await self.schema.create("identity_tenant") as table:
            table.increments("id")
            table.integer("identity_id").unsigned()
            table.integer("tenant_id").unsigned()
            table.string("role", length=50).default("member")

            table.timestamps()

            table.unique(["identity_id", "tenant_id"])
            table.foreign("identity_id").references("id").on("identity").on_delete("cascade")
            table.foreign("tenant_id").references("id").on("tenants").on_delete("cascade")

    async def down(self):
        """Revert the migrations."""
        await self.schema.drop("identity_tenant")
