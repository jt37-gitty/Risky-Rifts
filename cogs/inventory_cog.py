import discord
from discord.ext import commands
from utils import user_manager

class InventoryCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='inventory')
    async def inventory(self, ctx):
        users = user_manager.get()
        uid = str(ctx.author.id)
        user = users.get(uid, {})
        inv = user.get('inventory', {})
        if not inv:
            return await ctx.send("Your inventory is empty.")
        lines = [f"**{k}**: {v}" for k, v in inv.items()]
        await ctx.send("\n".join(lines))

    @commands.command(name='level')
    async def level(self, ctx):
        users = user_manager.get()
        uid = str(ctx.author.id)
        user = users.get(uid, {})
        xp = user.get('xp', 0)
        lvl = user.get('level', 0)
        await ctx.send(f"Level: {lvl} | XP: {xp}")

async def setup(bot):
    await bot.add_cog(InventoryCog(bot))
