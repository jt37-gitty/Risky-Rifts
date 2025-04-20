import discord
from discord.ext import commands
from random import choice
from utils import user_manager

ELEMENTS = ['pyrith', 'aquarem', 'terravite', 'aythest', 'voidite']

class ShardCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='craft')
    async def craft(self, ctx):
        users = user_manager.get()
        uid = str(ctx.author.id)
        user = users.setdefault(uid, {
            'level': 0, 'xp': 0, 'coins': 0, 'archetype': None,
            'equipped': {}, 'inventory': {}, 'shards': [], 'current_run': None
        })

        if user['shards']:
            return await ctx.send("❌ You already have an un-used Shard. Run your Rift first!")

        inv = user.get("inventory", {})
        for e in ELEMENTS:
            if inv.get(e.title(), 0) < 5:
                return await ctx.send("🌟 You need at least 5 of each elemental resource to craft a shard.")

        for e in ELEMENTS:
            inv[e.title()] -= 5
            if inv[e.title()] <= 0:
                del inv[e.title()]

        elem = choice(ELEMENTS)
        user['shards'].append({'element': elem, 'quality': 'basic'})
        user_manager.save()
        await ctx.send("🔮 You crafted a **mysterious Shard**... it pulses with unknown power!")

async def setup(bot):
    await bot.add_cog(ShardCog(bot))
