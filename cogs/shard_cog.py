import discord
from discord.ext import commands
from random import choice
from utils import user_manager

ELEMENTS = ['pyrith', 'aquarem', 'terravite', 'aythest', 'voidite']

class ShardCog(commands.Cog):
    """Handle random shard crafting, one at a time."""
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='craft')
    async def craft(self, ctx):
        """Craft a random elemental Shard (only one at a time)."""
        users = user_manager.get()
        uid = str(ctx.author.id)
        # Initialize user data with default values
        user = users.setdefault(uid, {
            'level': 0,
            'xp': 0,
            'coins': 0,
            'archetype': None,
            'equipped': {},
            'inventory': {},
            'shards': [],
            'current_run': None
        })

        # Prevent crafting if you already have an un-used shard
        if user['shards']:
            return await ctx.send("❌ You already have an un-used Shard. Run your Rift first!")

        # Choose a random element
        elem = choice(ELEMENTS)
        user['shards'].append({'element': elem, 'quality': 'basic'})
        user_manager.save()

        await ctx.send(f"🔮 You crafted a **mysterious Shard**... it pulses with unknown power!")

async def setup(bot):
    await bot.add_cog(ShardCog(bot))
