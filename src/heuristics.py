
import time
import random
import math

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


def dsatur_random(n, adj):
    color = [-1] * n
    sat = [set() for _ in range(n)]
    uncolored = set(range(n))
    deg = [len(adj[v]) for v in range(n)]

    for i in range(n):
        best_key = (-1, -1)
        candidates = []
        for v in uncolored:
            key = (len(sat[v]), deg[v])
            if key > best_key:
                best_key = key
                candidates = [v]
            elif key == best_key:
                candidates.append(v)
        v = random.choice(candidates)
        used = {color[u] for u in adj[v] if color[u] != -1}
        c = min_free_color(used)
        color[v] = c
        uncolored.discard(v)
        for u in adj[v]:
            if color[u] == -1:
                sat[u].add(c)
    return color


def _reduce_to_k(n, color, target_k):
    k_cur = max(color) + 1
    if k_cur <= target_k:
        return

    sizes = [0] * k_cur
    for c in color:
        sizes[c] += 1

    elim = set(sorted(range(k_cur), key=lambda c: sizes[c])[:k_cur - target_k])
    remap, idx = {}, 0
    for v in range(n):
        if color[v] in elim:
            color[v] = random.randint(0, target_k - 1)
        else:
            if color[v] not in remap:
                remap[color[v]] = idx
                idx += 1
            color[v] = remap[color[v]]


def tabucol(n, adj, init_color, target_k, deadline):
    if target_k < 1:
        return None

    color = list(init_color)
    _reduce_to_k(n, color, target_k)

    acc = [[0] * target_k for _ in range(n)]
    for v in range(n):
        for u in adj[v]:
            acc[v][color[u]] += 1
    conflicts = sum(acc[v][color[v]] for v in range(n)) // 2
    if conflicts == 0:
        return color

    tenure = int(0.6 * n) + random.randint(0, 9)
    tabu = [[0] * target_k for _ in range(n)]

    for it in range(1, 10**9):
        if time.time() > deadline:
            return None

        best_d, moves = float('inf'), []
        for v in range(n):
            if acc[v][color[v]] == 0:
                continue
            oc = color[v]
            for c in range(target_k):
                if c == oc:
                    continue
                d = acc[v][c] - acc[v][oc]
                if tabu[v][c] > it and conflicts + d > 0:
                    continue
                if d < best_d:
                    best_d, moves = d, [(v, c)]
                elif d == best_d:
                    moves.append((v, c))

        if not moves:
            return None

        v, nc = random.choice(moves)
        oc = color[v]
        for u in adj[v]:
            acc[u][oc] -= 1
            acc[u][nc] += 1
        color[v] = nc
        conflicts += best_d
        tabu[v][oc] = it + tenure + random.randint(0, 9)

        if conflicts == 0:
            return color
    return None


def sa_col(n, adj, init_color, target_k, deadline):
    if target_k < 2:
        return None

    color = list(init_color)
    _reduce_to_k(n, color, target_k)

    acc = [[0] * target_k for _ in range(n)]
    for v in range(n):
        for u in adj[v]:
            acc[v][color[u]] += 1
    conflicts = sum(acc[v][color[v]] for v in range(n)) // 2
    if conflicts == 0:
        return color

    remaining = deadline - time.time()
    if remaining <= 0:
        return None

    temp, t_end = 1.0, 0.001
    alpha = (t_end / temp) ** (1.0 / max(remaining * 500, 1))

    for _ in range(10**9):
        if time.time() > deadline:
            return None

        v = random.randint(0, n - 1)
        if acc[v][color[v]] == 0:
            continue

        oc = color[v]
        nc = random.randint(0, target_k - 2)
        if nc >= oc:
            nc += 1

        d = acc[v][nc] - acc[v][oc]
        if d <= 0 or random.random() < math.exp(-d / max(temp, 1e-10)):
            for u in adj[v]:
                acc[u][oc] -= 1
                acc[u][nc] += 1
            color[v] = nc
            conflicts += d
            if conflicts == 0:
                return color

        temp *= alpha
        if temp < t_end:
            temp = 1.0
    return None


def solve(n, adj, time_limit=280):
    import sys
    start = time.time()
    deadline = start + time_limit

    best = None
    for fn in [greedy_desc, greedy_asc, dsatur]:
        c = fn(n, adj)
        if best is None or max(c) < max(best):
            best = c

    best_k = max(best) + 1
    best_color = list(best)
    print(f"[init] k={best_k} t={time.time()-start:.1f}s", file=sys.stderr)

    rand_end = start + min(time_limit * 0.15, 30)
    no_improve = 0
    while time.time() < rand_end and no_improve < max(50, n):
        c = dsatur_random(n, adj)
        k = max(c) + 1
        if k < best_k:
            best_k, best_color = k, list(c)
            no_improve = 0
            print(f"[rdsatur] k={best_k} t={time.time()-start:.1f}s", file=sys.stderr)
        else:
            no_improve += 1

    solvers = [tabucol, sa_col]
    while best_k > 1 and time.time() < deadline:
        target = best_k - 1
        print(f"[reduce] trying k={target} t={time.time()-start:.1f}s", file=sys.stderr)
        found = False
        for attempt in range(10):
            if time.time() > deadline:
                break
            remaining = deadline - time.time()
            att_deadline = time.time() + remaining / max(10 - attempt, 1)

            if attempt > 0:
                c = dsatur_random(n, adj)
                k = max(c) + 1
                if k < best_k:
                    best_k, best_color = k, list(c)
                    if k <= target:
                        found = True
                        break

            result = solvers[attempt % 2](n, adj, best_color, target, att_deadline)
            if result is not None:
                best_k, best_color = target, result
                print(f"[found] k={best_k} t={time.time()-start:.1f}s", file=sys.stderr)
                found = True
                break
        if not found:
            break

    return best_color
