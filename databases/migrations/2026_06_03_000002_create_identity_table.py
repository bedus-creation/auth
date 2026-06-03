"""Create-identity-table Migration."""

from fastapi_startkit.masoniteorm import Migration


class CreateIdentityTable(Migration):
    async def up(self):
        """Run the migrations."""
        async with await self.schema.create("identity") as table:
            table.increments("id")
            table.string("tenant")
            table.string("email")
            table.string("password")
            table.string("name").nullable()
            table.boolean("is_active").default(True)

            table.timestamps()

            # An email is unique within a tenant, not globally.
            table.unique(["tenant", "email"])

    async def down(self):
        """Revert the migrations."""
        await self.schema.drop("identity")
