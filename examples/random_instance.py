import numpy as np
import ssplib

def print_solution(value, solution):
    print(f'optimal value = {value}')
    print('solution:')
    for val, length, items in solution:
        print(f'use {val} x {items} (length = {length})')


def main():
    # fix random seed (to get the same instance at each run)
    np.random.seed(42)
    inst = ssplib.generate.random(50, 5, 45, 10)
    print(inst)

    # try all three models
    for mod in [ssplib.arcflow, ssplib.larcflow, ssplib.reflect]:
        print(f'\nmodel: {mod.__name__}')
        # build and solve IP model
        model = mod.build(inst)
        model.setParam('OutputFlag', 0)
        model.optimize()

        print('-- solution of integer problem --')
        solution = mod.extract_solution(inst, model)
        print_solution(model.objVal, solution)

        # solve LP relaxation
        model = model.relax()
        model.optimize()

        print('-- solution of lp relaxation --')
        solution = mod.extract_solution(inst, model)
        print_solution(model.objVal, solution)


if __name__ == '__main__':
    main()
