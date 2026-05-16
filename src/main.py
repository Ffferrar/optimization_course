import sys
import time
from parser import parse_file
from heuristics import solve as heuristic_solve

def validate(edges, color):
    for u, v in edges:
        if color[u] == color[v]:
            return False
    return True

def num_colors(color):
    return max(color) + 1 if color else 0

def solve(path):
    t0 = time.time()
    n, m, adj, edges = parse_file(path)
    tl = int(sys.argv[2]) if len(sys.argv) > 2 else 280
    best = heuristic_solve(n, adj, time_limit=tl)
    k = num_colors(best)
    elapsed = time.time() - t0
    print(f"{k} colors, valid={validate(edges, best)}, time={elapsed:.2f}s", file=sys.stderr)
    print(k)
    print(best)

if __name__ == "__main__":
    solve(sys.argv[1])
