import sys
import math
import random
import time
import argparse

from parser import parse_file

MAX_STARTS = 3
LARGE_M = 5000

T0 = 1000.0
ALPHA = 0.999
ALPHA_LARGE = 0.9995

TIME_CHECK = 100
MIN_TEMP = 1e-3

K_SMALL = 3
K_LARGE = 2


def _greedy(n, m, sets, costs):
    unc = set(range(n))
    sol = []
    used = set()
    cov = [False] * n
    tc = 0

    while unc:
        bi = -1
        bc = 1
        bg = 0

        for i in range(m):
            if i in used:
                continue
            g = 0
            for e in sets[i]:
                if not cov[e]:
                    g += 1
            if g > 0:
                if bi == -1 or costs[i] * bg < bc * g:
                    bg = g
                    bc = costs[i]
                    bi = i

        if bi == -1:
            break

        sol.append(bi)
        used.add(bi)
        tc += costs[bi]
        for e in sets[bi]:
            if not cov[e]:
                cov[e] = True
                unc.discard(e)

    return sol, tc


def _trim(n, sets, costs, sol):
    sol.sort(key=lambda x: -costs[x])
    cnt = [0] * n
    for s in sol:
        for e in sets[s]:
            cnt[e] += 1

    ns = []
    for s in sol:
        red = True
        for e in sets[s]:
            if cnt[e] <= 1:
                red = False
                break
        if red:
            for e in sets[s]:
                cnt[e] -= 1
        else:
            ns.append(s)

    return ns, sum(costs[s] for s in ns)


def _repair(n, m, sets, costs, sol):
    ss = set(sol)
    cov = set()
    for s in sol:
        cov.update(sets[s])
    unc = set(range(n)) - cov

    if unc:
        adds = []
        for i in range(m):
            if i in ss:
                continue
            g = len(sets[i] & unc)
            if g > 0:
                adds.append((costs[i] / g, g, i))
        adds.sort()
        idx = 0
        while unc and idx < len(adds):
            s = adds[idx][2]
            sol.append(s)
            unc -= sets[s]
            idx += 1

    return _trim(n, sets, costs, sol)


def solve(n, m, costs, sets, seed, time_limit):
    random.seed(seed)
    deadline = time.time() + time_limit

    best_sol, best_cost = _greedy(n, m, sets, costs)
    best_sol, best_cost = _trim(n, sets, costs, best_sol)

    k = K_LARGE if m > LARGE_M else K_SMALL
    alpha = ALPHA_LARGE if m > LARGE_M else ALPHA

    ns = MAX_STARTS
    tps = (deadline - time.time()) / ns

    for _ in range(ns):
        if time.time() >= deadline:
            break

        sd = min(time.time() + tps, deadline)

        sol = list(best_sol)
        cost = best_cost
        temp = T0
        ni = 0
        step = 0

        while True:
            if step % TIME_CHECK == 0:
                if time.time() >= sd:
                    break

            cur = list(sol)
            l = len(cur)
            ss = set(cur)
            r = random.random()

            if r < 0.3 and l < m:
                att = 0
                while att < 20:
                    idx = random.randint(0, m - 1)
                    if idx not in ss:
                        cur.append(idx)
                        break
                    att += 1
            elif r < 0.5 and l > 1:
                pos = random.randint(0, l - 1)
                del cur[pos]
            elif r < 0.7 and 0 < l < m:
                pos = random.randint(0, l - 1)
                rem = cur[pos]
                att = 0
                while att < 20:
                    ns2 = random.randint(0, m - 1)
                    if ns2 != rem:
                        cur[pos] = ns2
                        break
                    att += 1
            elif l >= k and m - l >= k:
                tr = sorted(random.sample(range(l), k), reverse=True)
                for idx in tr:
                    del cur[idx]
                nss = set(cur)
                added = 0
                att = 0
                while added < k and att < k * 30:
                    c = random.randint(0, m - 1)
                    if c not in nss:
                        cur.append(c)
                        nss.add(c)
                        added += 1
                    att += 1

            nb, nc = _repair(n, m, sets, costs, cur)
            delta = nc - cost

            if delta < 0 or (temp > MIN_TEMP and random.random() < math.exp(-delta / temp)):
                sol = nb
                cost = nc
                if cost < best_cost:
                    best_cost = cost
                    best_sol = list(sol)
                ni = 0
            else:
                ni += 1

            if ni > 1000:
                temp = T0 * 0.5
                ni = 0
            else:
                temp *= alpha
                if temp < MIN_TEMP:
                    temp = T0

            step += 1

    return best_sol, best_cost


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('instance')
    ap.add_argument('--seed', type=int, default=42)
    ap.add_argument('--time-limit-sec', type=float, default=60.0)
    args = ap.parse_args()

    n, m, costs, sets = parse_file(args.instance)
    sol, cost = solve(n, m, costs, sets, args.seed, args.time_limit_sec)

    print(cost)
    print(' '.join(map(str, sol)))


if __name__ == '__main__':
    main()
