"""Create-refresh-tokens-table Migration."""

from fastapi_startkit.masoniteorm import Migration


class CreateRefreshTokensTable(Migration):
    async def up(self):
        """Run the migrations."""
        async with await self.schema.create("refresh_tokens") as table:
            table.increments("id")
            table.string("token").unique()   # opaque random token held by the client
            table.integer("identity_id").unsigned()
            table.string("tenant")           # which tenant this refresh token is for
            table.integer("expires_at")      # epoch seconds
            table.boolean("revoked").default(False)

            table.timestamps()

    async def down(self):
        """Revert the migrations."""
        await self.schema.drop("refresh_tokens")
