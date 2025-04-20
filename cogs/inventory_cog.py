import discord
from discord.ext import commands
from utils import user_manager
from data.items import ITEM_TYPE_MAP, ITEM_ELEMENT_MAP

ELEMENT_EMOJIS = {
    "pyrith": "🔥", "aquarem": "💧", "terravite": "🪨", "aythest": "🌪", "voidite": "🌑"
}

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
        progress = xp % 100
        archetype = user.get("archetype", "None").title()
        equipped = user.get("equipped", {})
        inv = user.get("inventory", {})

        embed = discord.Embed(title=f"{ctx.author.name}'s Inventory")
        embed.add_field(name="🧠 Archetype", value=archetype, inline=True)
        embed.add_field(name="📈 Level", value=f"{level} ({progress}/100)", inline=True)
        embed.add_field(name="💰 Coins", value=str(coins), inline=True)

        if equipped:
            equipped_str = []
            if equipped.get("weapon"):
                equipped_str.append(f"🗡️ {equipped['weapon']}")
            if equipped.get("armor"):
                equipped_str.append(f"🛡️ {equipped['armor']}")
            embed.add_field(name="🎽 Equipped", value="\n".join(equipped_str), inline=False)
        else:
            embed.add_field(name="🎽 Equipped", value="None", inline=False)

        if inv:
            res_lines, wep_lines, arm_lines, other_lines = [], [], [], []
            for item, qty in inv.items():
                item_type = ITEM_TYPE_MAP.get(item)
                elem = ITEM_ELEMENT_MAP.get(item)
                emoji = ELEMENT_EMOJIS.get(elem.lower(), "📦") if elem else "📦"

                if item.lower() in ELEMENT_EMOJIS:
                    emoji = ELEMENT_EMOJIS[item.lower()]
                    res_lines.append(f"{emoji} {item.title()} x{qty}")
                elif item_type == "weapon":
                    wep_lines.append(f"{emoji} {item} x{qty}")
                elif item_type == "armour":
                    arm_lines.append(f"{emoji} {item} x{qty}")
                else:
                    other_lines.append(f"📦 {item} x{qty}")

            if res_lines:
                embed.add_field(name="🧪 Resources", value="\n".join(res_lines), inline=False)
            if wep_lines:
                embed.add_field(name="🗡️ Weapons", value="\n".join(wep_lines), inline=False)
            if arm_lines:
                embed.add_field(name="🛡️ Armors", value="\n".join(arm_lines), inline=False)
            if other_lines:
                embed.add_field(name="📦 Other", value="\n".join(other_lines), inline=False)
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

        from data.items import ITEM_TYPE_MAP
        item_type = ITEM_TYPE_MAP.get(item_name)
        if not item_type or item_type not in ["weapon", "armour"]:
            return await ctx.send(f"❌ '{item_name}' is not equippable.")

        equipped[item_type if item_type != "armour" else "armor"] = item_name
        user_manager.save()
        await ctx.send(f"✅ Equipped **{item_name}**!")

async def setup(bot):
    await bot.add_cog(InventoryCog(bot))