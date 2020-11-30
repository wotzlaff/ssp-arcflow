import gurobipy as gp
from sortedcontainers import SortedSet
import collections

def create_larcflow_arcs(inst):
    threshold, lvec, bvec = inst
    m = len(lvec)
    is_active = SortedSet([0])

    min_shifted = threshold
    arcs = set()
    for item in range(m):
        for node in list(reversed(is_active)):
            for rep in range(bvec[item]):
                start = node + rep * lvec[item]
                if start >= threshold:
                    break
                end = start + lvec[item]
                if end > threshold:
                    start = threshold - lvec[item]
                    end = threshold
                    min_shifted = min(min_shifted, start)
                arcs.add((start, end, item, 's'))
                is_active.add(end)
    # activate all tails
    for arc in arcs:
        is_active.add(arc[0])

    # create list of active nodes in reversed order
    active_n = []
    for j in reversed(is_active):
        if j == threshold:
            continue
        if j < min_shifted:
            break
        active_n.append(j)
    # create loss arcs between active nodes
    for i in range(len(active_n) - 1):
        arcs.add((active_n[i], active_n[i + 1], -1, 'l'))

    return is_active, arcs


def create_variable_start(inst, is_active, patterns):
    threshold, lvec, bvec = inst
    vals = collections.Counter()
    loss = []
    for pattern in patterns:
        start = 0
        for item, count in pattern.items():
            for _ in range(count):
                end = start + lvec[item]
                if end > threshold:
                    shifted_start = threshold - lvec[item]
                    # remember to add loss arc value
                    loss.append((start, shifted_start))
                    # update start and end
                    end = threshold
                    start = shifted_start
                vals[(start, end, item, 's')] += 1
                start = end
    # add loss arc values
    for start, end in loss:
        idxs = list(is_active.irange(end, start, reverse=True))
        for i, j in zip(idxs, idxs[1:]):
            vals[(i, j, -1, 'l')] += 1
    return vals


def build(inst, patterns=None, bound=None, relaxed=False):
    threshold, lvec, bvec = inst
    m = len(lvec)
    assert m == len(bvec)
    is_active, arcs = create_larcflow_arcs(inst)
    arcs = gp.tuplelist(arcs)

    model = gp.Model()
    x = model.addVars(arcs, name='x', vtype=gp.GRB.CONTINUOUS if relaxed else gp.GRB.INTEGER, ub=[
        gp.GRB.INFINITY if arc[2] == -1 else bvec[arc[2]] for arc in arcs
    ])

    # set start values
    if patterns is not None:
        for arc, count in create_variable_start(inst, is_active, patterns).items():
            x[arc].start = count

    for j in is_active:
        if j == 0 or j == threshold:
            continue
        model.addConstr(x.sum(j, '*', '*', '*') == x.sum('*', j, '*', '*'))

    for i in range(m):
        model.addConstr(x.sum('*', '*', i, '*') <= bvec[i])

    obj = x.sum('*', threshold, '*', '*')
    model.setObjective(obj, sense=gp.GRB.MAXIMIZE)

    if bound is not None:
        model.addConstr(obj <= bound)
    return model



def format_solution(lvec, val, path):
    length = 0
    solution = []
    for arc in path:
        if arc == 'R' or (arc[2] == -1 and arc[3] == 'r'):
            solution.append('R')
        elif arc[3] == 'l':
            if isinstance(solution[-1], str) and solution[-1][-1] == 'L':
                solution[-1] = '{}xL'.format(int(solution[-1][:-2]) + 1)
                continue
            solution.append('1xL')
        else:
            larc = lvec[arc[2]]
            solution.append(larc)
            length += larc
    return val, length, solution


def _name2tuple(name):
    i, j, k, t = name[2:-1].split(',')
    return int(i), int(j), int(k), t

def extract_solution(inst, model, eps=1e-6):
    threshold, lvec, bvec = inst

    vals = gp.tupledict([
        (_name2tuple(v.varName), v.x)
        for v in model.getVars()
        if v.x > eps
    ])
    arcs = vals.keys()

    solutions = []
    for arc0 in arcs.select(0):
        while vals[arc0] > eps:
            minval = vals[arc0]
            start, next_start, item, kind = arc0
            current_path = [arc0]
            vals[arc0] -= minval
            while next_start < threshold:
                next_arcs = [arc for arc in arcs.select(next_start) if vals[arc] > eps]
                next_arcs.sort(key=lambda arc: arc[1])
                assert len(next_arcs) > 0
                arc1 = start, end, item, kind = next_arcs[0]
                if vals[arc1] < minval:
                    diff = minval - vals[arc1]
                    for arc in current_path:
                        vals[arc] += diff
                    minval = vals[arc1]
                vals[arc1] -= minval
                current_path.append(arc1)
                next_start = end
            solutions.append((minval, current_path))
    return [format_solution(lvec, v, sol) for v, sol in solutions]
