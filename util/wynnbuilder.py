import json
import math

t = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz+-"
b64dig = {t[i]: i for i in range(len(t))}

class base64:
    @staticmethod
    def to_int(s: str) -> int:
        return sum((b64dig[s[len(s)-1-i]] << 6*i) for i in range(len(s)))

class ItemDB:
    with open("itemdb.json" if __name__ == "__main__" else "util/itemdb.json") as f:
        db = json.load(f)
    @classmethod
    def get_name(cls, id: int) -> str:
        return cls.db.get(str(id))

def info(build_string: str):
    # first three chars are absolutely useless
    build_string = build_string[3:]
    # find helm, chest, legs, boots, ring1, ring2, bracelet, neck, weapon
    result = ["Helmet", "Chestplate", "Leggings", "Boots", "Ring 1", "Ring 2", "Bracelet", "Necklace", "Weapon", 
    "Strength", "Dexterity", "Intelligence", "Defense", "Agility", "Level"]
    res_vals = []
    for i in range(0, 27, 3):
        res_vals.append(ItemDB.get_name(base64.to_int(build_string[i:i+3])))
    # find skill pts
    for i in range(5):
        v = base64.to_int(build_string[27+i*2:29+i*2])
        if v > 200:
            v = "Impossible (negative points)"
        res_vals.append(str(v))
    # find player level
    lvl = str(base64.to_int(build_string[37:39]))
    return [*zip(result, res_vals+[lvl])]

if __name__ == "__main__":
    print(info('#3_07R0PV0WH0K50050050Jn0KG0Qk0c0D221q021g00001004fI'))