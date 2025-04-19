
import discord
from discord.ext import commands
from utils import user_manager

class InventoryCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="inventory")
    async def inventory(self, ctx):
        uid = str(ctx.author.id)
        users = user_manager.get()
        user = users.get(uid)
        if not user:
            return await ctx.send("❌ No data found for you. Try crafting a shard first.")

        coins = user.get("coins", 0)
        xp = user.get("xp", 0)
        level = xp // 100
        archetype = user.get("archetype", "None").title()
        equipped = user.get("equipped", {})
        inv = user.get("inventory", {})

        embed = discord.Embed(title=f"{ctx.author.name}'s Inventory")
        embed.add_field(name="🧠 Archetype", value=archetype, inline=True)
        embed.add_field(name="📈 Level", value=f"{level} ({xp}/100 XP)", inline=True)
        embed.add_field(name="💰 Coins", value=str(coins), inline=True)

        equipped_str = []
        if equipped.get("weapon"):
            equipped_str.append(f"🗡️ {equipped['weapon']}")
        if equipped.get("armor"):
            equipped_str.append(f"🛡️ {equipped['armor']}")
        embed.add_field(name="🎽 Equipped", value="\n".join(equipped_str) if equipped_str else "None", inline=False)

        if inv:
            inv_lines = [f"{item} x{qty}" for item, qty in inv.items()]
            embed.add_field(name="🎒 Bag", value="\n".join(inv_lines), inline=False)
        else:
            embed.add_field(name="🎒 Bag", value="Empty", inline=False)

        await ctx.send(embed=embed)

    @commands.command(name="equip")
    async def equip(self, ctx, *, item_name: str):
        uid = str(ctx.author.id)
        users = user_manager.get()
        user = users.get(uid)
        if not user:
            return await ctx.send("❌ No data found for you.")

        inv = user.get("inventory", {})
        equipped = user.setdefault("equipped", {})

        if item_name not in inv or inv[item_name] < 1:
            return await ctx.send(f"❌ You don't have '{item_name}' in your inventory.")

        # Determine if item is weapon or armor
        from data.items import ITEM_TYPE_MAP
        item_type = ITEM_TYPE_MAP.get(item_name)
        if not item_type or item_type not in ["weapon", "armour"]:
            return await ctx.send(f"❌ '{item_name}' is not equippable.")

        equipped[item_type if item_type != "armour" else "armor"] = item_name
        user_manager.save()
        await ctx.send(f"✅ Equipped **{item_name}**!")

async def setup(bot):
    await bot.add_cog(InventoryCog(bot))
