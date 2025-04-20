import discord
from discord.ext import commands
from utils import user_manager

ARCHETYPES = {
    'pyrith': 'Embermage',
    'aquarem': 'Tideshaper',
    'terravite': 'Golemheart',
    'aythest': 'Windblade',
    'voidite': 'Shadeborn'
}

COST = 20
ELEMENT_COST = 10

class ArchetypeCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="archetype")
    async def choose_archetype(self, ctx, element: str):
        uid = str(ctx.author.id)
        users = user_manager.get()
        user = users.setdefault(uid, {
            'xp': 0, 'level': 0, 'coins': 0,
            'inventory': {}, 'shards': [], 'current_run': None
        })

        element = element.lower()
        if element not in ARCHETYPES:
            return await ctx.send(f"❌ Invalid element. Choose from: {', '.join(ARCHETYPES.keys())}.")

        inv = user.get("inventory", {})
        if user.get("coins", 0) < COST:
            return await ctx.send(f"💰 You need {COST} coins to become an archetype.")
        if inv.get(element.title(), 0) < ELEMENT_COST:
            return await ctx.send(f"🌟 You need {ELEMENT_COST}x {element.title()} to unlock this archetype.")

        user['coins'] -= COST
        inv[element.title()] -= ELEMENT_COST
        if inv[element.title()] <= 0:
            del inv[element.title()]
        user['archetype'] = element
        user_manager.save()

        await ctx.send(f"✨ You are now an **{ARCHETYPES[element]}**! (Element: {element.title()})")

async def setup(bot):
    await bot.add_cog(ArchetypeCog(bot))
