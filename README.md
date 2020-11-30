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