import discord
from discord.ext import commands
from discord.ui import View, Button
from random import randint, choices, random
from utils import user_manager
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
        self.max_chambers = randint(4, 8)
        self.loot = []
        self.xp = 0
        self.enemy_hp = None
        self.enemy_atk = None
        self.player_hp = 100
        self.special_used = False

    def gen_enemy(self):
        lvl = self.depth
        hp = 20 + lvl * 5
        atk = 5 + lvl * 2
        self.enemy_hp = hp
        self.enemy_atk = atk
        return {'name': 'Goblin', 'hp': hp, 'atk': atk}

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
        user = users.setdefault(uid, {'level': 0, 'xp': 0, 'shards': [], 'inventory': {}, 'current_run': None})
        if not user['shards']:
            return await ctx.send("❌ You have no Shards. Craft one with !craft <element>.")
        shard = user['shards'].pop(0)
        session = RunSession(ctx.author.id, shard)
        active_runs[ctx.author.id] = session
        user_manager.save()
        await self.send_combat(ctx, session)

    async def send_combat(self, ctx_or_interaction, session):
        enemy = session.gen_enemy()
        embed = discord.Embed(title=f"Rift Chamber {session.depth}", description="🧟 A wild enemy appears!")
        embed.add_field(name="Enemy HP", value=str(enemy['hp']), inline=True)
        embed.add_field(name="Your HP", value=str(session.player_hp), inline=True)
        view = CombatView(self, session)

        if isinstance(ctx_or_interaction, commands.Context):
            await ctx_or_interaction.send(embed=embed, view=view)
        else:
            await ctx_or_interaction.response.edit_message(embed=embed, view=view)

    async def finish_run(self, interaction, session, conquered=False):
        users = user_manager.get()
        uid = str(session.user_id)
        user = users[uid]
        inv = user.setdefault('inventory', {})
        for item in session.loot:
            inv[item['name']] = inv.get(item['name'], 0) + item['qty']
        user['xp'] += session.xp
        user_manager.save()
        active_runs.pop(session.user_id, None)

        message = "🌟 **Rift Conquered!**" if conquered else "🏃 You ran from the Rift."
        await interaction.response.edit_message(embed=discord.Embed(
            title="Run Complete!",
            description=f"{message} Loot: {len(session.loot)} items XP: {session.xp}"), view=None)


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
        sess = self.session
        damage = 15
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

        embed = discord.Embed(title=f"Rift Chamber {sess.depth}", description="You hit the enemy!")
        embed.add_field(name="Enemy HP", value=str(max(sess.enemy_hp, 0)), inline=True)
        embed.add_field(name="Your HP", value=str(sess.player_hp), inline=True)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label='🎯 Parry', style=discord.ButtonStyle.secondary)
    async def parry(self, interaction: discord.Interaction, button: discord.ui.Button):
        sess = self.session
        success = random() < 0.5

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
        await self.cog.send_combat(interaction, self.session)

    @discord.ui.button(label='🏃 Run', style=discord.ButtonStyle.danger)
    async def run(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.cog.finish_run(interaction, self.session, conquered=False)


async def setup(bot):
    await bot.add_cog(RunCog(bot))
