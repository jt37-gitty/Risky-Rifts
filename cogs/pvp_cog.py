import discord
from discord.ext import commands
from discord.ui import View, Button
from random import choice
import random
from utils import user_manager

active_duels = {}

class PvPSession:
    def __init__(self, user1, user2):
        self.user1 = user1
        self.user2 = user2
        self.hp = {user1.id: self.calculate_hp(user1.id), user2.id: self.calculate_hp(user2.id)}
        self.turn = user1.id
        self.special_used = {user1.id: False, user2.id: False}

    def calculate_hp(self, uid):
        user = user_manager.get().get(str(uid), {})
        level = user.get("level", 0)
        health = user.get("skills", {}).get("health", 0)
        return 100 + level * 10 + health * 10

    def switch_turn(self):
        self.turn = self.user1.id if self.turn == self.user2.id else self.user2.id

class PvPCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="challenge")
    async def challenge(self, ctx, member: discord.Member):
        if member.bot or member.id == ctx.author.id:
            return await ctx.send("❌ Invalid opponent.")
        if ctx.author.id in active_duels or member.id in active_duels:
            return await ctx.send("⚔️ One of the users is already in a duel!")

        view = AcceptView(ctx.author, member, self)
        challenge_message = await ctx.send(f"{member.mention}, do you accept the challenge from {ctx.author.mention}?", view=view)
        view.message = challenge_message  # Store message so we can delete/update it

    async def start_duel(self, channel, user1, user2):
        session = PvPSession(user1, user2)
        active_duels[user1.id] = session
        active_duels[user2.id] = session
        await self.send_duel(channel, session)

    async def send_duel(self, channel, session):
        attacker = session.user1 if session.turn == session.user1.id else session.user2
        defender = session.user2 if session.turn == session.user1.id else session.user1

        embed = discord.Embed(title="⚔️ PvP Duel", description=f"{attacker.mention}'s turn to act!")
        embed.add_field(name=f"{session.user1.display_name}'s HP", value=str(session.hp[session.user1.id]), inline=True)
        embed.add_field(name=f"{session.user2.display_name}'s HP", value=str(session.hp[session.user2.id]), inline=True)

        view = PvPCombatView(self, session, attacker, defender)
        view.message = await channel.send(embed=embed, view=view)

    async def end_duel(self, channel, session, winner, loser):
        users = user_manager.get()
        udata = users.get(str(winner.id), {})
        #udata.setdefault('shards', []).append({'element': choice(['fire', 'ice', 'earth', 'air'])})
        udata["xp"] += 50
        udata["coins"] += 100
        user_manager.save()

        active_duels.pop(session.user1.id, None)
        active_duels.pop(session.user2.id, None)

        embed = discord.Embed(title="🏆 Duel Over", description=f"{winner.mention} has defeated {loser.mention}!")
        embed.add_field(name="Reward", value="🎁 You received a 100 coins and 20XP", inline=False)
        await channel.send(embed=embed)

class AcceptView(View):
    def __init__(self, challenger, challenged, cog):
        super().__init__(timeout=30)
        self.challenger = challenger
        self.challenged = challenged
        self.cog = cog
        self.message = None

    @discord.ui.button(label="✅ Accept", style=discord.ButtonStyle.success)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.challenged.id:
            return await interaction.response.send_message("❌ You're not the one being challenged!", ephemeral=True)

        await interaction.response.defer()
        if self.message:
            await self.message.delete()
        await self.cog.start_duel(interaction.channel, self.challenger, self.challenged)
        self.stop()

    @discord.ui.button(label="❌ Decline", style=discord.ButtonStyle.danger)
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.message:
            await self.message.delete()
        await interaction.response.send_message(f"{self.challenged.mention} declined the challenge.")
        self.stop()

class PvPCombatView(View):
    def __init__(self, cog, session, attacker, defender):
        super().__init__(timeout=30)
        self.cog = cog
        self.session = session
        self.attacker = attacker
        self.defender = defender
        self.message = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.attacker.id:
            await interaction.response.send_message("❌ It's not your turn!", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="🗡️ Attack", style=discord.ButtonStyle.primary)
    async def attack(self, interaction: discord.Interaction, button: discord.ui.Button):
        damage = random.randint(10, 20)
        self.session.hp[self.defender.id] -= damage

        if self.session.hp[self.defender.id] <= 0:
            await interaction.response.defer()
            await self.cog.end_duel(interaction.channel, self.session, self.attacker, self.defender)
            return

        self.session.switch_turn()
        await interaction.response.defer()
        await self.cog.send_duel(interaction.channel, self.session)

    @discord.ui.button(label="🎯 Parry", style=discord.ButtonStyle.secondary)
    async def parry(self, interaction: discord.Interaction, button: discord.ui.Button):
        success = random.random() < 0.5
        damage = random.randint(20, 30)
        if success:
            self.session.hp[self.defender.id] -= damage
            msg = f"✅ Parry success! Reflected {damage} damage."
        else:
            self.session.hp[self.attacker.id] -= int(damage * 1.5)
            msg = f"❌ Parry failed! Took {int(damage * 1.5)} damage."

        if self.session.hp[self.defender.id] <= 0:
            await interaction.response.defer()
            await self.cog.end_duel(interaction.channel, self.session, self.attacker, self.defender)
            return
        elif self.session.hp[self.attacker.id] <= 0:
            await interaction.response.defer()
            await self.cog.end_duel(interaction.channel, self.session, self.defender, self.attacker)
            return

        self.session.switch_turn()
        await interaction.response.send_message(msg, ephemeral=True)
        await self.cog.send_duel(interaction.channel, self.session)

    @discord.ui.button(label="✨ Special", style=discord.ButtonStyle.success)
    async def special(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.session.special_used[self.attacker.id]:
            return await interaction.response.send_message("❗ You've already used your special!", ephemeral=True)

        self.session.special_used[self.attacker.id] = True
        self.session.hp[self.defender.id] -= 30

        if self.session.hp[self.defender.id] <= 0:
            await interaction.response.defer()
            await self.cog.end_duel(interaction.channel, self.session, self.attacker, self.defender)
            return

        self.session.switch_turn()
        await interaction.response.defer()
        await self.cog.send_duel(interaction.channel, self.session)

async def setup(bot):
    await bot.add_cog(PvPCog(bot))



