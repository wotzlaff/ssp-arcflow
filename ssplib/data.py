import collections

def strip_large_parts(inst):
    threshold, lvec, bvec = inst
    lvecn, bvecn = [], []
    for li, bi in zip(lvec, bvec):
        if li < threshold:
            lvecn.append(li)
            bvecn.append(bi)
    return threshold, lvecn, bvecn


def read(name):
    lines = open(name, 'r').read().split('\n')
    nb_instances = int(lines[0])

    counter = 0
    for line in lines[1:]:
        if len(line.strip()) == 0:
            continue
        line = line.split()
        nb_items = int(line[0])
        threshold = int(line[1])
        line = [int(v) for v in line[2:]]
        inst = threshold, line[:nb_items], line[nb_items:2 * nb_items]
        yield strip_large_parts(inst)
        counter += 1
    assert counter == nb_instances
