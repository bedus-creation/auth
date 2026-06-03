"""Create-auth-codes-table Migration (one-time OAuth2 authorization codes)."""

from fastapi_startkit.masoniteorm import Migration


class CreateAuthCodesTable(Migration):
    async def up(self):
        """Run the migrations."""
        async with await self.schema.create("auth_codes") as table:
            table.increments("id")
            table.string("code").unique()
            table.integer("identity_id").unsigned()
            table.string("client_id")
            table.text("redirect_uri")
            table.integer("expires_at")  # epoch seconds
            table.boolean("used").default(False)

            table.timestamps()

    async def down(self):
        """Revert the migrations."""
        await self.schema.drop("auth_codes")
