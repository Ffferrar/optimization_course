import sys

def do_dp(n, W, stuff):
    arr = [0] * (W + 1)
    for val, wei in stuff:
        for j in range(W, wei - 1, -1):
            x = arr[j - wei] + val
            if x > arr[j]:
                arr[j] = x
    return arr[W]

def frac(stuff_sorted, start, room):
    z = 0
    r = room
    for i in range(start, len(stuff_sorted)):
        v, w = stuff_sorted[i][0], stuff_sorted[i][1]
        if r <= 0:
            break
        if w <= r:
            z += v
            r -= w
        else:
            z += v * r / w
            r = 0
    return z

def do_bnb(n, W, stuff):
    t = sorted([(v, w) for v, w in stuff], key=lambda x: -x[0] / x[1] if x[1] else 0)
    best_so_far = 0
    q = 0
    for v, w in t:
        if q + w <= W:
            best_so_far += v
            q += w
    st = [(0, 0, 0)]
    while st:
        i, a, b = st.pop()
        if i >= len(t):
            continue
        v, w = t[i][0], t[i][1]
        upper_bound_if_we_skip_this_item = a + frac(t, i + 1, W - b)
        if upper_bound_if_we_skip_this_item > best_so_far:
            st.append((i + 1, a, b))
        if b + w <= W:
            new_val = a + v
            if new_val > best_so_far:
                best_so_far = new_val
            u = new_val + frac(t, i + 1, W - b - w)
            if u > best_so_far:
                st.append((i + 1, new_val, b + w))
    return best_so_far

lines = sys.stdin.read().strip().split("\n")
n, W = map(int, lines[0].split())
stuff = [tuple(map(int, line.split())) for line in lines[1 : n + 1]]

if W <= 200000:
    ans = do_dp(n, W, stuff)
else:
    ans = do_bnb(n, W, stuff)

print(int(ans))
