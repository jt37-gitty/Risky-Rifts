import os
import json
import discord
from discord.ext import commands
import asyncio
from dotenv import load_dotenv
from utils import user_manager

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'✅ Bot is ready as {bot.user}')

async def main():
    user_manager.load()

    async with bot:
        cog_dir = os.path.join(os.path.dirname(__file__), 'cogs')
        for fname in os.listdir(cog_dir):
            if fname.endswith('.py'):
                print(f"🔧 Loading cog: {fname}")
                await bot.load_extension(f'cogs.{fname[:-3]}')
        await bot.start(os.getenv('DISCORD_TOKEN'))

if __name__ == '__main__':
    asyncio.run(main())
