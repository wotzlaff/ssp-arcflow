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