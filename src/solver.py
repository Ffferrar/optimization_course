import sys
import math
import random
import time
import argparse

from parser import parse_file

MAX_STARTS = 8
LARGE_N = 5000
BRIDGE_MIN_N = 200
MAX_SEG = 500

T0_SMALL = 0.005
T0_MED = 0.003
T0_LARGE = 0.002
ALPHA = 0.999995
ALPHA_LARGE = 0.999999

REHEAT_FACTOR = 200
REHEAT_MIN = 500000
REHEAT_TEMP_FRAC = 0.3

TIME_CHECK_INTERVAL = 5000
MIN_TEMP = 1e-12


def _nn_tour(n, dist, start):
    visited = [False] * n
    tour = [start]
    visited[start] = True
    for _ in range(n - 1):
        cur = tour[-1]
        best_d = float('inf')
        best_c = -1
        for c in range(n):
            if not visited[c]:
                dd = dist(cur, c)
                if dd < best_d:
                    best_d = dd
                    best_c = c
        tour.append(best_c)
        visited[best_c] = True
    return tour


def _two_opt_pass(tour, n, d, deadline):
    improved = True
    while improved:
        improved = False
        for i in range(n - 1):
            if time.time() >= deadline:
                return
            for j in range(i + 2, n):
                if i == 0 and j == n - 1:
                    continue
                a, b = tour[i], tour[i + 1]
                c, e = tour[j], tour[(j + 1) % n]
                delta = (d(a, c) + d(b, e)) - (d(a, b) + d(c, e))
                if delta < -1e-10:
                    tour[i + 1:j + 1] = tour[i + 1:j + 1][::-1]
                    improved = True


def solve(n, coords, seed, time_limit):
    random.seed(seed)
    deadline = time.time() + time_limit
    if n <= LARGE_N:
        dm = [[0.0] * n for _ in range(n)]
        for i in range(n):
            xi, yi = coords[i]
            for j in range(i + 1, n):
                xj, yj = coords[j]
                v = math.sqrt((xi - xj) ** 2 + (yi - yj) ** 2)
                dm[i][j] = v
                dm[j][i] = v

        def d(a, b):
            return dm[a][b]
    else:
        def d(a, b):
            dx = coords[a][0] - coords[b][0]
            dy = coords[a][1] - coords[b][1]
            return math.sqrt(dx * dx + dy * dy)

    def length(t):
        s = 0.0
        for i in range(n):
            s += d(t[i], t[(i + 1) % n])
        return s
    num_starts = min(MAX_STARTS, max(1, int(time_limit / 2)))
    best_tour = None
    best_cost = float('inf')
    nn_starts = min(num_starts, n)
    start_cities = random.sample(range(n), nn_starts)
    for sc in start_cities:
        if time.time() >= deadline:
            break
        t = _nn_tour(n, d, sc)
        c = length(t)
        if c < best_cost:
            best_cost = c
            best_tour = t[:]

    opt_deadline = time.time() + time_limit / 3
    if n <= 2000 and time.time() < deadline:
        _two_opt_pass(best_tour, n, d, min(opt_deadline, deadline))
        best_cost = length(best_tour)

    tour = best_tour[:]
    cost = best_cost

    if n <= 100:
        t0 = best_cost * T0_SMALL
    elif n <= 1000:
        t0 = best_cost * T0_MED
    else:
        t0 = best_cost * T0_LARGE

    temp = t0
    alpha = ALPHA_LARGE if n > LARGE_N else ALPHA

    step = 0
    reheat_interval = max(n * REHEAT_FACTOR, REHEAT_MIN)

    while True:
        if step % TIME_CHECK_INTERVAL == 0:
            if time.time() >= deadline:
                break

        if n <= 150 and random.random() < 0.3:
            i = random.randint(0, n - 1)
            j = random.randint(0, n - 2)
            if j >= i:
                j += 1
            pi = (i - 1) % n
            ni = (i + 1) % n
            city = tour[i]
            prev_c = tour[pi]
            next_c = tour[ni]
            jn = (j + 1) % n
            after_c = tour[j]
            after_next = tour[jn]

            old = d(prev_c, city) + d(city, next_c) + d(after_c, after_next)
            new = d(prev_c, next_c) + d(after_c, city) + d(city, after_next)
            delta = new - old

            if delta < 0 or (temp > MIN_TEMP and random.random() < math.exp(-delta / temp)):
                tour.pop(i)
                ins = j if j < i else j - 1
                tour.insert(ins + 1, city)
                cost += delta
        else:
            if n > MAX_SEG:
                i = random.randint(0, n - 1)
                j = i + random.randint(2, MAX_SEG)
                if j >= n:
                    j -= n
                if i > j:
                    i, j = j, i
            else:
                i = random.randint(0, n - 1)
                j = random.randint(0, n - 1)
                if i == j:
                    step += 1
                    continue
                if i > j:
                    i, j = j, i
            if j - i <= 1 or (i == 0 and j == n - 1):
                step += 1
                continue

            a, b = tour[i], tour[(i - 1) % n]
            c, e = tour[j], tour[(j + 1) % n]
            delta = (d(b, c) + d(a, e)) - (d(b, a) + d(c, e))

            if delta < 0:
                tour[i:j + 1] = tour[i:j + 1][::-1]
                cost += delta
            elif temp > MIN_TEMP:
                if random.random() < math.exp(-delta / temp):
                    tour[i:j + 1] = tour[i:j + 1][::-1]
                    cost += delta

        if cost < best_cost:
            best_cost = cost
            best_tour = tour[:]

        temp *= alpha

        if step > 0 and step % reheat_interval == 0 and n >= BRIDGE_MIN_N:
            cuts = sorted(random.sample(range(1, n), 3))
            a, b, c = cuts
            tour = best_tour[:a] + best_tour[b:c] + best_tour[a:b] + best_tour[c:]
            cost = length(tour)
            remaining = deadline - time.time()
            if remaining > 0:
                temp = t0 * (remaining / time_limit) * REHEAT_TEMP_FRAC
            else:
                break

        step += 1

    return best_tour, best_cost


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('instance')
    ap.add_argument('--seed', type=int, default=42)
    ap.add_argument('--time-limit-sec', type=float, default=60.0)
    args = ap.parse_args()

    n, coords = parse_file(args.instance)
    tour, cost = solve(n, coords, args.seed, args.time_limit_sec)
    print(' '.join(map(str, tour)))


if __name__ == '__main__':
    main()
