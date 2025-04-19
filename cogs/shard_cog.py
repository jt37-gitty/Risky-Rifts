import discord
from discord.ext import commands
from utils import user_manager

class ShardCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='craft')
    async def craft(self, ctx, element: str):
        users = user_manager.get()
        valid = ['pyrith','aquarem','terravite','aythest','voidite']
        e = element.lower()
        if e not in valid:
            return await ctx.send(f"❌ Invalid element. Choose {', '.join(valid)}.")
        uid = str(ctx.author.id)
        user = users.setdefault(uid, {'level':0,'xp':0,'shards':[], 'inventory':{}, 'current_run':None})
        user['shards'].append({'element': e, 'quality': 'basic'})
        user_manager.save()
        await ctx.send(f"🛠️ {ctx.author.mention} crafted a **{e.title()} Shard**.")

async def setup(bot):
    await bot.add_cog(ShardCog(bot))
