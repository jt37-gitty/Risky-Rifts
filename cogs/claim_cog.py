import discord
from discord.ext import commands
from utils import user_manager

# how many coins you need to claim the special role
REQUIRED_COINS = 500
# elemental resources required
ELEMENTS = ['Pyrith', 'Aquarem', 'Terravite', 'Aythest', 'Voidite']

class ClaimCog(commands.Cog):
    """Allows high-level players who hold every element to claim a special role."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='claim')
    @commands.guild_only()
    async def claim(self, ctx):
        uid  = str(ctx.author.id)
        data = user_manager.get().get(uid, None)
        if not data:
            return await ctx.send("❌ You have no data yet. Run some Rifts first!")

        coins = data.get('coins', 0)
        inv   = data.get('inventory', {})

        # check coins
        if coins < REQUIRED_COINS:
            return await ctx.send(f"❌ You need at least {REQUIRED_COINS} coins to claim this role. You have {coins}.")

        # check elemental resources
        missing = [e for e in ELEMENTS if inv.get(e, 0) < 1000]
        if missing:
            return await ctx.send(f"❌ You need 1000 of these elements in your inventory : {', '.join(missing)}.")

        guild     = ctx.guild
        role_name = "🔱 Rift Conqueror"
        # find or create the role
        role = discord.utils.get(guild.roles, name=role_name)
        if not role:
            try:
                role = await guild.create_role(
                    name=role_name,
                    colour=discord.Colour.purple(),
                    reason="Awarded for collecting all elements and enough coins"
                )
            except discord.Forbidden:
                return await ctx.send("❌ I don’t have permission to create the claim role.")
        # assign role
        try:
            await ctx.author.add_roles(role, reason="Claimed Rift Conqueror status")
        except discord.Forbidden:
            return await ctx.send("❌ I don’t have permission to assign roles.")

        # prefix nickname
        member    = ctx.author
        old_nick  = member.display_name
        prefix    = "🔮 "
        if not old_nick.startswith(prefix):
            new_nick = prefix + old_nick
            try:
                await member.edit(nick=new_nick, reason="Prefix for Rift Conqueror")
            except discord.Forbidden:
                return await ctx.send("✅ Role assigned, but I can’t change your nickname.")

        await ctx.send(f"🎉 Congratulations, {member.mention}! You’re now **{role_name}**.")

async def setup(bot):
    await bot.add_cog(ClaimCog(bot))
