import discord
from discord.ext import commands
from discord.ui import View, Button
from random import randint, choices, random
from utils import user_manager
from random import random, randint, choices
from utils.element_utils import get_multiplier, apply_crit
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
        self.enemy_element = choices(['fire', 'water', 'earth', 'air', 'void'])[0]
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
        # 1) Generate enemy (sets session.enemy_element)
        enemy = session.gen_enemy()
        # Map the enemy name based on Rift element
        name_map = {
            'pyrith': 'Blazebeast',
            'aquarem': 'Tidecaller',
            'terravite': 'Stonehide',
            'aythest': 'Windstalker',
            'voidite': 'Dreadshade'
        }
        enemy_name = name_map.get(session.shard['element'], 'Goblin')

        # 2) On first chamber only: send Loadout Summary
        if session.depth == 1 and isinstance(ctx_or_interaction, commands.Context):
            users = user_manager.get()
            user = users[str(ctx_or_interaction.author.id)]
            arche = user.get('archetype', 'None')

            # Friendly names & specials
            arche_names = {
                'pyrith': ('Embermage', 'Inferno Bolt: deal 25 dmg + burn 5×2 turns'),
                'aquarem': ('Tideshaper', 'Healing Wave: restore 20 HP instantly'),
                'terravite': ('Golemheart', 'Stonehide: take 50% less dmg for 2 hits'),
                'aythest': ('Windblade', 'Blurstep: 75% dodge & reflect next hit'),
                'voidite': ('Shadeborn', 'Abyss Pierce: instant kill <25% HP or 30 true dmg')
            }
            cls_name, special_desc = arche_names.get(arche, ('None', 'No special'))

            # Weapon stats
            weap = user.get('equipped', {}).get('weapon', 'None')
            weap_elem = next((i['element'] for pool in LOOT_TABLE.values()
                              for i in pool if i['name'] == weap), 'void')
            base_dmg = 15
            atk_mul = get_multiplier(weap_elem, session.enemy_element)
            final_dmg = int(base_dmg * atk_mul)

            # Enemy stats
            enemy_atk = session.enemy_atk
            arm = user.get('equipped', {}).get('armor', 'None')
            arm_elem = next((i['element'] for pool in LOOT_TABLE.values()
                             for i in pool if i['name'] == arm), 'void')
            def_mul = get_multiplier(session.enemy_element, arm_elem)
            final_atk = int(enemy_atk * def_mul)

            summary = discord.Embed(
                title=f"⚙️ Loadout Summary — {session.shard['element'].title()} Rift",
                description=(
                    f"**Archetype:** {cls_name} — {special_desc}\n\n"
                    f"**Your Attack:** {base_dmg} × {atk_mul:.2f} = **{final_dmg}** dmg\n"
                    f"**Enemy Attack:** {enemy_atk} × {def_mul:.2f} = **{final_atk}** dmg\n\n"
                    f"**Weapon:** {weap} ({weap_elem.title()})\n"
                    f"**Armor:** {arm} ({arm_elem.title()})"
                )
            )
            await ctx_or_interaction.send(embed=summary)

        # 3) Send the actual chamber embed
        embed = discord.Embed(
            title=f"Rift Chamber {session.depth} — {session.shard['element'].title()} Rift",
            description=f"🧟 A wild {enemy_name} appears! HP: {enemy['hp']}"
        )
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

        summary = f"{message}**XP Gained:** {session.xp}**Coins Earned:** {user.get('coins', 0)}"

        if session.loot:
            loot_summary = "".join([f"{item['qty']}x {item['name']}" for item in session.loot])
            summary += f"**Loot Gained:**{loot_summary}"

        eq = user.get('equipped', {})
        if eq.get('weapon') or eq.get('armor'):
            summary += "**Equipped Gear:**"
            if eq.get('weapon'):
                summary += f"🗡️ {eq['weapon']}"
            if eq.get('armor'):
                summary += f"🛡️ {eq['armor']}"

        await interaction.response.edit_message(embed=discord.Embed(title="Run Complete!", description=summary),
                                                view=None)


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

        users = user_manager.get()
        uid = str(interaction.user.id)
        user = users[uid]
        from data.items import ITEM_TYPE_MAP
        users = user_manager.get()
        uid = str(interaction.user.id)
        user = users[uid]
        weapon_name = user.get("equipped", {}).get("weapon")
        weapon_elem = None

        if weapon_name:
            weapon_elem = next(
                (item.get("element") for pool in LOOT_TABLE.values() for item in pool if item["name"] == weapon_name),
                None
            )

        multiplier = get_multiplier(weapon_elem or "void", sess.enemy_element)
        base_damage = 15
        final_damage, is_crit = apply_crit(int(base_damage * multiplier))

        sess.enemy_hp -= final_damage
        crit_text = " 💥 Critical Hit!" if is_crit else ""

        if sess.enemy_hp <= 0:
            loot = sess.roll_loot()
            sess.loot.append(loot)
            sess.xp += 10
            coins = 5 + sess.depth * 1 + users[str(sess.user_id)]['level'] * 2
            users[str(sess.user_id)]['coins'] = users[str(sess.user_id)].get('coins', 0) + coins
            user_manager.save()
            coins = 5 + sess.depth * 1 + users[str(sess.user_id)]['level'] * 2
            users[str(sess.user_id)]['coins'] = users[str(sess.user_id)].get('coins', 0) + coins
            user_manager.save()
            if sess.depth >= sess.max_chambers:
                await self.cog.finish_run(interaction, sess, conquered=True)
            else:
                view = ContinueView(self.cog, sess)
                await interaction.response.edit_message(embed=discord.Embed(
                    title=f"Chamber {sess.depth} Cleared!",
                    description=f"Loot: {loot['qty']}x {loot['name']} XP gained: 10 • 💰 Coins gained: {coins}"),
                    view=view)
            return

        # 🔥 Burn damage to enemy
        if hasattr(sess, "burn_turns") and sess.burn_turns > 0:
            sess.enemy_hp -= sess.burn_dmg
            burn_info = f"🔥 Burn dealt {sess.burn_dmg} damage.\n"
            sess.burn_turns -= 1
        else:
            burn_info = ""

        # 🪨 Stonehide reduction
        dmg = sess.enemy_atk
        if hasattr(sess, "stonehide_turns") and sess.stonehide_turns > 0:
            dmg = int(dmg * 0.5)
            sess.stonehide_turns -= 1
            stone_info = f"🪨 Stonehide reduced damage to {dmg}.\n"
        else:
            stone_info = ""

        # 🌪 Blurstep dodge
        blur_info = ""
        if hasattr(sess, "blurstep") and sess.blurstep:
            from random import random
            if random() < 0.75:
                reflect = int(sess.enemy_atk * 0.5)
                sess.enemy_hp -= reflect
                dmg = 0
                blur_info = f"🌪 Blurstep dodged the attack and reflected {reflect} damage!\n"
            else:
                blur_info = "🌪 Blurstep failed.\n"
            sess.blurstep = False

        # 🛡️ Armor passive effects
        armor_name = user.get("equipped", {}).get("armor")
        armor_elem = None
        if armor_name:
            for pool in LOOT_TABLE.values():
                for item in pool:
                    if item["name"] == armor_name:
                        armor_elem = item.get("element")
                        break

        if armor_elem == "pyrith":
            reflect = int(dmg * 0.05)
            sess.enemy_hp -= reflect
            armor_info = f"🔥 Fire Armor reflected {reflect} damage.\n"
        elif armor_elem == "aquarem":
            from random import random
            if random() < 0.1:
                sess.player_hp += 5
                armor_info = "💧 Water Armor healed you for 5 HP.\n"
            else:
                armor_info = ""
        elif armor_elem == "terravite":
            dmg = max(0, dmg - 2)
            armor_info = f"🪨 Earth Armor reduced damage by 2.\n"
        elif armor_elem == "aythest":
            # Boost parry logic already handled in parry()
            armor_info = ""
        elif armor_elem == "voidite":
            from random import random
            if random() < 0.2:
                dmg = 0
                armor_info = "🌑 Void Armor ignored all damage!\n"
            else:
                armor_info = ""
        else:
            armor_info = ""
        sess.player_hp -= dmg
        details = burn_info + stone_info + blur_info + armor_info

        if sess.player_hp <= 0:
            await interaction.response.edit_message(embed=discord.Embed(
                title="You Died... ☠️",
                description="All loot lost. Better luck next time!"
            ), view=None)
            active_runs.pop(sess.user_id, None)
            return

        embed = discord.Embed(title=f"Rift Chamber {sess.depth} — {sess.shard["element"].title()} Rift",
                              description=f"You hit the enemy for {final_damage} damage!{crit_text}\n" + burn_info + stone_info + blur_info + armor_info)
        embed.add_field(name="Enemy HP", value=str(max(sess.enemy_hp, 0)), inline=True)
        embed.add_field(name="Your HP", value=str(sess.player_hp), inline=True)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label='🎯 Parry', style=discord.ButtonStyle.secondary)
    async def parry(self, interaction: discord.Interaction, button: discord.ui.Button):
        sess = self.session
        users = user_manager.get()
        uid = str(interaction.user.id)
        user = users[uid]

        # 1) Attempt Parry
        success = random() < 0.5
        if success:
            # Reflect damage with elemental + crit
            weapon = user.get("equipped", {}).get("weapon")
            weap_elem = next(
                (itm["element"] for pool in LOOT_TABLE.values() for itm in pool if itm["name"] == weapon),
                "void"
            )
            dmg, is_crit = apply_crit(int(sess.enemy_atk * get_multiplier(weap_elem, sess.enemy_element)))
            sess.enemy_hp -= dmg
            msg = f"🎯 Parry successful! You reflected {dmg} damage{' 💥 Critical!' if is_crit else ''}"
        else:
            # Failed parry: take 150% damage
            dmg = int(sess.enemy_atk * 1.5)
            sess.player_hp -= dmg
            msg = f"❌ Parry failed! You took {dmg} damage."

        # 2) Armor Passive
        armor = user.get("equipped", {}).get("armor")
        armor_info = ""
        if armor == "Fireproof Helm":
            refl = int(dmg * 0.05)
            sess.enemy_hp -= refl
            armor_info = f"\n🔥 Fire Armor reflected {refl} damage."
        elif armor == "Hydro Cloak":
            if random() < 0.1:
                sess.player_hp += 5
                armor_info = "\n💧 Water Armor healed you for 5 HP."
        elif armor == "Golem Plate":
            # Flat reduce 2 (undo 2 of the damage just taken)
            if not success:
                sess.player_hp += 2
                armor_info = "\n🪨 Earth Armor reduced damage by 2."
        elif armor == "Eclipse Guard":
            if random() < 0.2:
                # Negate last damage
                if not success:
                    sess.player_hp += dmg
                armor_info = "\n🌑 Void Armor ignored all damage."

        # 3) Check for end conditions
        if sess.enemy_hp <= 0:
            # Victory or conquest
            return await self.cog.finish_run(interaction, sess, conquered=(sess.depth >= sess.max_chambers))

        if sess.player_hp <= 0:
            # Death path
            return await interaction.response.edit_message(
                embed=discord.Embed(
                    title="You Died... ☠️",
                    description=f"{msg}{armor_info}\nAll loot lost. Better luck next time!"
                ),
                view=None
            )

        # 4) Update the embed with current HP and messages
        embed = discord.Embed(
            title=f"Rift Chamber {sess.depth} — {sess.shard['element'].title()} Rift",
            description=msg + armor_info
        )
        embed.add_field(name="Enemy HP", value=str(max(sess.enemy_hp, 0)), inline=True)
        embed.add_field(name="Your HP", value=str(sess.player_hp), inline=True)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label='✨ Special', style=discord.ButtonStyle.success)
    async def special(self, interaction: discord.Interaction, button: discord.ui.Button):
        sess = self.session
        if sess.special_used:
            await interaction.response.send_message("✨ You've already used your special this run!", ephemeral=True)
            return

        users = user_manager.get()
        uid = str(interaction.user.id)
        user = users[uid]
        sess.special_used = True
        users = user_manager.get()
        uid = str(interaction.user.id)
        user = users[uid]
        archetype = user.get("archetype")

        description = ""
        if archetype == "pyrith":
            sess.enemy_hp -= 25
            sess.burn_turns = 2
            sess.burn_dmg = 5
            description = "🔥 Inferno Bolt! You dealt 25 damage and applied burn (5 dmg for 2 turns)."
        elif archetype == "aquarem":
            healed = min(20, 100 + user.get("level", 0) * 10 - sess.player_hp)
            sess.player_hp += healed
            description = f"💧 Healing Wave! You restored {healed} HP."
        elif archetype == "terravite":
            sess.stonehide_turns = 2
            description = "🪨 Stonehide! You will take 50% less damage for the next 2 attacks."
        elif archetype == "aythest":
            sess.blurstep = True
            description = "🌪 Blurstep! 75% chance to dodge and reflect the next hit."
        elif archetype == "voidite":
            if sess.enemy_hp <= 0.25 * (20 + sess.depth * 5):
                sess.enemy_hp = 0
                description = "🕳️ Abyss Pierce! Instant kill triggered!"
            else:
                sess.enemy_hp -= 30
                description = "🕳️ Abyss Pierce! You dealt 30 true damage."

        embed = discord.Embed(title=f"Rift Chamber {sess.depth} — {sess.shard["element"].title()} Rift",
                              description=description)
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
