import sys
import math
import random
import time
import argparse

from parser import parse_file

TOP_K = 5
FULL_MULTISTART_N = 600
MULTISTART_MED = 150
MULTISTART_LARGE = 32
MULTISTART_XLARGE = 8

LOCAL_SEARCH_EXHAUSTIVE_MAX_N = 200
TWO_OPT_MAX_EXHAUSTIVE_PASSES = 50_000
THREE_OPT_MAX_EXHAUSTIVE_PASSES = 50_000
TWO_OPT_RANDOM_ROUNDS = 64
TWO_OPT_SAMPLES_PER_ROUND = 200_000
THREE_OPT_RANDOM_ROUNDS = 64
THREE_OPT_SAMPLES_PER_ROUND = 200_000

SA_T0_FRAC = 0.002
SA_ALPHA = 0.999997
SA_MIN_TEMP = 1e-12
SA_TIME_CHECK = 5000
SA_MAX_SEG = 500


def _make_dist_fn(n, coords):
    if n <= 5000:
        dm = [[0.0] * n for _ in range(n)]
        for i in range(n):
            xi, yi = coords[i]
            for j in range(i + 1, n):
                xj, yj = coords[j]
                v = math.hypot(xi - xj, yi - yj)
                dm[i][j] = v
                dm[j][i] = v
        def d(a, b):
            return dm[a][b]
        return d
    else:
        cx = [c[0] for c in coords]
        cy = [c[1] for c in coords]
        def d(a, b):
            return math.hypot(cx[a] - cx[b], cy[a] - cy[b])
        return d


def _tour_length(tour, n, d):
    s = d(tour[n - 1], tour[0])
    for i in range(n - 1):
        s += d(tour[i], tour[i + 1])
    return s


def _min_gain(tour_len):
    return max(1e-9, 1e-12 * tour_len)


def _nn_tour(n, d, start):
    visited = [False] * n
    tour = [0] * n
    tour[0] = start
    visited[start] = True
    cur = start
    for step in range(1, n):
        best_d = float('inf')
        best_c = -1
        for j in range(n):
            if not visited[j]:
                dd = d(cur, j)
                if dd < best_d:
                    best_d = dd
                    best_c = j
        tour[step] = best_c
        visited[best_c] = True
        cur = best_c
    return tour


def _multistart_count(n):
    if n <= FULL_MULTISTART_N:
        return n
    if n <= 2000:
        return min(n, MULTISTART_MED)
    if n <= 12000:
        return min(n, MULTISTART_LARGE)
    return min(n, MULTISTART_XLARGE)


def _start_vertex(n, num_starts, idx):
    if num_starts >= n:
        return idx
    if num_starts <= 1:
        return 0
    return int(idx * (n - 1) // (num_starts - 1))


def _insert_top(top_tours, top_lens, top_count, k, tour, length):
    if top_count < k:
        top_tours[top_count] = tour[:]
        top_lens[top_count] = length
        return top_count + 1
    worst = 0
    for i in range(1, k):
        if top_lens[i] > top_lens[worst]:
            worst = i
    if length < top_lens[worst]:
        top_tours[worst] = tour[:]
        top_lens[worst] = length
    return k


def _reverse_seg(arr, lo, hi):
    while lo < hi:
        arr[lo], arr[hi] = arr[hi], arr[lo]
        lo += 1
        hi -= 1


def _apply_two_opt(tour, n, i, j):
    work = [tour[(i + p) % n] for p in range(n)]
    _reverse_seg(work, 1, j - i)
    for p in range(n):
        tour[(i + p) % n] = work[p]


def _two_opt_exhaustive(tour, n, d, deadline):
    tl = _tour_length(tour, n, d)
    mg = _min_gain(tl)
    dup = tour + tour

    best_delta = 0.0
    best_i = -1
    best_j = -1

    for i in range(n):
        if i % 100 == 0 and time.time() >= deadline:
            return False
        a = dup[i]
        b = dup[i + 1]
        for j in range(i + 2, i + n - 1):
            c = dup[j]
            e = dup[j + 1]
            delta = (d(a, c) + d(b, e)) - (d(a, b) + d(c, e))
            if delta < -mg and delta < best_delta - 1e-15:
                best_delta = delta
                best_i = i
                best_j = j

    if best_i < 0 or best_delta >= -mg:
        return False

    backup = tour[:]
    _apply_two_opt(tour, n, best_i, best_j)
    if _tour_length(tour, n, d) >= tl - mg:
        tour[:] = backup
        return False
    return True


def _two_opt_random(tour, n, d, rng, samples, deadline):
    tl = _tour_length(tour, n, d)
    mg = _min_gain(tl)

    for s in range(samples):
        if s % 20000 == 0 and time.time() >= deadline:
            return False
        i = rng.randint(0, n - 1)
        gap = max(1, n - 4)
        j = i + 2 + rng.randint(0, gap - 1)
        if j > i + n - 2:
            continue

        a = tour[i % n]
        b = tour[(i + 1) % n]
        c = tour[j % n]
        e = tour[(j + 1) % n]
        delta = (d(a, c) + d(b, e)) - (d(a, b) + d(c, e))
        if delta >= -mg:
            continue

        backup = tour[:]
        _apply_two_opt(tour, n, i, j)
        if _tour_length(tour, n, d) < tl - mg:
            return True
        tour[:] = backup
    return False


def _two_opt(tour, n, d, deadline):
    if n < 4:
        return
    if n <= LOCAL_SEARCH_EXHAUSTIVE_MAX_N:
        for _ in range(TWO_OPT_MAX_EXHAUSTIVE_PASSES):
            if time.time() >= deadline:
                break
            if not _two_opt_exhaustive(tour, n, d, deadline):
                break
    else:
        rng = random.Random(131313)
        for _ in range(TWO_OPT_RANDOM_ROUNDS):
            if time.time() >= deadline:
                break
            if not _two_opt_random(tour, n, d, rng, TWO_OPT_SAMPLES_PER_ROUND, deadline):
                break


def _apply_three_opt(tour, n, i, j, k, case_id):
    work = [tour[(i + p) % n] for p in range(n)]
    pj = j - i
    pk = k - i

    if case_id == 2:
        _reverse_seg(work, 1, pj)
    elif case_id == 3:
        _reverse_seg(work, pj + 1, pk)
    elif case_id == 4:
        _reverse_seg(work, 1, pk)
    elif case_id == 5:
        _reverse_seg(work, 1, pj)
        _reverse_seg(work, pj + 1, pk)
    elif case_id == 6:
        _reverse_seg(work, pj + 1, pk)
        _reverse_seg(work, 1, pk)
    elif case_id == 7:
        _reverse_seg(work, pj + 1, pk)
        _reverse_seg(work, 1, pj)

    for p in range(n):
        tour[(i + p) % n] = work[p]


def _three_opt_exhaustive(tour, n, d, deadline):
    tl = _tour_length(tour, n, d)
    mg = _min_gain(tl)
    dup = tour + tour

    best_delta = 0.0
    best_i = -1
    best_j = -1
    best_k = -1
    best_case = -1

    for i in range(n):
        if time.time() >= deadline:
            break
        a = dup[i]
        b = dup[i + 1]
        for j in range(i + 2, i + n - 1):
            c = dup[j]
            dd = dup[j + 1]
            for k in range(j + 2, i + n - 1):
                e = dup[k]
                f = dup[k + 1]

                d0 = d(a, b) + d(c, dd) + d(e, f)
                g2 = d(a, c) + d(b, dd) + d(e, f) - d0
                g3 = d(a, b) + d(c, e) + d(dd, f) - d0
                g4 = d(a, dd) + d(e, b) + d(c, f) - d0
                g5 = d(a, e) + d(c, b) + d(dd, f) - d0
                g6 = d(a, dd) + d(e, c) + d(b, f) - d0
                g7 = d(a, e) + d(dd, b) + d(c, f) - d0

                for g, cid in ((g2, 2), (g3, 3), (g4, 4),
                                (g5, 5), (g6, 6), (g7, 7)):
                    if g < -mg and g < best_delta - 1e-15:
                        best_delta = g
                        best_i = i
                        best_j = j
                        best_k = k
                        best_case = cid

    if best_case < 0 or best_delta >= -mg:
        return False

    backup = tour[:]
    _apply_three_opt(tour, n, best_i, best_j, best_k, best_case)
    if _tour_length(tour, n, d) >= tl - mg:
        tour[:] = backup
        return False
    return True


def _three_opt_random(tour, n, d, rng, samples, deadline):
    tl = _tour_length(tour, n, d)
    mg = _min_gain(tl)

    for s in range(samples):
        if s % 10000 == 0 and time.time() >= deadline:
            return False
        i = rng.randint(0, n - 1)
        gap = max(1, n - 4)
        j = i + 2 + rng.randint(0, gap - 1)
        max_k = i + n - 2
        if j + 2 > max_k:
            continue
        k = j + 2 + rng.randint(0, max_k - (j + 2))

        a = tour[i % n]
        b = tour[(i + 1) % n]
        c = tour[j % n]
        dd = tour[(j + 1) % n]
        e = tour[k % n]
        f = tour[(k + 1) % n]

        d0 = d(a, b) + d(c, dd) + d(e, f)
        g2 = d(a, c) + d(b, dd) + d(e, f) - d0
        g3 = d(a, b) + d(c, e) + d(dd, f) - d0
        g4 = d(a, dd) + d(e, b) + d(c, f) - d0
        g5 = d(a, e) + d(c, b) + d(dd, f) - d0
        g6 = d(a, dd) + d(e, c) + d(b, f) - d0
        g7 = d(a, e) + d(dd, b) + d(c, f) - d0

        best_case = -1
        best_g = 0.0
        for g, cid in ((g2, 2), (g3, 3), (g4, 4),
                        (g5, 5), (g6, 6), (g7, 7)):
            if g < -mg and g < best_g - 1e-15:
                best_g = g
                best_case = cid

        if best_case >= 0:
            backup = tour[:]
            _apply_three_opt(tour, n, i, j, k, best_case)
            if _tour_length(tour, n, d) < tl - mg:
                return True
            tour[:] = backup
    return False


def _three_opt(tour, n, d, deadline):
    if n < 6:
        return
    if n <= LOCAL_SEARCH_EXHAUSTIVE_MAX_N:
        for _ in range(THREE_OPT_MAX_EXHAUSTIVE_PASSES):
            if time.time() >= deadline:
                break
            if not _three_opt_exhaustive(tour, n, d, deadline):
                break
    else:
        rng = random.Random(424242)
        for _ in range(THREE_OPT_RANDOM_ROUNDS):
            if time.time() >= deadline:
                break
            if not _three_opt_random(tour, n, d, rng, THREE_OPT_SAMPLES_PER_ROUND, deadline):
                break


def _local_search(tour, n, d, deadline):
    if n < 4:
        return
    _two_opt(tour, n, d, deadline)
    if time.time() < deadline:
        _three_opt(tour, n, d, deadline)
    if time.time() < deadline:
        _two_opt(tour, n, d, deadline)


def _sa_phase(tour, n, d, cost, deadline):
    best_tour = tour[:]
    best_cost = cost

    t0 = best_cost * SA_T0_FRAC
    temp = t0
    alpha = SA_ALPHA

    step = 0
    while True:
        if step % SA_TIME_CHECK == 0:
            if time.time() >= deadline:
                break

        if n > SA_MAX_SEG:
            i = random.randint(0, n - 1)
            j = i + random.randint(2, SA_MAX_SEG)
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
        elif temp > SA_MIN_TEMP:
            if random.random() < math.exp(-delta / temp):
                tour[i:j + 1] = tour[i:j + 1][::-1]
                cost += delta

        if cost < best_cost:
            best_cost = cost
            best_tour = tour[:]

        temp *= alpha
        step += 1

    return best_tour, best_cost


def solve(n, coords, seed, time_limit):
    random.seed(seed)
    deadline = time.time() + time_limit

    if n <= 1:
        return list(range(n)), 0.0

    d = _make_dist_fn(n, coords)

    nn_deadline = min(time.time() + time_limit * 0.3, deadline)
    num_starts = _multistart_count(n)
    top_tours = [None] * TOP_K
    top_lens = [0.0] * TOP_K
    top_count = 0

    for t in range(num_starts):
        if time.time() >= nn_deadline:
            break
        sv = _start_vertex(n, num_starts, t)
        tour = _nn_tour(n, d, sv)
        length = _tour_length(tour, n, d)
        top_count = _insert_top(top_tours, top_lens, top_count, TOP_K,
                                tour, length)

    if top_count == 0:
        tour = _nn_tour(n, d, 0)
        top_tours[0] = tour
        top_lens[0] = _tour_length(tour, n, d)
        top_count = 1

    best_tour = top_tours[0][:]
    best_len = top_lens[0]
    for i in range(top_count):
        if top_lens[i] < best_len:
            best_len = top_lens[i]
            best_tour = top_tours[i][:]

    ls_deadline = min(time.time() + time_limit * 0.4, deadline - 5)
    if ls_deadline > time.time() and top_count > 0:
        time_per_cand = (ls_deadline - time.time()) / top_count
        for k in range(top_count):
            if time.time() >= ls_deadline:
                break
            cand = top_tours[k][:]
            cand_deadline = min(time.time() + time_per_cand, ls_deadline)
            _local_search(cand, n, d, cand_deadline)
            cand_len = _tour_length(cand, n, d)
            if cand_len < best_len:
                best_len = cand_len
                best_tour = cand[:]

    remaining = deadline - time.time()
    if remaining > 3.0:
        extra_deadline = min(time.time() + remaining * 0.3, deadline - 2)
        _local_search(best_tour, n, d, extra_deadline)
        best_len = _tour_length(best_tour, n, d)

    remaining = deadline - time.time()
    if remaining > 1.0:
        best_tour, best_len = _sa_phase(best_tour, n, d, best_len, deadline - 0.5)

    return best_tour, best_len


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
