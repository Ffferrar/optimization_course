
def min_free_color(used):
    c = 0

    while c in used:
        c += 1
    return c

def greedy_desc(n, adj):
    order = sorted(range(n), key=lambda v: -len(adj[v]))
    color = [-1] * n

    for v in order:
        used = {color[u] for u in adj[v] if color[u] != -1}
        color[v] = min_free_color(used)
    return color

def greedy_asc(n, adj):
    order = sorted(range(n), key=lambda v: len(adj[v]))
    color = [-1] * n

    for v in order:
        used = {color[u] for u in adj[v] if color[u] != -1}
        color[v] = min_free_color(used)
    return color

def dsatur(n, adj):
    color = [-1] * n
    sat = [set() for _ in range(n)]
    uncolored = set(range(n))

    for i in range(n):
        best = max(uncolored, key=lambda v: (len(sat[v]), sum(1 for u in adj[v] if color[u] == -1), len(adj[v]), -v))
        used = {color[u] for u in adj[best] if color[u] != -1}
        c = min_free_color(used)
        color[best] = c
        uncolored.discard(best)
        for u in adj[best]:
            if color[u] == -1:
                sat[u].add(c)
    return color
