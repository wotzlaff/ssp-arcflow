import collections
import gurobipy
from gurobipy import GRB
import math


def extract_simple(threshold, lvec, uvec):
    solution = collections.Counter()
    m = len(lvec)
    # forward pass
    current_length = 0
    for k in range(m):
        if uvec[k] > 0 and current_length + lvec[k] <= threshold:
            take = min((threshold - current_length) // lvec[k], uvec[k])
            solution[k] = take
            uvec[k] -= take
            current_length += take * lvec[k]
    assert current_length <= threshold
    # backward pass
    if current_length < threshold:
        for k in reversed(range(m)):
            if uvec[k] > 0 and current_length + lvec[k] >= threshold:
                uvec[k] -= 1
                current_length += lvec[k]
                solution[k] += 1
                break
    # final pass
    if current_length < threshold:
        for k in reversed(range(m)):
            if uvec[k] > 0:
                take = min((threshold - current_length) // lvec[k], uvec[k])
                solution[k] = take
                uvec[k] -= take
                current_length += take * lvec[k]
                if current_length >= threshold:
                    break
    # remove unused item
    small_k = max(solution.keys())
    last_lk = lvec[small_k]
    while current_length - last_lk >= threshold:
        current_length -= last_lk
        solution[small_k] -= 1
        uvec[small_k] += 1

        if solution[small_k] == 0:
            del solution[small_k]
            small_k = max(solution.keys())
            last_lk = lvec[small_k]
    return solution, current_length


def extract_ssp_solution(threshold, lvec, uvec):
    m = len(lvec)
    model = gurobipy.Model()
    model.setParam(GRB.Param.OutputFlag, False)
    x = model.addVars(range(m), ub=uvec, vtype=GRB.INTEGER)
    model.setObjective(x.prod(lvec))
    model.addConstr(x.prod(lvec), sense=GRB.GREATER_EQUAL, rhs=threshold)
    model.optimize()

    if model.getAttr(GRB.Attr.Status) == GRB.Status.INTERRUPTED:
        raise Exception('Terminated.')

    solution = {}
    for k in range(m):
        xk = int(x[k].getAttr('x'))
        if xk > 0:
            solution[k] = xk
            uvec[k] -= xk
    length = int(model.getAttr(GRB.Attr.ObjVal))
    return solution, length


def check_solution(inst, solutions):
    threshold, lvec, bvec = inst
    m = len(lvec)
    # check feasibility
    used = [0] * m
    for solution in solutions:
        length = 0
        for k, count in solution.items():
            length += count * lvec[k]
            used[k] += count
        # feasible pattern
        assert length >= threshold, 'pattern not feasible'
        # minimal pattern
        last_lk = lvec[max(solution.keys())]
        assert length - last_lk < threshold, 'pattern not minimal'
    for k in range(m):
        assert used[k] <= bvec[k], 'overused item'


def print_solution(inst, solution):
    print('len = {} || '.format(sum([
        inst[1][k] * c
        for k, c in solution.items()
    ])) + ', '.join([
        '{}:{}'.format(inst[1][k], c)
        for k, c in solution.items()
    ]))


def heuristic_sequential(inst, method):
    threshold, lvec, bvec = inst
    uvec = bvec.copy()
    remaining = sum([li * bi for li, bi in zip(lvec, bvec)])
    solutions = []
    while remaining >= threshold:
        solution, length = method(threshold, lvec, uvec)
        if length < threshold:
            break
        remaining -= length
        # print_solution(inst, solution)
        solutions.append(solution)

    check_solution(inst, solutions)
    return solutions


def heuristic_a(inst):
    return heuristic_sequential(inst, extract_simple)


def heuristic_b(inst):
    return heuristic_sequential(inst, extract_ssp_solution)


def heuristic_c(inst):
    threshold, lvec, bvec = inst
    bins = []
    m = len(lvec)
    # pack each item
    for k in range(m):
        lk = lvec[k]
        for _rep in range(bvec[k]):
            # find first bin
            for b in bins:
                if b['length'] + lk <= threshold:
                    b['length'] += lk
                    b['content'][k] += 1
                    break
            else:
                # or create new bin
                b = {'length': lk, 'content': collections.Counter([k]), 'id': len(bins)}
                bins.append(b)
    # find filled and not filled bins
    filled, nfilled = [], []
    for b in bins:
        (filled if b['length'] == threshold else nfilled).append(b)

    # fill each bin
    while len(nfilled) > 1:
        first_bin = nfilled.pop(0)
        while first_bin['length'] < threshold:
            last_bin = nfilled[-1]
            for k in reversed(sorted(last_bin['content'].keys())):
                lk = lvec[k]
                while last_bin['content'][k] > 0:
                    last_bin['content'][k] -= 1
                    first_bin['content'][k] += 1
                    last_bin['length'] -= lk
                    first_bin['length'] += lk
                    if first_bin['length'] >= threshold:
                        break
                if first_bin['length'] >= threshold:
                    break
            if last_bin['length'] <= 0:
                nfilled.pop()
                break
        if first_bin['length'] >= threshold:
            filled.append(first_bin)
    solutions = [b['content'] for b in filled]
    check_solution(inst, solutions)
    return len(solutions)


def upper_bound_a(inst):
    threshold, lvec, bvec = inst
    remaining = sum([li * bi for li, bi in zip(lvec, bvec)])
    return remaining // threshold


def upper_bound_b(inst):
    threshold, lvec, bvec = inst
    return sum(bvec) // math.ceil(threshold / lvec[0])
