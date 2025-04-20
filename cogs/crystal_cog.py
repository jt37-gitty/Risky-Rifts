import discord
from discord.ext import commands
from discord.ui import View
from random import randint, sample, choice
from utils import user_manager

TOTAL_STAGES = 20

class CrystalSession:
    def __init__(self):
        self.progress = 0
        self.failures = 0
        # Pick between 5 and 15 unique failure points from 1..19
        n = randint(5, 15)
        pts = sample(range(1, TOTAL_STAGES), n)
        # Always fail at the final stage (just before completion)
        if TOTAL_STAGES - 1 not in pts:
            pts.append(TOTAL_STAGES - 1)
        self.failure_stages = sorted(pts)

class CrystalCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.sessions = {}  # uid -> CrystalSession

    @commands.command(name="shard")
    async def start_crystal(self, ctx):
        uid = str(ctx.author.id)
        users = user_manager.get()
        user = users.setdefault(uid, {
            'xp': 0, 'level': 0, 'coins': 0,
            'archetype': None, 'equipped': {},
            'inventory': {}, 'shards': [], 'current_run': None
        })

        # If they already have a shard, block them
        if user['shards']:
            return await ctx.send("❌ You already have an active Shard. Use it in a Rift first.")

        # If they’re mid‑refinement, block re‑entry
        if uid in self.sessions:
            return await ctx.send("🌀 You're already refining a shard!")

        # Start a new session
        self.sessions[uid] = CrystalSession()
        await ctx.send(
            f"{ctx.author.mention} 🔧 Compressing unstable energy into a shard...\n"
            f"Progress: 0/{TOTAL_STAGES}",
            view=CrystalView(self, uid)
        )

async def setup(bot):
    await bot.add_cog(CrystalCog(bot))

class CrystalView(View):
    def __init__(self, cog: CrystalCog, uid: str):
        super().__init__(timeout=None)
        self.cog = cog
        self.uid = uid

    @discord.ui.button(label="🔩 Refine", style=discord.ButtonStyle.primary)
    async def refine(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = str(interaction.user.id)
        # Must match the session owner
        if user_id != self.uid:
            return await interaction.response.send_message(
                "❌ This shard isn’t yours to refine!", ephemeral=True
            )

        session = self.cog.sessions[self.uid]
        session.progress += 1  # Move forward first

        # Check for a failure at this new progress
        if session.failure_stages and session.progress == session.failure_stages[0]:
            session.failures += 1
            session.progress = 0
            session.failure_stages.pop(0)
            return await interaction.response.edit_message(
                content=(
                    "💥 Instability! The crystal shatters and you must start over.\n"
                    f"Progress: 0/{TOTAL_STAGES}"
                ),
                view=self
            )

        # Check for success
        if session.progress >= TOTAL_STAGES:
            users = user_manager.get()
            user = users[self.uid]
            elem = choice(["pyrith", "aquarem", "terravite", "aythest", "voidite"])
            user["shards"].append({"element": elem, "quality": "basic"})
            user_manager.save()
            # End session and report success (element hidden)
            del self.cog.sessions[self.uid]
            return await interaction.response.edit_message(
                content=(
                    "✨ You finally stabilize the shard.\n"
                    "A mysterious Rift Shard hums in your hand..."
                ),
                view=None
            )

        # Otherwise, show updated progress
        return await interaction.response.edit_message(
            content=(
                "🔧 Refining... You steady the crystal.\n"
                f"Progress: {session.progress}/{TOTAL_STAGES}"
            ),
            view=self
        )
