import sys
import os
import subprocess
import time
import math

from parser import parse_file

def main():
    time_limit = 60
    paths = []
    i = 1
    while i < len(sys.argv):
        if sys.argv[i] == '--time-limit':
            time_limit = int(sys.argv[i + 1])
            i += 2
        else:
            paths.append(sys.argv[i])
            i += 1

    files = []
    for p in paths:
        if os.path.isdir(p):
            for name in sorted(os.listdir(p)):
                fp = os.path.join(p, name)
                if os.path.isfile(fp) and not name.startswith('.'):
                    files.append(fp)
        else:
            files.append(p)

    solver = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'solver.py')

    for path in files:
        name = os.path.basename(path)
        n, coords = parse_file(path)
        cmd = [sys.executable, solver, path, '--seed', '42', '--time-limit-sec', str(time_limit)]
        start = time.time()
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=time_limit + 30)
        except subprocess.TimeoutExpired:
            print('timeout')
            continue
        elapsed = time.time() - start

        if res.returncode != 0:
            print('error')
            continue

        tour = list(map(int, res.stdout.strip().split()))
        if len(tour) != n or sorted(tour) != list(range(n)):
            print('error')
            continue

        total = 0
        for i in range(n):
            ax, ay = coords[tour[i]]
            bx, by = coords[tour[(i + 1) % n]]
            total += math.sqrt((ax - bx) ** 2 + (ay - by) ** 2)

        print(name, n, total, elapsed, 'OK')


if __name__ == '__main__':
    main()
