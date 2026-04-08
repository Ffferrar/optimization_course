import sys
import math
import random
import time
import argparse

from parser import parse_file

MAX_STARTS = 8
LARGE_N = 5000
BRIDGE_MIN_N = 200

T0_SMALL = 0.05
T0_MED = 0.02
T0_LARGE = 0.01
ALPHA = 0.95
ALPHA_LARGE = 0.99

REHEAT_FACTOR = 200
REHEAT_MIN = 500000
REHEAT_TEMP_FRAC = 0.2

TIME_CHECK_INTERVAL = 5000
MIN_TEMP = 1e-12


def solve(n, coords, seed, time_limit):
    random.seed(seed)
    deadline = time.time() + time_limit

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
    for _ in range(num_starts):
        t = list(range(n))
        random.shuffle(t)
        c = length(t)
        if c < best_cost:
            best_cost = c
            best_tour = t[:]

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

        i = random.randint(0, n - 1)
        j = random.randint(0, n - 1)
        if i == j:
            step += 1
            continue
        if i > j:
            i, j = j, i
        if j - i == 1 or (i == 0 and j == n - 1):
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
