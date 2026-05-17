import sys, math, random, heapq, time


def read_input():
    z = sys.stdin.read().split()
    if not z:
        return None
    p = 0
    n = int(z[p]); p += 1
    m = int(z[p]); p += 1
    sf, cp, fx, fy = [], [], [], []
    for i in range(n):
        sf.append(float(z[p])); cp.append(float(z[p + 1])); fx.append(float(z[p + 2])); fy.append(float(z[p + 3])); p += 4
    de, cx, cy = [], [], []
    for i in range(m):
        de.append(float(z[p])); cx.append(float(z[p + 1])); cy.append(float(z[p + 2])); p += 3
    return n, m, sf, cp, fx, fy, de, cx, cy


def objective(a, s, dd):
    u = [0] * len(s)
    r = 0.0
    for i, j in enumerate(a):
        r += dd[i][j]
        if not u[j]:
            u[j] = 1
            r += s[j]
    return r


def state(a, n, cp, de):
    r = cp[:]
    q = [0] * n
    for i, j in enumerate(a):
        r[j] -= de[i]
        q[j] += 1
    return r, q


def fallback(n, m, cp, de, dd):
    r = cp[:]
    a = [-1] * m
    for i in sorted(range(m), key=lambda x: -de[x]):
        b = -1
        bv = 10 ** 99
        for j in range(n):
            if r[j] + 1e-9 >= de[i] and dd[i][j] < bv:
                b = j
                bv = dd[i][j]
        if b < 0:
            return None
        a[i] = b
        r[b] -= de[i]
    return a


def build_greedy(o, n, m, s, cp, de, dd, near):
    r = cp[:]
    q = [0] * n
    a = [-1] * m
    av = sum(de) / max(1, m)
    pp = [max(1.0, min(float(m), cp[i] / max(av, 1e-9))) for i in range(n)]
    for i in o:
        b = -1
        bv = 10 ** 99
        for rr in (near[i], range(n)):
            for j in rr:
                if r[j] + 1e-9 < de[i]:
                    continue
                v = dd[i][j] + (0 if q[j] else s[j] / pp[j]) + 0.03 * (cp[j] - r[j]) / max(cp[j], 1e-9)
                if v < bv:
                    bv = v
                    b = j
            if b >= 0:
                break
        if b < 0:
            return None
        a[i] = b
        r[b] -= de[i]
        q[b] += 1
    return a


def improve_moves(a, n, m, s, cp, de, dd, near, passes=2):
    r, q = state(a, n, cp, de)
    for t in range(passes):
        ok = 0
        for i in sorted(range(m), key=lambda x: -de[x]):
            x = a[i]
            b = x
            bv = -1e-9
            pools = [near[i]]
            if n <= 500:
                pools.append(range(n))
            for rr in pools:
                for j in rr:
                    if j == x or r[j] + 1e-9 < de[i]:
                        continue
                    v = dd[i][j] - dd[i][x]
                    if q[x] == 1:
                        v -= s[x]
                    if q[j] == 0:
                        v += s[j]
                    if v < bv:
                        bv = v
                        b = j
            if b != x:
                r[x] += de[i]
                q[x] -= 1
                a[i] = b
                r[b] -= de[i]
                q[b] += 1
                ok = 1
        if not ok:
            break
    return a


def try_close(a, n, m, s, cp, de, dd, near):
    r, q = state(a, n, cp, de)
    fs = [i for i in range(n) if q[i]]
    fs.sort(key=lambda x: (q[x], -s[x] / max(1, q[x])))
    for f in fs[:80 if n * m > 200000 else len(fs)]:
        if q[f] == 0:
            continue
        olda = a[:]
        oldr = r[:]
        oldq = q[:]
        oldv = objective(a, s, dd)
        cc = [i for i in range(m) if a[i] == f]
        r[f] += sum(de[i] for i in cc)
        q[f] = 0
        good = 1
        for i in sorted(cc, key=lambda x: -de[x]):
            cand = [j for j in range(n) if q[j] and j != f]
            for j in near[i]:
                if j != f and j not in cand:
                    cand.append(j)
            if n <= 500:
                for j in range(n):
                    if j != f and j not in cand:
                        cand.append(j)
            b = -1
            bv = 10 ** 99
            for j in cand:
                if r[j] + 1e-9 >= de[i]:
                    v = dd[i][j] + (0 if q[j] else s[j])
                    if v < bv:
                        bv = v
                        b = j
            if b < 0:
                good = 0
                break
            a[i] = b
            r[b] -= de[i]
            q[b] += 1
        if not good or objective(a, s, dd) + 1e-9 >= oldv:
            a[:] = olda
            r[:] = oldr
            q[:] = oldq
    return a


def swap_moves(a, n, m, s, cp, de, dd, near):
    r, q = state(a, n, cp, de)
    fac_cust = [[] for _ in range(n)]
    for i in range(m):
        fac_cust[a[i]].append(i)
    improved = True
    while improved:
        improved = False
        for i in range(m):
            fi = a[i]
            for fj in near[i]:
                if fj == fi:
                    continue
                for c2 in fac_cust[fj]:
                    if c2 == i:
                        continue
                    ri_new = r[fi] + de[i] - de[c2]
                    rj_new = r[fj] + de[c2] - de[i]
                    if ri_new + 1e-9 < 0 or rj_new + 1e-9 < 0:
                        continue
                    gain = (dd[i][fi] + dd[c2][fj]) - (dd[i][fj] + dd[c2][fi])
                    if gain > 1e-9:
                        fac_cust[fi].remove(i)
                        fac_cust[fj].remove(c2)
                        a[i] = fj
                        a[c2] = fi
                        fac_cust[fj].append(i)
                        fac_cust[fi].append(c2)
                        r[fi] = ri_new
                        r[fj] = rj_new
                        improved = True
                        break
                if improved:
                    break
            if improved:
                break
    return a


def try_swap_fac(a, n, m, s, cp, de, dd, near):
    r, q = state(a, n, cp, de)
    improved = True
    while improved:
        improved = False
        opened = [j for j in range(n) if q[j] > 0]
        closed = [j for j in range(n) if q[j] == 0]
        if not closed:
            break
        for fo in opened:
            if q[fo] == 0:
                continue
            custs = [i for i in range(m) if a[i] == fo]
            for fn in closed:
                if q[fn] > 0:
                    continue
                need = sum(de[i] for i in custs)
                if cp[fn] + 1e-9 < need:
                    continue
                gain = s[fo] - s[fn]
                for i in custs:
                    gain += dd[i][fo] - dd[i][fn]
                if gain > 1e-9:
                    for i in custs:
                        a[i] = fn
                    r[fo] += need
                    q[fo] = 0
                    r[fn] -= need
                    q[fn] = len(custs)
                    improved = True
                    break
            if improved:
                break
    improved2 = True
    while improved2:
        improved2 = False
        closed = [j for j in range(n) if q[j] == 0]
        best_gain = 1e-9
        best_move = None
        for fn in closed:
            gains = []
            for i in range(m):
                old = a[i]
                save = dd[i][old] - dd[i][fn]
                if save > 0:
                    gains.append((save, i))
            if not gains:
                continue
            gains.sort(reverse=True)
            total_gain = -s[fn]
            cap_left = cp[fn]
            to_move = []
            for save, i in gains:
                if cap_left + 1e-9 < de[i]:
                    continue
                old = a[i]
                bonus = s[old] if q[old] == 1 else 0
                marginal = save + bonus
                if marginal <= 0 and total_gain + marginal <= 0:
                    continue
                total_gain += marginal
                cap_left -= de[i]
                to_move.append(i)
            if total_gain > best_gain and to_move:
                best_gain = total_gain
                best_move = (fn, to_move[:])
        if best_move:
            fn, to_move = best_move
            for i in to_move:
                old = a[i]
                r[old] += de[i]
                q[old] -= 1
                a[i] = fn
                r[fn] -= de[i]
                q[fn] += 1
            improved2 = True
    return a


def full_local_search(a, n, m, s, cp, de, dd, near):
    """Apply the full local search pipeline."""
    a = improve_moves(a, n, m, s, cp, de, dd, near, 3)
    a = try_close(a, n, m, s, cp, de, dd, near)
    a = swap_moves(a, n, m, s, cp, de, dd, near)
    a = try_swap_fac(a, n, m, s, cp, de, dd, near)
    a = improve_moves(a, n, m, s, cp, de, dd, near, 2)
    return a


def main():
    x = read_input()
    if x is None:
        return
    n, m, s, cp, fx, fy, de, cx, cy = x
    rnd = random.Random(42)
    t0_time = time.time()
    deadline = t0_time + 165
    dd = [[math.hypot(cx[i] - fx[j], cy[i] - fy[j]) for j in range(n)] for i in range(m)]
    k = min(50, n)
    near = [heapq.nsmallest(k, range(n), key=lambda j, ii=i: dd[ii][j]) for i in range(m)]

    avd = [sum(dd[i][j] for j in near[i]) / max(1, len(near[i])) for i in range(m)]
    fit = [sum(1 for j in range(n) if cp[j] + 1e-9 >= de[i]) for i in range(m)]
    oo = [
        sorted(range(m), key=lambda i: -de[i]),
        sorted(range(m), key=lambda i: fit[i]),
        sorted(range(m), key=lambda i: -de[i] / max(avd[i], 1e-9)),
    ]
    for t in range(8 if n * m < 200000 else 3):
        o = list(range(m))
        rnd.shuffle(o)
        o.sort(key=lambda i: -de[i] * (0.4 + rnd.random()))
        oo.append(o)
    ba = None
    bv = 10 ** 99
    for o in oo:
        a = build_greedy(o, n, m, s, cp, de, dd, near)
        if a is None:
            a = fallback(n, m, cp, de, dd)
        if a is None:
            continue
        a = full_local_search(a, n, m, s, cp, de, dd, near)
        v = objective(a, s, dd)
        if v < bv:
            bv = v
            ba = a[:]

    if ba is None:
        ba = fallback(n, m, cp, de, dd)
        bv = objective(ba, s, dd)

    init_time = time.time()


    a = ba[:]
    r, q = state(a, n, cp, de)
    cur_v = bv
    nk = len(near[0])

    deltas = []
    for _ in range(min(2000, m * 5)):
        i = rnd.randrange(m)
        old_f = a[i]
        new_f = near[i][rnd.randrange(nk)]
        if new_f == old_f:
            continue
        if r[new_f] + 1e-9 < de[i]:
            continue
        delta = dd[i][new_f] - dd[i][old_f]
        if q[old_f] == 1:
            delta -= s[old_f]
        if q[new_f] == 0:
            delta += s[new_f]
        if delta > 0:
            deltas.append(delta)
    if deltas:
        deltas.sort()

        median_delta = deltas[len(deltas) // 2]
        t0_temp = median_delta / math.log(1.0 / 0.4)  # exp(-d/T) = 0.4 => T = d / ln(2.5)
    else:
        avg_dd = sum(dd[i][a[i]] for i in range(m)) / m
        t0_temp = avg_dd * 0.1

    total_sa_time = deadline - init_time - 8 
    if total_sa_time < 5:
        total_sa_time = 5
    est_steps_per_sec = 1_500_000
    est_total_steps = int(est_steps_per_sec * total_sa_time)
    reheat_interval = max(m * 200, 500_000)
    steps_to_cool = reheat_interval
    alpha = (0.01) ** (1.0 / steps_to_cool)  # T * alpha^steps = 0.01*T
    min_temp = t0_temp * 1e-8

    time_check = 5000
    temp = t0_temp
    step = 0
    drift_fix_interval = max(reheat_interval // 2, 200_000)

    fac_c = [set() for _ in range(n)]
    for i in range(m):
        fac_c[a[i]].add(i)

    fac_near = []
    for j in range(n):
        dists = [(math.hypot(fx[j] - fx[j2], fy[j] - fy[j2]), j2) for j2 in range(n) if j2 != j]
        dists.sort()
        fac_near.append([j2 for _, j2 in dists[:min(20, n - 1)]])

    sa_start = time.time()

    while True:
        step += 1

        if step % time_check == 0:
            if time.time() >= sa_start + total_sa_time:
                break

        if step % drift_fix_interval == 0:
            real_v = objective(a, s, dd)
            if real_v < bv:
                bv = real_v
                ba = a[:]
            cur_v = real_v

        rv = rnd.random()
        if rv < 0.55:
            i = rnd.randrange(m)
            old_f = a[i]
            if rnd.random() < 0.85:
                new_f = near[i][rnd.randrange(nk)]
            else:
                new_f = rnd.randrange(n)
            if new_f == old_f:
                continue
            if r[new_f] + 1e-9 < de[i]:
                continue
            delta = dd[i][new_f] - dd[i][old_f]
            if q[old_f] == 1:
                delta -= s[old_f]
            if q[new_f] == 0:
                delta += s[new_f]
            if delta < 0 or (temp > min_temp and rnd.random() < math.exp(-delta / temp)):
                r[old_f] += de[i]
                q[old_f] -= 1
                fac_c[old_f].discard(i)
                a[i] = new_f
                r[new_f] -= de[i]
                q[new_f] += 1
                fac_c[new_f].add(i)
                cur_v += delta
                if cur_v < bv:
                    real_v = objective(a, s, dd)
                    if real_v < bv:
                        bv = real_v
                        ba = a[:]
                    cur_v = real_v

        elif rv < 0.85:
            i1 = rnd.randrange(m)
            i2 = rnd.randrange(m)
            f1 = a[i1]
            f2 = a[i2]
            if f1 == f2:
                continue
            r1_new = r[f1] + de[i1] - de[i2]
            r2_new = r[f2] + de[i2] - de[i1]
            if r1_new + 1e-9 < 0 or r2_new + 1e-9 < 0:
                continue
            delta = (dd[i1][f2] + dd[i2][f1]) - (dd[i1][f1] + dd[i2][f2])
            if delta < 0 or (temp > min_temp and rnd.random() < math.exp(-delta / temp)):
                fac_c[f1].discard(i1)
                fac_c[f2].discard(i2)
                a[i1] = f2
                a[i2] = f1
                fac_c[f2].add(i1)
                fac_c[f1].add(i2)
                r[f1] = r1_new
                r[f2] = r2_new
                cur_v += delta
                if cur_v < bv:
                    real_v = objective(a, s, dd)
                    if real_v < bv:
                        bv = real_v
                        ba = a[:]
                    cur_v = real_v

        elif rv < 0.95:
            opened = [j for j in range(n) if q[j] > 0]
            if len(opened) <= 1:
                continue
            f = rnd.choice(opened)
            custs = list(fac_c[f])
            if not custs:
                continue
            new_assign = {}
            total_delta = -s[f]
            temp_r = r[:]
            temp_r[f] += sum(de[ci] for ci in custs)
            feasible = True
            for ci in sorted(custs, key=lambda x: -de[x]):
                best_j = -1
                best_cost = 10 ** 99
                for j in near[ci]:
                    if j == f:
                        continue
                    if temp_r[j] + 1e-9 >= de[ci]:
                        cost = dd[ci][j] + (0 if q[j] > 0 or j in new_assign else s[j])
                        if cost < best_cost:
                            best_cost = cost
                            best_j = j
                if best_j < 0:
                    feasible = False
                    break
                new_assign[ci] = best_j
                total_delta += dd[ci][best_j] - dd[ci][f]
                if q[best_j] == 0 and best_j not in {new_assign[c] for c in new_assign if c != ci}:
                    total_delta += s[best_j]
                temp_r[best_j] -= de[ci]
            if not feasible:
                continue
            delta = -s[f]
            for ci in custs:
                delta += dd[ci][new_assign[ci]] - dd[ci][f]
            new_facs_opened = set()
            for ci in custs:
                nf = new_assign[ci]
                if q[nf] == 0 and nf not in new_facs_opened:
                    delta += s[nf]
                    new_facs_opened.add(nf)
            if delta < 0 or (temp > min_temp and rnd.random() < math.exp(-delta / temp)):
                for ci in custs:
                    nf = new_assign[ci]
                    r[f] += de[ci]
                    q[f] -= 1
                    fac_c[f].discard(ci)
                    a[ci] = nf
                    r[nf] -= de[ci]
                    q[nf] += 1
                    fac_c[nf].add(ci)
                cur_v += delta
                if cur_v < bv:
                    real_v = objective(a, s, dd)
                    if real_v < bv:
                        bv = real_v
                        ba = a[:]
                    cur_v = real_v
        else:
            closed = [j for j in range(n) if q[j] == 0]
            if not closed:
                continue
            fn = rnd.choice(closed)
            candidates = []
            for i in range(m):
                save = dd[i][a[i]] - dd[i][fn]
                if save > 0:
                    candidates.append((save, i))
            if not candidates:
                continue
            candidates.sort(reverse=True)
            delta = s[fn]
            cap_left = cp[fn]
            to_move = []
            for save, i in candidates:
                if cap_left + 1e-9 < de[i]:
                    continue
                old = a[i]
                bonus = s[old] if q[old] == 1 else 0
                marginal = -save - bonus
                if len(to_move) == 0 or delta + marginal < delta * 1.5:
                    delta += marginal
                    cap_left -= de[i]
                    to_move.append(i)
                if cap_left < 1e-9:
                    break
            if not to_move:
                continue
            delta = s[fn]
            closing_facs = set()
            for i in to_move:
                old = a[i]
                delta -= dd[i][old] - dd[i][fn]
                if q[old] == 1 and old not in closing_facs:
                    others_moving = sum(1 for i2 in to_move if a[i2] == old and i2 != i)
                    if q[old] - 1 - others_moving <= 0:
                        pass
            delta = s[fn]
            fac_loss = {}
            for i in to_move:
                old = a[i]
                delta += dd[i][fn] - dd[i][old]
                fac_loss[old] = fac_loss.get(old, 0) + 1
            for old, cnt in fac_loss.items():
                if q[old] == cnt:
                    delta -= s[old]
            if delta < 0 or (temp > min_temp and rnd.random() < math.exp(-delta / temp)):
                for i in to_move:
                    old = a[i]
                    r[old] += de[i]
                    q[old] -= 1
                    fac_c[old].discard(i)
                    a[i] = fn
                    r[fn] -= de[i]
                    q[fn] += 1
                    fac_c[fn].add(i)
                cur_v += delta
                if cur_v < bv:
                    real_v = objective(a, s, dd)
                    if real_v < bv:
                        bv = real_v
                        ba = a[:]
                    cur_v = real_v

        temp *= alpha
        if temp < min_temp:
            temp = min_temp

        if step % reheat_interval == 0:
            remaining = sa_start + total_sa_time - time.time()
            if remaining <= 0:
                break
            if cur_v < bv * 1.01:
                a2 = a[:]
                a2 = improve_moves(a2, n, m, s, cp, de, dd, near, 2)
                v2 = objective(a2, s, dd)
                if v2 < bv:
                    bv = v2
                    ba = a2[:]

            a = ba[:]
            r, q = state(a, n, cp, de)
            cur_v = bv
            fac_c = [set() for _ in range(n)]
            for i in range(m):
                fac_c[a[i]].add(i)
            cands = list(range(m))
            rnd.shuffle(cands)
            cnt = max(3, m // 15)
            for ci in cands[:cnt]:
                old_f = a[ci]
                new_f = near[ci][rnd.randrange(nk)]
                if new_f != old_f and r[new_f] + 1e-9 >= de[ci]:
                    r[old_f] += de[ci]
                    q[old_f] -= 1
                    fac_c[old_f].discard(ci)
                    a[ci] = new_f
                    r[new_f] -= de[ci]
                    q[new_f] += 1
                    fac_c[new_f].add(ci)
            cur_v = objective(a, s, dd)

            frac = remaining / total_sa_time
            temp = t0_temp * max(frac, 0.1) * 0.5

    ba = improve_moves(ba, n, m, s, cp, de, dd, near, 5)
    ba = try_close(ba, n, m, s, cp, de, dd, near)
    ba = swap_moves(ba, n, m, s, cp, de, dd, near)
    ba = try_swap_fac(ba, n, m, s, cp, de, dd, near)
    ba = improve_moves(ba, n, m, s, cp, de, dd, near, 3)
    bv = objective(ba, s, dd)
    print('%.6f' % bv)
    print(' '.join(str(int(x)) for x in ba))


if __name__ == '__main__':
    main()
