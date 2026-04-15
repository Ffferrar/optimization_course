import sys, math, random, heapq


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
            if n < 90:
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
    for f in fs[:60 if n * m > 200000 else len(fs)]:
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
            if n < 80:
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


def build_ant(n, m, s, cp, de, dd, near, ph, rnd):
    r = cp[:]
    q = [0] * n
    a = [-1] * m
    av = sum(de) / max(1, m)
    pp = [max(1.0, min(float(m), cp[i] / max(av, 1e-9))) for i in range(n)]
    o = list(range(m))
    o.sort(key=lambda x: -de[x] * (0.6 + rnd.random()))
    for i in o:
        vv = []
        for rr in (near[i], range(n)):
            vv = []
            for j in rr:
                if r[j] + 1e-9 >= de[i]:
                    e = 1.0 / (dd[i][j] + (0 if q[j] else s[j] / pp[j]) + 1e-9)
                    vv.append((j, ph.get((i, j), 1.0) * e ** 3))
            if vv:
                break
        if not vv:
            return None
        if rnd.random() < 0.25:
            b = max(vv, key=lambda x: x[1])[0]
        else:
            sm = sum(x[1] for x in vv)
            z = rnd.random() * sm
            y = 0.0
            b = vv[-1][0]
            for j, w in vv:
                y += w
                if y >= z:
                    b = j
                    break
        a[i] = b
        r[b] -= de[i]
        q[b] += 1
    return a


def main():
    x = read_input()
    if x is None:
        return
    n, m, s, cp, fx, fy, de, cx, cy = x
    rnd = random.Random(7)
    dd = [[math.hypot(cx[i] - fx[j], cy[i] - fy[j]) for j in range(n)] for i in range(m)]
    k = min(30, n)
    near = [heapq.nsmallest(k, range(n), key=lambda j: dd[i][j]) for i in range(m)]
    avd = [sum(dd[i][j] for j in near[i]) / max(1, len(near[i])) for i in range(m)]
    fit = [sum(1 for j in range(n) if cp[j] + 1e-9 >= de[i]) for i in range(m)]
    oo = [sorted(range(m), key=lambda i: -de[i]), sorted(range(m), key=lambda i: fit[i]), sorted(range(m), key=lambda i: -de[i] / max(avd[i], 1e-9))]
    for t in range(6 if n * m < 200000 else 2):
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
        a = improve_moves(a, n, m, s, cp, de, dd, near, 3 if n * m < 200000 else 1)
        a = try_close(a, n, m, s, cp, de, dd, near)
        v = objective(a, s, dd)
        if v < bv:
            bv = v
            ba = a[:]
    ph = {(i, j): 1.0 for i in range(m) for j in near[i]}
    it = 50 if n * m <= 50000 else 20 if n * m <= 500000 else 8
    ants = 7 if n * m <= 300000 else 4
    for t in range(it):
        ia = None
        iv = 10 ** 99
        for z in range(ants):
            a = build_ant(n, m, s, cp, de, dd, near, ph, rnd)
            if a is None:
                a = fallback(n, m, cp, de, dd)
            if a is None:
                continue
            a = improve_moves(a, n, m, s, cp, de, dd, near, 1)
            v = objective(a, s, dd)
            if v < iv:
                iv = v
                ia = a[:]
            if v < bv:
                bv = v
                ba = a[:]
        for key in list(ph):
            ph[key] = max(1e-6, ph[key] * 0.9)
        if ia is not None:
            add = 100.0 / max(iv, 1e-9)
            for i, j in enumerate(ia):
                if (i, j) in ph:
                    ph[(i, j)] += add
    if ba is None:
        ba = fallback(n, m, cp, de, dd)
    ba = improve_moves(ba, n, m, s, cp, de, dd, near, 2)
    ba = try_close(ba, n, m, s, cp, de, dd, near)
    print('%.6f' % objective(ba, s, dd))
    print(' '.join(str(int(x)) for x in ba))


if __name__ == '__main__':
    main()
