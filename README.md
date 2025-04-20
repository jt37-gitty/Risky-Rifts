# ⚔️ Risky Rifts

**Risky Rifts** is a Discord-based RNG-heavy adventure game where players dive into dangerous elemental rifts, fight elemental enemies, collect loot, and make high-stakes decisions.

Designed for a hackathon, this game combines combat, progression, minigames, and randomness in a fast-paced text interface — all run through Discord commands.

---

## 🚀 Getting Started

### 🔧 Prerequisites
- Python 3.10+
- `discord.py` v2.x
- `python-dotenv` for managing your bot token
- Your own Discord bot application + token

### 📦 Install dependencies
```bash
pip install -r requirements.txt
```

### ⚙️ Setup
1. Clone the repository.
2. Add your `.env` file with the following:
```
DISCORD_TOKEN=your-bot-token-here
```
3. Run the bot:
```bash
python main.py
```

---

## 🌀 Gameplay Overview

### 🪨 Shards & Rifts
- Use `!shard` to begin crafting a shard via a frustrating crystal-clicker minigame.
- Crafted shards have a **random hidden element** and **4–8 chambers**.
- Use `!start` to enter the Rift with your shard.
- You may only hold **one shard at a time**.

### ⚔️ Combat System
Combat occurs in each Rift chamber:

- **🗡️ Attack**: Basic attack that scales with skills and elements.
- **🛡️ Parry**: 50/50 gamble to reflect damage or take more.
- **✨ Special**: Element-based ability from your archetype.
- **🏃 Run**: Exit the Rift **after battle** (not during).

Each decision is a gamble — every battle could reward or ruin you.

---

## 🔥 Elements & Archetypes

Each element has:
- Unique **archetype** with a special ability.
- Strengths and weaknesses against others.

| Element   | Archetype     | Special Ability                        |
|-----------|---------------|----------------------------------------|
| Pyrith    | Fire Wizard   | Burn enemy over turns                  |
| Aquarem   | Water Sage    | Heal yourself once                     |
| Terravite | Earth Golem   | Heavy shield to absorb damage          |
| Aythest   | Wind Dancer   | Boost parry chance                     |
| Voidite   | Void Seer     | Double damage or complete failure 🎲    |

Unlock archetypes using `!archetype` (costs coins).

---

## 🎒 Inventory System

Use `!inventory` to view:
- 🧠 Current archetype
- 📈 Level and XP progress
- 💰 Coins
- 🎽 Equipped weapon & armor
- 🗡️ Weapons in inventory
- 🛡️ Armor in inventory
- 🧪 Elemental resources

Use `!equip <item name>` to gear up.

Gear is **exhausted** after a Rift run (whether you conquer, die, or run).

---

## 💹 Progression

- Each Rift chamber grants **XP** and **Coins**
- 100 XP = 1 Level
- Every 10 levels = 1 skill point
- Skill points (via `!skills`) improve:
  - 💥 Damage
  - ❤️ Health
  - 🛡️ Parry chance
  - 🍀 Loot/Luck
  - 🔧 Extra resources

---

## 📦 Loot & Resources

- Loot drops are **elementally weighted** to match the Rift.
- You can gain:
  - Elemental resources (used in crafting, upgrades, cosmetics)
  - Weapons & armor
  - Coins
- Extra loot is granted via skill points and archetype bonuses.

---

## 🧠 Minigames

Outside of Rifts, players can:
- Duel in **PvP**
- Use `!steal` to take coins
- Play themed **sports games**
- Play **crystal crafting minigame** to generate a shard when out of resources

Minigames offer fun and sometimes rage-inducing RNG rewards (or losses).

---

## 🧾 End of Run Summary

When a player ends a Rift (run, death, or victory), they receive a complete summary showing:
- XP earned
- Coins collected
- Loot gained
- Gear exhausted

---

## 📘 Commands Overview

| Command       | Description                                      |
|---------------|--------------------------------------------------|
| `!shard`      | Start shard crafting minigame                    |
| `!start`      | Begin a Rift run using your shard                |
| `!inventory`  | View your bag, gear, coins, XP                   |
| `!equip`      | Equip a weapon or armor from your bag            |
| `!archetype`  | Select an archetype (class)                      |
| `!skills`     | Spend skill points earned by leveling            |
| `!info`       | Learn all game mechanics                         |
| `!tutorial`   | Step-by-step guide for new players               |
| `!steal`      | Attempt to rob another player (PvP)              |
| `!pvp`        | Challenge another player in combat               |

---

## 🧠 Dev Notes

- Player data is stored persistently via JSON.
- Loot tables and gear are elementally themed.
- Every combat action is subject to RNG — so play smart (or pray to the void).

---

## 🏁 Future Plans

- Boss battles at the end of each Rift (with puzzles and phases)
- Cosmetic item system themed around your college
- Element-based item crafting outside of Rifts
- Luck stat affecting all gamble-based actions

---

Made with ❤️ and chaos by **Akshat, Jatin & Gnan** at HackNite.