from typing import Tuple
war_ranks = [0, 20, 200, 800, 2000, 2700, 3500, 5000]
xp_ranks = [0, 10e6, 50e6, 500e6, 1e9, 2.5e9, 5e9, 10e9]
numeral_map = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX"]
# returns (rank, next_count)
def get_war_rank(warcnt: int) -> Tuple[int, int]:
    i = 0
    while i < len(war_ranks):
        if warcnt < war_ranks[i]:
            break
        i += 1
    return numeral_map[i-1], war_ranks[min(i, len(war_ranks)-1)]

def get_xp_rank(xp: int) -> Tuple[int, int]:
    i = 0
    while i < len(xp_ranks):
        if xp < xp_ranks[i]:
            break
        i += 1
    return numeral_map[i-1], xp_ranks[min(i, len(xp_ranks)-1)]
