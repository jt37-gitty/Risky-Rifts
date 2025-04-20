
import random

# Weakness chart: attacker -> defender -> multiplier
WEAKNESS_CHART = {
    'fire':   {'fire': 1.0, 'water': 0.5, 'earth': 1.5, 'air': 1.0, 'void': 1.25},
    'water':  {'fire': 1.5, 'water': 1.0, 'earth': 0.5, 'air': 1.25, 'void': 1.25},
    'earth':  {'fire': 0.5, 'water': 1.5, 'earth': 1.0, 'air': 1.25, 'void': 1.0},
    'air':    {'fire': 1.25, 'water': 0.75, 'earth': 0.5, 'air': 1.0, 'void': 1.5},
    'void':   {'fire': 1.0, 'water': 1.0, 'earth': 1.0, 'air': 1.25, 'void': 1.0}
}

CRIT_CHANCE = 0.1  # 10%
CRIT_MULTIPLIER = 1.5

def get_multiplier(attacker_element: str, defender_element: str) -> float:
    return WEAKNESS_CHART.get(attacker_element, {}).get(defender_element, 1.0)

def roll_crit() -> bool:
    return random.random() < CRIT_CHANCE

def apply_crit(base_damage: int) -> (int, bool):
    if roll_crit():
        return int(base_damage * CRIT_MULTIPLIER), True
    return base_damage, False
