import numpy as np
import collections
import itertools


def all(threshold, n, exact_n=False):
    last_n = 0
    for items in itertools.combinations_with_replacement(range(1 if exact_n else 0, threshold), n):
        ls, bs = [], []
        for li, bi in sorted(collections.Counter(items).items(), reverse=True):
            if li == 0:
                continue
            ls.append(li)
            bs.append(bi)
        n = sum(bs)
        if n > last_n:
            print('n = {}'.format(n))
            last_n = n
        yield threshold, ls, bs


def random(threshold, lmin, lmax, n):
    parts = collections.Counter()
    for r in np.random.randint(lmin, lmax, size=n):
        parts[r] += 1
    ls, bs = [], []
    for li, bi in sorted(parts.items(), reverse=True):
        ls.append(li)
        bs.append(bi)
    return (threshold, ls, bs)
