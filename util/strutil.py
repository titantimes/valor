def strhash(s: str) -> int:
    h = 0
    for c in s:
        h = ((h << 5)-h) + ord(c)
    return h & 0xFFFFFFFF