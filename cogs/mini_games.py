import discord
import random
from discord.ext import commands
from utils import user_manager

user_sessions = {}

class MiniGames(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.football_sessions = {}

    @commands.command(name="gamble")
    async def sports_game(self, ctx):
        await ctx.send("🎮 Choose a mini-game to play:", view=SportSelect(self))

# --------- Main Game Select View ----------
class SportSelect(discord.ui.View):
    def __init__(self, cog):
        super().__init__()
        self.cog = cog

    @discord.ui.button(label="Football ⚽", style=discord.ButtonStyle.success)
    async def football(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("⚽ Choose where to shoot!", view=FootballShootView(self.cog, interaction.user, 0, 0, 1))

    @discord.ui.button(label="✊✋✌️", style=discord.ButtonStyle.secondary)
    async def sps(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Choose your move:", view=SPSView())

    @discord.ui.button(label="Luck Spin 🎰", style=discord.ButtonStyle.danger)
    async def luck(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Pick your luck emoji:", view=LuckSpinView())

    @discord.ui.button(label="7up 7down 🎲", style=discord.ButtonStyle.primary)
    async def updown(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_sessions[interaction.user.id] = {}
        await interaction.response.send_message("Enter the amount you want to bet:", ephemeral=True)

        def check(m):
            return m.author == interaction.user and m.channel == interaction.channel

        try:
            msg = await self.cog.bot.wait_for('message', check=check, timeout=30.0)
            amount = int(msg.content)
            if amount <= 0:
                raise ValueError()
        except:
            await interaction.followup.send("Invalid amount or timeout! Try again using `!gamble`.", ephemeral=True)
            return

        user_sessions[interaction.user.id]['bet'] = amount
        number = random.randint(1, 14)
        user_sessions[interaction.user.id]['number'] = number

        await interaction.followup.send(
            f"You've bet **{amount} coins**. Choose: Will the number be above or below 7?",
            view=SevenUpDownView()
        )

# --------- Football Penalty Shootout ----------
class FootballShootView(discord.ui.View):
    def __init__(self, cog, user, score, turn, round_num):
        super().__init__()
        self.cog = cog
        self.user = user
        self.score = score
        self.turn = turn
        self.round_num = round_num

        for pos in ["Left", "Center", "Right"]:
            self.add_item(FootballButton(pos, self))

class FootballButton(discord.ui.Button):
    def __init__(self, direction, parent):
        super().__init__(label=direction, style=discord.ButtonStyle.primary)
        self.direction = direction
        self.parent = parent

    async def callback(self, interaction):
        goalie = random.choice(["Left", "Center", "Right"])
        if self.direction == goalie:
            msg = f"🧤 You shot {self.direction}, Goalie dived {goalie}. ❌ Miss!"
        else:
            self.parent.score += 1
            msg = f"⚽ You shot {self.direction}, Goalie dived {goalie}. ✅ Goal!"

        if self.parent.round_num >= 5:
            result = f"\n\n🏁 Final Score: {self.parent.score}/5"
            if self.parent.score >= 3:
                result += "\n🎉 You win! +50 coins"
                user_manager.add_coins(self.parent.user.id, 50)
            else:
                result += "\n💀 You lose! -10 coins"
                user_manager.remove_coins(self.parent.user.id,10)
            await interaction.response.edit_message(content=msg + result, view=None)
        else:
            await interaction.response.edit_message(content=msg, view=FootballShootView(self.parent.cog, self.parent.user, self.parent.score, self.parent.turn, self.parent.round_num + 1))

# --------- Stone Paper Scissors ----------
class SPSView(discord.ui.View):
    def __init__(self):
        super().__init__()
        for move in ["Stone", "Paper", "Scissors"]:
            self.add_item(SPSButton(move))

class SPSButton(discord.ui.Button):
    def __init__(self, move):
        super().__init__(label=move, style=discord.ButtonStyle.primary)
        self.move = move

    async def callback(self, interaction):
        user = interaction.user
        comp = random.choice(["Stone", "Paper", "Scissors"])
        result = f"You chose **{self.move}**, computer chose **{comp}**.\n"

        if self.move == comp:
            result += "It's a draw! 🤝"
        elif (self.move == "Stone" and comp == "Scissors") or \
             (self.move == "Paper" and comp == "Stone") or \
             (self.move == "Scissors" and comp == "Paper"):
            result += "You win! 🎉 +50 coins"
            user_manager.add_coins(user.id, 50)
        else:
            result += "Computer wins! 🤖 -10 coins"
            user_manager.remove_coins(user.id,10)

        await interaction.response.edit_message(content=result, view=None)

# --------- Luck Spin ----------
class LuckSpinView(discord.ui.View):
    @discord.ui.button(label="🍀", style=discord.ButtonStyle.success)
    async def clover(self, interaction, button):
        await self.spin(interaction, "🍀")

    @discord.ui.button(label="💎", style=discord.ButtonStyle.primary)
    async def diamond(self, interaction, button):
        await self.spin(interaction, "💎")

    @discord.ui.button(label="💀", style=discord.ButtonStyle.danger)
    async def skull(self, interaction, button):
        await self.spin(interaction, "💀")

    async def spin(self, interaction, choice):
        result = random.choice(["🍀", "💎", "💀"])
        if result == choice:
            text = f"🎰 You spun **{result}**. It's a match! x5 coins 🎉"
            user_manager.multiply_coins(interaction.user.id,5)
        else:
            text = f"🎰 You spun **{result}**. No match. Try again! you lost half of your coins "
            user_manager.multiply_coins(interaction.user.id,0.5)
        await interaction.response.edit_message(content=text, view=None)

# --------- 7up 7down ----------
class SevenUpDownView(discord.ui.View):
    @discord.ui.button(label="Up (8-14)", style=discord.ButtonStyle.success)
    async def up(self, interaction: discord.Interaction, button: discord.ui.Button):
        await resolve_updown(interaction, "up")

    @discord.ui.button(label="Down (1-6)", style=discord.ButtonStyle.primary)
    async def down(self, interaction: discord.Interaction, button: discord.ui.Button):
        await resolve_updown(interaction, "down")

async def resolve_updown(interaction: discord.Interaction, choice):
    session = user_sessions.get(interaction.user.id, {})
    number = session.get('number')
    bet = session.get('bet')

    if number == 7:
        result = f"The number is **7**! It's a neutral number. You lost **{bet} coins**. 💸"
        user_manager.remove_coins(interaction.user.id, bet)
    elif (number > 7 and choice == "up") or (number < 7 and choice == "down"):
        result = f"The number is **{number}**. You guessed right! You win **{bet * 2} coins**! 🤑"
        user_manager.add_coins(interaction.user.id, bet * 2)
    else:
        result = f"The number is **{number}**. Wrong guess! You lost **{bet} coins**. 💸"
        user_manager.remove_coins(interaction.user.id, bet)

    await interaction.response.edit_message(content=result, view=None)

# --------- Setup ----------
async def setup(bot):
    await bot.add_cog(MiniGames(bot))
