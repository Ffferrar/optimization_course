import sys


def parse_file(path):
    with open(path) as f:
        lines = f.read().strip().split('\n')
    n = int(lines[0].strip())
    coords = []
    for i in range(1, n + 1):
        parts = lines[i].split()
        x, y = float(parts[0]), float(parts[1])
        coords.append((x, y))
    return n, coords


def parse_stdin():
    data = sys.stdin.read().split()
    idx = 0
    n = int(data[idx]); idx += 1
    coords = []
    for i in range(n):
        x = float(data[idx]); idx += 1
        y = float(data[idx]); idx += 1
        coords.append((x, y))
    return n, coords
