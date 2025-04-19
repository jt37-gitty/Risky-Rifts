import discord
from discord.ext import commands
from discord.ui import View, Button
from random import randint, choices
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
        self.loot = []
        self.xp = 0
        self.enemy_hp = None

    def gen_enemy(self):
        lvl = self.depth
        hp = 10 + lvl * 2
        atk = 3 + lvl
        self.enemy_hp = hp
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
        """Begin a Rift run using your first Shard"""
        users = user_manager.get()
        uid = str(ctx.author.id)
        user = users.setdefault(uid, {'level': 0, 'xp': 0, 'shards': [], 'inventory': {}, 'current_run': None})
        if not user['shards']:
            return await ctx.send("❌ You have no Shards. Craft one with !craft <element>.")
        shard = user['shards'].pop(0)
        session = RunSession(uid, shard)
        active_runs[uid] = session
        user_manager.save()
        await self.send_combat(ctx, session)

    async def send_combat(self, ctx_or_interaction, session):
        enemy = session.gen_enemy()
        embed = discord.Embed(title=f"Rift Chamber {session.depth}",
                              description=f"A wild {enemy['name']} appears! HP: {enemy['hp']}")
        view = CombatView(self, session)

        if isinstance(ctx_or_interaction, commands.Context):
            await ctx_or_interaction.send(embed=embed, view=view)
        else:
            await ctx_or_interaction.response.edit_message(embed=embed, view=view)

    async def finish_run(self, interaction, session):
        users = user_manager.get()
        uid = session.user_id
        user = users[uid]
        inv = user.setdefault('inventory', {})
        for item in session.loot:
            inv[item['name']] = inv.get(item['name'], 0) + item['qty']
        user['xp'] += session.xp
        user_manager.save()
        active_runs.pop(uid, None)

        await interaction.response.edit_message(embed=discord.Embed(
            title="Run Complete!",
            description=f"Total loot: {len(session.loot)} items\nTotal XP: {session.xp}"
        ), view=None)


class CombatView(View):
    def __init__(self, cog, session):
        super().__init__(timeout=None)
        self.cog = cog
        self.session = session

    @discord.ui.button(label='Attack', style=discord.ButtonStyle.primary)
    async def attack(self, interaction: discord.Interaction, button: discord.ui.Button):
        sess = self.session
        damage = 5
        sess.enemy_hp -= damage

        if sess.enemy_hp > 0:
            await interaction.response.edit_message(embed=discord.Embed(
                title=f"Rift Chamber {sess.depth}",
                description=f"Enemy HP: {sess.enemy_hp} - you dealt {damage} damage."
            ), view=self)
        else:
            loot = sess.roll_loot()
            sess.loot.append(loot)
            sess.xp += 10
            view = ContinueView(self.cog, sess)
            await interaction.response.edit_message(embed=discord.Embed(
                title=f"Chamber {sess.depth} Cleared!",
                description=f"Loot: {loot['qty']}x {loot['name']}\nXP gained: 10"
            ), view=view)

    @discord.ui.button(label='Extract', style=discord.ButtonStyle.danger)
    async def extract(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.cog.finish_run(interaction, self.session)


class ContinueView(View):
    def __init__(self, cog, session):
        super().__init__(timeout=None)
        self.cog = cog
        self.session = session

    @discord.ui.button(label='Continue', style=discord.ButtonStyle.success)
    async def cont(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.session.depth += 1
        await self.cog.send_combat(interaction, self.session)

    @discord.ui.button(label='Extract', style=discord.ButtonStyle.danger)
    async def extract(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.cog.finish_run(interaction, self.session)


async def setup(bot):
    await bot.add_cog(RunCog(bot))
