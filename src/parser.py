import sys

def parse_file(path):
    with open(path) as f:
        lines = f.read().split('\n')
    first = lines[0].split()
    n, m = int(first[0]), int(first[1])
    adj = [set() for i in range(n)]
    edges = []
    for i in range(1, m + 1):
        parts = lines[i].split()
        u, v = int(parts[0]), int(parts[1])
        adj[u].add(v)
        adj[v].add(u)
        edges.append((u, v))
    return n, m, adj, edges

def parse_stdin():
    data = sys.stdin.read().split()
    idx = 0
    n, m = int(data[idx]), int(data[idx+1])
    idx += 2
    adj = [set() for i in range(n)]
    edges = []
    for i in range(m):
        u, v = int(data[idx]), int(data[idx+1])
        idx += 2
        adj[u].add(v)
        adj[v].add(u)
        edges.append((u, v))
    return n, m, adj, edges
