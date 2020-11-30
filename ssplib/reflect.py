import gurobipy as gp
from sortedcontainers import SortedSet
import collections

from .larcflow import format_solution

def create_reflect_arcs(inst):
    threshold, lvec, bvec = inst
    m = len(lvec)
    is_active = SortedSet([0])
    souvenir = SortedSet([0])

    min_rpoint = threshold
    arcs = set()
    for item in range(m):
        done = SortedSet()
        for k in range(0, bvec[item]):
            for start in list(reversed(souvenir)):
                if start in done or start == threshold:
                    continue
                done.add(start)
                end = start + 2 * lvec[item]
                if end <= threshold:
                    souvenir.add(end)
                    kind = 's'
                else:
                    end = 2 * threshold - end
                    kind = 'r'
                    min_rpoint = min(min_rpoint, end)
                arcs.add((start, end, item, kind))
                is_active.add(end)

    active_n = []
    for j in is_active:
        if j < min_rpoint or j == threshold:
            continue
        active_n.append(j)
    active_n.append(threshold)

    for i in range(len(active_n) - 1):
        arcs.add((active_n[i], active_n[i + 1], -1, 'l'))
    arcs.add((threshold, threshold, -1, 'r'))

    return is_active, min_rpoint, arcs


def create_variable_start(inst, is_active, patterns):
    threshold, lvec, bvec = inst
    vals = collections.Counter()
    for pattern in patterns:
        start = 0
        for item, count in pattern.items():
            for _ in range(count):
                end = start + 2 * lvec[item]
                if end <= threshold:
                    vals[(start, end, item, 's')] += 1
                    start = end
                    if start == threshold:
                        start = 0
                else:
                    end = 2 * threshold - end
                    vals[(start, end, item, 'r')] += 1
                    start = 0
    # TODO: set values for loss arcs (atm Gurobi fills the gaps for us)
    return vals

def build(inst, patterns=None, bound=None, relaxed=False):
    threshold, lvec, bvec = inst
    assert len(lvec) == len(bvec)
    is_active, min_rpoint, arcs = create_reflect_arcs(inst)
    arcs = gp.tuplelist(arcs)

    model = gp.Model()
    x = model.addVars(arcs, name='x', vtype=gp.GRB.CONTINUOUS if relaxed else gp.GRB.INTEGER, lb=0, ub=[
        gp.GRB.INFINITY if arc[2] == -1 else bvec[arc[2]] for arc in arcs
    ])
    x[(threshold, threshold, -1, 'r')].lb = -gp.GRB.INFINITY

    # set start values
    if patterns is not None:
        for arc, count in create_variable_start(inst, is_active, patterns).items():
            x[arc].start = count

    for j in is_active:
        if j == 0:
            continue
        sin = x.sum('*', j, '*', 's')
        sout = x.sum(j, '*', '*', 's')
        rin = x.sum('*', j, '*', 'r')
        rout = x.sum(j, '*', '*', 'r')
        lin = x.sum('*', j, '*', 'l')
        lout = x.sum(j, '*', '*', 'l')
        model.addConstr(sin + lout == rin + lin + rout + sout)
        if j >= min_rpoint and j < threshold:
            model.addConstr(lin + rin >= lout)

    cout0 = x.sum(0, '*', '*', '*')
    nb_refl = x.sum('*', '*', '*', 'r')
    model.addConstr(cout0 == 2 * nb_refl)

    for i in range(len(bvec)):
        model.addConstr(x.sum('*', '*', i, '*') <= bvec[i])

    obj = x.sum('*', '*', '*', 'r')
    model.setObjective(obj, sense=gp.GRB.MAXIMIZE)

    if bound is not None:
        model.addConstr(obj <= bound)
    return model


def _find_path_fwd(arc0, arcs, vals, eps):
    while vals[arc0] > eps:
        minval = vals[arc0]
        start, end, item, kind = arc0
        next_start = end
        assert kind == 's' or kind == 'r'
        current_path = [arc0]
        while kind != 'r':
            next_arcs = [
                arc for arc in arcs.select(next_start)
                if vals[arc] > eps and arc[3] != 'l'
            ]
            if len(next_arcs) == 0:
                break
            arc1 = start, end, item, kind = next_arcs[0]
            minval = min(minval, vals[arc1])
            current_path.append(arc1)
            next_start = end

        assert len(current_path) > 0
        for arc in current_path:
            vals[arc] -= minval
        yield minval, current_path


def _combine_paths(partial_s, partial_r, arcs, vals, eps):
    solutions = []
    partial_s.sort(key=lambda p: p[1][-1][1])

    for val, path in partial_s:
        end = path[-1][1]

        pathl = []
        while val > eps:
            minval = val
            for arc1 in pathl:
                minval = min(minval, vals[arc1])

            for i, (valr, pathr) in enumerate(partial_r):
                endr = pathr[-1][1]
                if endr == end:
                    minval = min(minval, valr)
                    solutions.append((minval, path + pathl + pathr))
                    val -= minval
                    for arc1 in pathl:
                        vals[arc1] -= minval
                    if valr - minval <= eps:
                        partial_r.pop(i)
                    else:
                        partial_r[i] = (valr - minval, pathr)
                    break
            else:
                next_arcs = [
                    arc for arc in arcs.select('*', end, -1, 'l')
                    if vals[arc] > eps
                ]
                assert len(next_arcs) == 1
                arc1 = next_arcs[0]
                end = arc1[0]
                minval = min(minval, vals[arc1])
                pathl.append(arc1)
    return solutions

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

    partial_s = []
    partial_r = []
    for arc0 in arcs.select(0):
        for val, path in _find_path_fwd(arc0, arcs, vals, eps):
            (partial_r if path[-1][-1] == 'r' else partial_s).append((val, path))

    solutions = _combine_paths(partial_s, partial_r, arcs, vals, eps)

    if len(partial_r) > 0:
        for val, path in partial_r:
            while val > eps:
                pathl = []
                arc1 = path[-1]
                end = arc1[1]
                minval = val
                while end != threshold:
                    next_arcs = [
                        arc for arc in arcs.select(end, '*', -1, 'l')
                        if vals[arc] > eps
                    ]
                    assert len(next_arcs) == 1
                    arc1 = next_arcs[0]
                    end = arc1[1]
                    minval = min(minval, vals[arc1])
                    pathl.append(arc1)
                for arc in pathl:
                    vals[arc] -= minval
                solutions.append((minval, path + pathl + ['R']))
                val -= minval
    return [format_solution(lvec, v, sol) for v, sol in solutions]
