def parse_file(filename):
    with open(filename) as f:
        n, m = map(int, f.readline().split())
        costs = []
        sets = []
        for _ in range(m):
            data = list(map(int, f.readline().split()))
            costs.append(data[0])
            sets.append(set(data[1:]))
    return n, m, costs, sets
