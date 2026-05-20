import sys
import argparse

from parser import parse_file


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


def _reverse_delete(n, sets, costs, sol):
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


def solve(n, m, costs, sets):
    sol, tc = _greedy(n, m, sets, costs)
    sol, tc = _reverse_delete(n, sets, costs, sol)
    return sol, tc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('instance')
    args = ap.parse_args()

    n, m, costs, sets = parse_file(args.instance)
    sol, cost = solve(n, m, costs, sets)

    print(cost)
    print(' '.join(map(str, sol)))


if __name__ == '__main__':
    main()
