import discord
from discord.ext import commands
from discord.ui import View, Button
from utils import user_manager

# Skill display UI with interactive + and - buttons
SKILL_ORDER = ['damage', 'health', 'parry', 'luck', 'resource']
SKILL_NAMES = {
    'damage': '🔥 Pyro Surge',
    'health': '🌊 Aqua Vitality',
    'parry': '🪨 Terra Guard',
    'luck': '🌪 Aero Luck',
    'resource': '🌑 Void Insight'
}
MAX_SKILL_POINTS = 10

class SkillsView(View):
    def __init__(self, uid):
        super().__init__(timeout=None)
        self.uid = uid
        # Arrange buttons per skill in separate rows for clarity
        for i, skill in enumerate(SKILL_ORDER):
            plus = ChangeButton(skill, +1, row=i)
            minus = ChangeButton(skill, -1, row=i)
            self.add_item(plus)
            self.add_item(minus)

class ChangeButton(Button):
    def __init__(self, skill: str, delta: int, row: int):
        symbol = '+' if delta > 0 else '-'
        label = f"{skill[0].upper()}{symbol}"
        style = discord.ButtonStyle.primary if delta > 0 else discord.ButtonStyle.secondary
        super().__init__(label=label, style=style, row=row)
        self.skill = skill
        self.delta = delta

    async def callback(self, interaction: discord.Interaction):
        uid = str(interaction.user.id)
        users = user_manager.get()
        user = users.setdefault(uid, {
            'xp': 0,
            'level': 0,
            'skill_points': 0,
            'skills': {s: 0 for s in SKILL_ORDER}
        })

        available = user.get('skill_points', 0)
        current = user['skills'].get(self.skill, 0)

        # Check operation validity
        if self.delta > 0:
            if available <= 0 or current >= MAX_SKILL_POINTS:
                return await interaction.response.send_message('❌ Cannot increase further.', ephemeral=True)
            user['skill_points'] -= 1
            user['skills'][self.skill] += 1
        else:
            if current <= 0:
                return await interaction.response.send_message('❌ Cannot decrease further.', ephemeral=True)
            user['skill_points'] += 1
            user['skills'][self.skill] -= 1

        user_manager.save()
        # Refresh the UI with updated embed
        await interaction.response.edit_message(
            embed=build_embed(uid, interaction.user.name),
            view=SkillsView(uid)
        )

def build_embed(uid: str, display_name: str) -> discord.Embed:
    users = user_manager.get()
    user = users.get(uid, {})
    # Calculate level on the fly to avoid stale data
    xp = user.get('xp', 0)
    level = xp // 100
    pts = user.get('skill_points', 0)
    skills = user.get('skills', {})

    embed = discord.Embed(title=f"{display_name}'s Skills")
    embed.add_field(name='📈 Level', value=str(level), inline=True)
    embed.add_field(name='⭐ Available Points', value=str(pts), inline=True)

    # Display each skill with boxes
    for key in SKILL_ORDER:
        val = skills.get(key, 0)
        filled = '■' * val
        empty = '□' * (MAX_SKILL_POINTS - val)
        embed.add_field(name=SKILL_NAMES[key], value=filled + empty, inline=False)

    embed.set_footer(text='Use the + / - buttons to allocate skill points (max 10 each)')
    return embed

class SkillsUICog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='skills')
    async def skills(self, ctx):
        """Display and adjust your skill points UI"""
        uid = str(ctx.author.id)
        users = user_manager.get()
        users.setdefault(uid, {
            'xp': 0,
            'level': 0,
            'skill_points': 0,
            'skills': {s: 0 for s in SKILL_ORDER}
        })
        user_manager.save()

        embed = build_embed(uid, ctx.author.name)
        await ctx.send(embed=embed, view=SkillsView(uid))

async def setup(bot):
    await bot.add_cog(SkillsUICog(bot))
