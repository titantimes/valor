def to_seconds(s: str):
    lookup = {'s': 1, 'm': 60, 'h': 3600, 'd':3600*24}
    return sum(int(x[:-1])*lookup[x[-1]] for x in s.split(" "))