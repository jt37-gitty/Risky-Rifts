import discord
from discord.ext import commands

class InfoCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="info")
    async def info(self, ctx):
        embed = discord.Embed(
            title="🎮 Risky Rifts — Game Info",
            color=discord.Color.blue()
        )
        embed.add_field(name="🌀 Rifts & Shards", value=(
            "• Craft a shard using `!shard` to enter a Rift.\n"
            "• Each shard has a hidden element and 1–10 chambers.\n"
            "• You can only hold 1 shard at a time."
        ), inline=False)
        embed.add_field(name="⚔️ Combat", value=(
            "• Choose from Attack, Parry, Special, and Run.\n"
            "• Elemental matchups influence damage.\n"
            "• Specials are based on your **archetype**.\n"
            "• Parry has a risk/reward mechanic."
        ), inline=False)
        embed.add_field(name="🛡️ Gear", value=(
            "• Equip elemental weapons and armor.\n"
            "• Gear is exhausted after completing a Rift."
        ), inline=False)
        embed.add_field(name="🧱 Archetypes", value=(
            "• Unlock with coins using `!archetype`.\n"
            "• Each archetype grants a unique special ability."
        ), inline=False)
        embed.add_field(name="📈 Progression", value=(
            "• Gain XP and coins from Rifts.\n"
            "• 100 XP = 1 Level.\n"
            "• Every 10 levels = 1 skill point.\n"
            "• Use `!inventory` to view level, coins, and gear."
        ), inline=False)
        embed.add_field(name="🎲 Outside Rifts", value=(
            "• Play minigames (PvP, Steal, Sports) made by Jatin!\n"
            "• Great way to earn or lose resources."
        ), inline=False)

        await ctx.send(embed=embed)

    @commands.command(name="tutorial")
    async def tutorial(self, ctx):
        embed = discord.Embed(
            title="📚 Risky Rifts Tutorial",
            description="New to the game? Here's a quick walkthrough!",
            color=discord.Color.green()
        )
        embed.add_field(name="1️⃣ Craft a Shard", value="Use `!shard` to begin crafting. You can only hold one.", inline=False)
        embed.add_field(name="2️⃣ Check Inventory", value="Type `!inventory` to see your items, coins, and gear.", inline=False)
        embed.add_field(name="3️⃣ Equip Gear", value="Use `!equip <item name>` if you have weapons or armor.", inline=False)
        embed.add_field(name="4️⃣ Enter the Rift", value="Use `!start` once you have a shard to begin.", inline=False)
        embed.add_field(name="5️⃣ Combat", value=(
            "Choose actions during battle:\n"
            "• 🗡️ Attack — Basic strike\n"
            "• 🛡️ Parry — Risky, may avoid or reflect damage\n"
            "• ✨ Special — Based on your class\n"
            "• 🏃 Run — Exit Rift **after battle**"
        ), inline=False)
        embed.add_field(name="6️⃣ Archetypes", value="Use `!archetype` to pick a class. Each one is unique!", inline=False)
        embed.add_field(name="7️⃣ Leveling", value="Earn XP from Rifts. 100 XP = 1 Level. Leveling grants skill points!", inline=False)
        embed.add_field(name="8️⃣ Minigames", value="Try `!pvp`, `!steal`, and Sports games outside Rifts!", inline=False)

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(InfoCog(bot))