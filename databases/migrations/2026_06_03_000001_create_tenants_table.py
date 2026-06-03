"""Create-tenants-table Migration."""

from fastapi_startkit.masoniteorm import Migration


class CreateTenantsTable(Migration):
    async def up(self):
        """Run the migrations."""
        async with await self.schema.create("tenants") as table:
            table.increments("id")
            table.string("slug").unique()
            table.string("name")

            table.timestamps()

    async def down(self):
        """Revert the migrations."""
        await self.schema.drop("tenants")
