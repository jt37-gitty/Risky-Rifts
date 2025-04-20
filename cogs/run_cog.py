import discord
from discord.ext import commands
from discord.ui import View, Button
from random import randint, choices, random
from utils import user_manager
from data.rift_data import RIFT_DATA
import json, os

# Load loot tables
data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
with open(os.path.join(data_dir, 'items.json'), 'r') as f:
    LOOT_TABLE = json.load(f)

active_runs = {}

class RunSession:
    def __init__(self, user_id, shard):
        self.user_id = user_id
        self.shard = shard
        self.depth = 1
        self.max_chambers = randint(5, 10)
        self.loot = []
        self.xp = 0

        users = user_manager.get()
        udata = users.get(str(user_id), {})
        level = udata.get('level', 0)
        self.player_hp = 100 + level * 10

        element = shard['element']
        mob_data = RIFT_DATA[element]
        self.enemy_element = element
        self.generate_enemy()

        users = user_manager.get()
        udata = users.get(str(user_id), {})
        level = udata.get('level', 0)
        self.player_hp = 100 + level * 10

        self.special_used = False

    def generate_enemy(self):
        mob_data = RIFT_DATA[self.shard['element']]
        users = user_manager.get()
        udata = users.get(str(self.user_id), {})
        level = udata.get('level', 0)
        self.enemy_name = mob_data['mob']
        self.enemy_hp = (self.depth + 1) ** 2 + mob_data['hp'] + level * 5
        self.enemy_atk = int(mob_data['atk'] * (1 + 0.05 * (self.depth - 1)))

    def roll_loot(self):
        tbl = LOOT_TABLE.get(self.shard['element'], [])
        if not tbl:
            return None
        choice = choices(tbl, weights=[i['weight'] for i in tbl])[0]
        qty = randint(choice.get('min', 1), choice.get('max', 1))
        return {'name': choice['name'], 'qty': qty}


class RunCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='start')
    async def start(self, ctx):
        users = user_manager.get()
        uid = str(ctx.author.id)
        user = users.setdefault(uid, {'level': 0, 'xp': 0, 'skill_points': 0, 'shards': [], 'inventory': {}, 'current_run': None})
        if not user['shards']:
            return await ctx.send("❌ You have no Shards. Craft one with !craft.")
        shard = user['shards'].pop(0)
        session = RunSession(ctx.author.id, shard)
        active_runs[ctx.author.id] = session
        user_manager.save()
        await self.send_combat(ctx, session)

    async def send_combat(self, ctx_or_interaction, session):
        rift_info = RIFT_DATA[session.shard['element']]
        embed = discord.Embed(
            title=f"{session.shard['element'].title()} Rift - Chamber {session.depth}",
            description=f"{rift_info['mob']} emerges from the shadows...",
            color=rift_info['color']
        )
        embed.add_field(name="Enemy HP", value=str(session.enemy_hp), inline=True)
        embed.add_field(name="Your HP", value=str(session.player_hp), inline=True)
        view = CombatView(self, session)

        if isinstance(ctx_or_interaction, commands.Context):
            await ctx_or_interaction.send(embed=embed, view=view)
        else:
            await ctx_or_interaction.response.edit_message(embed=embed, view=view)

    async def finish_run(self, interaction, session, conquered=False):
        from data.items import ITEM_ELEMENT_MAP
        ELEMENT_EMOJIS = {
            "pyrith": "🔥", "aquarem": "💧", "terravite": "🪨", "aythest": "🌪", "voidite": "🌑"
        }

        users = user_manager.get()
        uid = str(session.user_id)
        user = users[uid]

        # Add loot to inventory
        inv = user.setdefault('inventory', {})
        for item in session.loot:
            inv[item['name']] = inv.get(item['name'], 0) + item['qty']

        # XP, level, and skill point gain
        old_level = user.get('level', 0)
        user['xp'] += session.xp
        new_level = user['xp'] // 100
        user['level'] = new_level



        # Exhaust equipped gear
        eq = user.get('equipped', {})
        lost_gear = []
        for slot in ('weapon', 'armor'):
            gear = eq.pop(slot, None)
            if gear:
                inv[gear] = inv.get(gear, 0) - 1
                if inv[gear] <= 0:
                    del inv[gear]
                lost_gear.append((slot, gear))

        user_manager.save()
        active_runs.pop(session.user_id, None)

        # 🧾 Build summary
        message = "🌟 **Rift Conquered!**" if conquered else "🏃 You ran from the Rift."
        coins = user.get("coins", 0)
        level = user['level']
        xp_bar = f"({user['xp'] % 100}/100)"

        summary = f"{message}\n\n"
        summary += f"📈 **Level {level}** {xp_bar}\n"
        summary += f"💰 **Coins Earned:** {coins}\n"
        summary += f"⭐ **XP Gained:** {session.xp}\n"

        if session.loot:
            summary += "\n📦 **Loot Collected:**\n"
            for item in session.loot:
                elem = ITEM_ELEMENT_MAP.get(item['name'])
                emoji = ELEMENT_EMOJIS.get(elem, "📦")
                summary += f"{emoji} {item['name']} x{item['qty']}\n"

        if lost_gear:
            summary += "\n🎽 **Exhausted Gear:**\n"
            for slot, gear in lost_gear:
                emoji = "🗡️" if slot == "weapon" else "🛡️"
                summary += f"{emoji} {gear}\n"

        await interaction.response.edit_message(
            embed=discord.Embed(title="Run Complete!", description=summary.strip()),
            view=None
        )


class CombatView(View):
    def __init__(self, cog, session):
        super().__init__(timeout=None)
        self.cog = cog
        self.session = session

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.session.user_id:
            await interaction.response.send_message("❌ This is not your Rift!", ephemeral=True)
            return False
        return True

    @discord.ui.button(label='🗡️ Attack', style=discord.ButtonStyle.primary)
    async def attack(self, interaction: discord.Interaction, button: discord.ui.Button):
        from random import randint
        sess = self.session
        users = user_manager.get()
        uid = str(interaction.user.id)
        user = users.get(uid, {})

        damage = randint(12, 18)

        # Crit chance
        crit_chance = 0.1
        is_crit = randint(1, 100) <= int(crit_chance * 100)
        if is_crit:
            damage = int(damage * 1.5)

        # Elemental Multiplier
        from utils.element_utils import get_multiplier  # Make sure this is imported
        weapon_name = user.get("equipped", {}).get("weapon")
        from data.items import ITEM_ELEMENT_MAP
        weapon_elem = ITEM_ELEMENT_MAP.get(weapon_name)
        multiplier = get_multiplier(weapon_elem, sess.enemy_element)
        damage = int(damage * multiplier)

        # Apply damage
        sess.enemy_hp -= damage

        if sess.enemy_hp <= 0:
            loot = sess.roll_loot()
            sess.loot.append(loot)
            sess.xp += 10
            if sess.depth >= sess.max_chambers:
                await self.cog.finish_run(interaction, sess, conquered=True)
            else:
                view = ContinueView(self.cog, sess)
                await interaction.response.edit_message(embed=discord.Embed(
                    title=f"Chamber {sess.depth} Cleared!",
                    description=f"Loot: {loot['qty']}x {loot['name']} XP gained: 10"), view=view)
            return

        sess.player_hp -= sess.enemy_atk

        if sess.player_hp <= 0:
            await interaction.response.edit_message(embed=discord.Embed(
                title="You Died... ☠️",
                description="All loot lost. Better luck next time!"
            ), view=None)
            active_runs.pop(sess.user_id, None)
            return

        msg = f"You hit the enemy for {damage} damage!"
        if is_crit:
            msg += " 💥 Critical hit!"

        embed = discord.Embed(title=f"Rift Chamber {sess.depth}", description=msg)
        embed.add_field(name="Enemy HP", value=str(max(sess.enemy_hp, 0)), inline=True)
        embed.add_field(name="Your HP", value=str(sess.player_hp), inline=True)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label='🎯 Parry', style=discord.ButtonStyle.secondary)
    async def parry(self, interaction: discord.Interaction, button: discord.ui.Button):
        sess = self.session

        users = user_manager.get()
        uid = str(interaction.user.id)
        user = users.get(uid, {})

        # Calculate parry success with Terra skill
        parry_base = 0.5 + 0.02 * (sess.depth - 1)
        parry_chance = parry_base
        success = random() < parry_chance

        if success:
            sess.enemy_hp -= sess.enemy_atk
            msg = f"🎯 Parry successful! You reflected {sess.enemy_atk} damage!"
        else:
            dmg = int(sess.enemy_atk * 1.5)
            sess.player_hp -= dmg
            msg = f"❌ Parry failed! You took {dmg} damage."

        if sess.enemy_hp <= 0:
            loot = sess.roll_loot()
            sess.loot.append(loot)
            sess.xp += 10
            if sess.depth >= sess.max_chambers:
                await self.cog.finish_run(interaction, sess, conquered=True)
            else:
                view = ContinueView(self.cog, sess)
                await interaction.response.edit_message(embed=discord.Embed(
                    title=f"Chamber {sess.depth} Cleared!",
                    description=f"{msg} Loot: {loot['qty']}x {loot['name']} XP gained: 10"), view=view)
            return

        if sess.player_hp <= 0:
            await interaction.response.edit_message(embed=discord.Embed(
                title="You Died... ☠️",
                description=f"{msg} All loot lost. Better luck next time!"), view=None)
            active_runs.pop(sess.user_id, None)
            return

        embed = discord.Embed(title=f"Rift Chamber {sess.depth}", description=msg)
        embed.add_field(name="Enemy HP", value=str(max(sess.enemy_hp, 0)), inline=True)
        embed.add_field(name="Your HP", value=str(sess.player_hp), inline=True)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label='✨ Special', style=discord.ButtonStyle.success)
    async def special(self, interaction: discord.Interaction, button: discord.ui.Button):
        sess = self.session
        if sess.special_used:
            await interaction.response.send_message("✨ You've already used your special this run!", ephemeral=True)
            return
        sess.special_used = True
        sess.enemy_hp -= 40

        embed = discord.Embed(title=f"Rift Chamber {sess.depth}",
                              description="✨ You unleashed your special attack!")
        embed.add_field(name="Enemy HP", value=str(max(sess.enemy_hp, 0)), inline=True)
        embed.add_field(name="Your HP", value=str(sess.player_hp), inline=True)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label='🏃 Run', style=discord.ButtonStyle.danger)
    async def run(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.cog.finish_run(interaction, self.session, conquered=False)


class ContinueView(View):
    def __init__(self, cog, session):
        super().__init__(timeout=None)
        self.cog = cog
        self.session = session

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.session.user_id:
            await interaction.response.send_message("❌ This is not your Rift!", ephemeral=True)
            return False
        return True

    @discord.ui.button(label='➡️ Continue', style=discord.ButtonStyle.success)
    async def cont(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.session.depth += 1
        self.session.generate_enemy()
        await self.cog.send_combat(interaction, self.session)

    @discord.ui.button(label='🏃 Run', style=discord.ButtonStyle.danger)
    async def run(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.cog.finish_run(interaction, self.session, conquered=False)


async def setup(bot):
    await bot.add_cog(RunCog(bot))
