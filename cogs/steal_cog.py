import discord
from discord.ext import commands
import random
from utils import user_manager

class StealCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="steal")
    @commands.cooldown(1, 10800, commands.BucketType.user)  # 3 hours cooldown (in seconds)
    async def steal(self, ctx, target: discord.Member):
        if target.bot or target.id == ctx.author.id:
            return await ctx.send("❌ You can't steal from yourself or a bot.")

        users = user_manager.get()
        stealer_id = str(ctx.author.id)
        target_id = str(target.id)

        stealer = users.setdefault(stealer_id, {})
        victim = users.setdefault(target_id, {})

        stealer.setdefault("coins", 0)
        victim.setdefault("coins", 0)

        if victim["coins"] < 10:
            return await ctx.send("🪙 The target doesn't have enough coins to steal from!")

        success = random.random() < 0.4  # 40% chance to succeed

        if success:
            stolen = random.randint(10, max(50, victim["coins"]))
            victim["coins"] -= stolen
            stealer["coins"] += stolen
            user_manager.save()
            await ctx.send(f"💸 {ctx.author.mention} successfully stole **{stolen} coins** from {target.mention}!")
        else:
            fine = random.randint(50,stealer["coins"])
            stealer["coins"] = max(0, stealer["coins"] - fine)
            user_manager.save()
            await ctx.send(f"🚨 {ctx.author.mention} got caught trying to steal from {target.mention} and lost **{fine} coins** in fines!")

    @steal.error
    async def steal_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            retry_after = int(error.retry_after)
            hours = retry_after // 3600
            minutes = (retry_after % 3600) // 60
            seconds = retry_after % 60
            await ctx.send(f"🕒 You can try stealing again in **{hours}h {minutes}m {seconds}s**.")
        else:
            raise error  # Re-raise if it's another kind of error

async def setup(bot):
    await bot.add_cog(StealCog(bot))
