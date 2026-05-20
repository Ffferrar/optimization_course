import sys

FULL_ENUM_LIMIT = 380
TOP_WORST_TAKEN_SWAP21 = 120
TOP_BEST_FREE_SWAP21 = 350
TOP_WORST_TAKEN_SWAP12 = 80
TOP_BEST_FREE_SWAP12 = 130
DP_CAPACITY_LIMIT = 200000


def solve_dp(n, capacity, items):
    dp = [0] * (capacity + 1)
    for value, weight in items:
        for w in range(capacity, weight - 1, -1):
            candidate = dp[w - weight] + value
            if candidate > dp[w]:
                dp[w] = candidate
    return dp[capacity]


def fractional_bound(sorted_items, start, remaining):
    bound = 0
    for i in range(start, len(sorted_items)):
        v, w = sorted_items[i][0], sorted_items[i][1]
        if remaining <= 0:
            break
        if w <= remaining:
            bound += v
            remaining -= w
        else:
            bound += v * remaining / w
            remaining = 0
    return bound


def solve_bnb(n, capacity, items):
    by_density = sorted(items, key=lambda x: -x[0] / x[1] if x[1] else 0)

    best = 0
    used = 0
    for v, w in by_density:
        if used + w <= capacity:
            best += v
            used += w

    stack = [(0, 0, 0)]
    while stack:
        idx, val, wt = stack.pop()
        if idx >= len(by_density):
            continue
        v, w = by_density[idx]

        skip_bound = val + fractional_bound(by_density, idx + 1, capacity - wt)
        if skip_bound > best:
            stack.append((idx + 1, val, wt))

        if wt + w <= capacity:
            take_val = val + v
            if take_val > best:
                best = take_val
            take_bound = take_val + fractional_bound(by_density, idx + 1, capacity - wt - w)
            if take_bound > best:
                stack.append((idx + 1, take_val, wt + w))

    return best


def solve_local_search(n, capacity, items):
    density = [v / w if w > 0 else float('inf') for v, w in items]
    order = sorted(range(n), key=lambda i: -density[i])

    taken = set()
    total_val = 0
    total_wt = 0
    for i in order:
        v, w = items[i]
        if total_wt + w <= capacity:
            taken.add(i)
            total_val += v
            total_wt += w

    improved = True
    while improved:
        improved = False

        worst_taken = sorted(taken, key=lambda i: density[i])
        best_free = sorted(
            [i for i in range(n) if i not in taken],
            key=lambda i: -density[i],
        )

        if n <= FULL_ENUM_LIMIT:
            pool_wt21 = worst_taken
            pool_bf21 = best_free
            pool_wt12 = worst_taken
            pool_bf12 = best_free
        else:
            pool_wt21 = worst_taken[:TOP_WORST_TAKEN_SWAP21]
            pool_bf21 = best_free[:TOP_BEST_FREE_SWAP21]
            pool_wt12 = worst_taken[:TOP_WORST_TAKEN_SWAP12]
            pool_bf12 = best_free[:TOP_BEST_FREE_SWAP12]

        best_delta = 0
        best_move = None

        for ai in range(len(pool_wt21)):
            a = pool_wt21[ai]
            va, wa = items[a]
            for bi in range(ai + 1, len(pool_wt21)):
                b = pool_wt21[bi]
                vb, wb = items[b]
                room = capacity - total_wt + wa + wb
                lost = va + vb
                for j in pool_bf21:
                    vj, wj = items[j]
                    if wj <= room:
                        delta = vj - lost
                        if delta > best_delta:
                            best_delta = delta
                            best_move = ('21', a, b, j)

        if best_move and best_move[0] == '21':
            _, a, b, j = best_move
            taken.discard(a)
            taken.discard(b)
            taken.add(j)
            total_val += best_delta
            total_wt = total_wt - items[a][1] - items[b][1] + items[j][1]
            improved = True
            continue

        best_delta = 0
        best_move = None

        for a in pool_wt12:
            va, wa = items[a]
            room = capacity - total_wt + wa
            for pi in range(len(pool_bf12)):
                p = pool_bf12[pi]
                vp, wp = items[p]
                if wp > room:
                    continue
                for qi in range(pi + 1, len(pool_bf12)):
                    q = pool_bf12[qi]
                    vq, wq = items[q]
                    if wp + wq <= room:
                        delta = vp + vq - va
                        if delta > best_delta:
                            best_delta = delta
                            best_move = (a, p, q)

        if best_move:
            a, p, q = best_move
            taken.discard(a)
            taken.add(p)
            taken.add(q)
            total_val += best_delta
            total_wt = total_wt - items[a][1] + items[p][1] + items[q][1]
            improved = True

    return total_val


def main():
    data = sys.stdin.read().strip().split("\n")
    n, capacity = map(int, data[0].split())
    items = [tuple(map(int, line.split())) for line in data[1 : n + 1]]

    if capacity <= DP_CAPACITY_LIMIT:
        result = solve_dp(n, capacity, items)
    else:
        result = solve_bnb(n, capacity, items)

    ls_result = solve_local_search(n, capacity, items)
    result = max(result, ls_result)

    print(int(result))


main()
