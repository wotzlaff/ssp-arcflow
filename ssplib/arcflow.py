import gurobipy as gp
from sortedcontainers import SortedSet
import collections

def create_arcflow_arcs(inst):
    threshold, lvec, bvec = inst
    m = len(lvec)
    is_active = SortedSet([0])
    arcs = set()
    for item in range(m):
        for node in list(reversed(is_active)):
            if node == threshold:
                continue
            for rep in range(bvec[item]):
                start = node + rep * lvec[item]
                if start >= threshold:
                    break
                end = min(threshold, start + lvec[item])
                arcs.add((start, end, item))
                is_active.add(end)
    return is_active, arcs


def create_variable_start(inst, patterns):
    threshold, lvec, bvec = inst
    vals = collections.Counter()
    for pattern in patterns:
        start = 0
        for item, count in pattern.items():
            for _ in range(count):
                end = min(threshold, start + lvec[item])
                vals[(start, end, item)] += 1
                start = end
    return vals


def build(inst, patterns=None, bound=None, relaxed=False):
    threshold, lvec, bvec = inst
    m = len(lvec)
    assert m == len(bvec)
    is_active, arcs = create_arcflow_arcs(inst)
    arcs = gp.tuplelist(arcs)

    model = gp.Model()
    x = model.addVars(arcs, name='x', vtype=gp.GRB.CONTINUOUS if relaxed else gp.GRB.INTEGER, ub=[
        gp.GRB.INFINITY if arc[2] == -1 else bvec[arc[2]] for arc in arcs
    ])

    # set start values
    if patterns is not None:
        for arc, count in create_variable_start(inst, patterns).items():
            x[arc].start = count

    for j in is_active:
        if j == 0 or j == threshold:
            continue
        model.addConstr(x.sum(j, '*', '*') == x.sum('*', j, '*'))

    for i in range(m):
        model.addConstr(x.sum('*', '*', i) <= bvec[i])

    obj = x.sum(0, '*', '*')
    model.setObjective(obj, sense=gp.GRB.MAXIMIZE)

    if bound is not None:
        model.addConstr(obj <= bound)
    return model

def _name2tuple(name):
    i, j, k = name[2:-1].split(',')
    return int(i), int(j), int(k)

def extract_solution(inst, model, eps=1e-6):
    threshold, lvec, bvec = inst

    vals = gp.tupledict([
        (_name2tuple(v.varName), v.x)
        for v in model.getVars()
        if v.x > eps
    ])
    arcs = vals.keys()

    solutions = []
    for arc0 in arcs.select(0, '*', '*'):
        while vals[arc0] > eps:
            minval = vals[arc0]
            start, next_start, item = arc0
            current_path = [arc0]
            while next_start < threshold:
                next_arcs = [arc for arc in arcs.select(next_start, '*', '*') if vals[arc] > eps]
                assert len(next_arcs) > 0
                arc1 = start, end, item = next_arcs[0]
                minval = min(minval, vals[arc1])
                current_path.append(arc1)
                next_start = end
            solution = []
            for arc in current_path:
                vals[arc] -= minval
                solution.append(arc[2])
            solutions.append((minval, solution))

    return [(v, sum([lvec[k] for k in sol]), [lvec[k] for k in sol]) for v, sol in solutions]
