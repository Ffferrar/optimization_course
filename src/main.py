import sys
from parser import parse_file
from heuristics import greedy_desc, greedy_asc, dsatur

def validate(edges, color):
    for u, v in edges:
        if color[u] == color[v]:
            return False
    return True

def num_colors(color):
    return max(color) + 1 if color else 0

def solve(path):
    n, m, adj, edges = parse_file(path)
    best = None
    for fn in [greedy_desc, greedy_asc, dsatur]:
        c = fn(n, adj)
        if validate(edges, c):
            if best is None or num_colors(c) < num_colors(best):
                best = c
    k = num_colors(best)
    print(k)
    print(best)

if __name__ == "__main__":
    solve(sys.argv[1])
