import argparse
import glob
import os
import time
import gurobipy as gp

import ssplib
models = dict(
    arcflow=ssplib.arcflow,
    larcflow=ssplib.larcflow,
    reflect=ssplib.reflect,
)


def main():
    p = argparse.ArgumentParser(description='Solve all SSP instances')
    p.add_argument('files', help='instance dat files', nargs='+')
    p.add_argument('--model', '-m', choices=['arcflow', 'larcflow', 'reflect'])
    p.add_argument('--out', '-o', help='output log file', type=argparse.FileType('w'))
    p.add_argument('--relax', '-r', help='solve relaxation only', action='store_true')
    args = p.parse_args()

    model = models[args.model]
    print(f'using model {model.__name__}')
    print(f'writing to {args.out.name}')
    print(f'reading {len(args.files)} files')

    for f in args.files:
        print(f'file {f}')
        block = os.path.basename(f)
        for idx, inst in enumerate(ssplib.data.read(f)):
            t0 = time.time()
            m = model.build(inst)
            m.update()
            if args.relax:
                m = m.relax()
            t1 = time.time()
            dt_model, t0 = t1 - t0, t1
            m.optimize()
            t1 = time.time()
            dt_solve = t1 - t0
            if m.status == gp.GRB.INTERRUPTED:
                raise KeyboardInterrupt()
            args.out.write(f'{block}\t{idx}\t{m.objVal}\t{m.numVars}\t{m.numConstrs}\t{m.numNZs}\t{dt_model}\t{dt_solve}\n')


if __name__ == '__main__':
    main()
