# Arcflow models for the Skiving Stock Problem (SSP)
Here, you can find the reference implementation of the arcflow-based models for the SSP introduced in [[1]](#1).

A basic example looks like this:
```python
import ssplib

inst = 10, [6, 5, 4, 3], [1, 1, 2, 4]
print(inst)

model = ssplib.arcflow.build(inst)
model.optimize()
print(model.objVal)

solution = ssplib.arcflow.extract_solution(inst, model)
print(solution)
```

## Installation
The file `environment.yml` contains a description of all required packages.
You can create a clean conda environment from this file using
```
conda env create
```
and activate it using
```
conda activate grb
```

Afterwards, use
```
conda develop .
```
to setup a link to the `ssplib` package such that it can be loaded easily.

## Usage
Example scripts can be found in the `examples` directory.

For instance, start
```
python examples/benchmark_datasets.py -m arcflow ../ssp-data/data/C1/Scholl_3_HARD.dat -o scholl3_reflect.log --relax
```
to compute solve the LP relaxation of the instances in `Scholl_3_HARD.dat`, where `../ssp-data` is the location of the `ssp-data` directory which contains the data from [here](https://github.com/wotzlaff/ssp-data).

## References
<a id="1">[1]</a>
Martinovic, J., Delorme, M., Iori, M., Scheithauer, G., & Strasdat, N. (2020). Improved flow-based formulations for the skiving stock problem. Computers & Operations Research, 113, 104770.