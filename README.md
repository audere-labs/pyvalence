

<img src="images/pyvalence-logo.png" alt="pyvalence" width="80%" display="block" margin="auto">
<!-- ![valence](logo/valence-logo.png) -->

---

## Overview

`pyvalence` is a python package for processing data generated from analytical chemistry. `pyvalence` reads analytical data from native formats into readily accessible `pandas` DataFrames and supports common analysis techniques (e.g. standard curves regression and utilization) to reduce manual, one-off data processing.  Analysis conducted with `pyvalence` allows researchers to spend less time processing data and more time interpreting results.  

### Features

`pyvalence` easily import data from a root directory using `pyvalence.build`

```
agi = AgilentGcms.from_root('data-directory')
```

which provides easily accessible and organized data.

```
library_ids   = agi.results_lib
areas         = agi.results_tic
chromatograms = agi.chromatogram
```
Plotting the chromatogram is now simple with `pandas` plots based on `matplotlib`.

```
chromatgrams.loc['run1'].plot('tme','tic')
```
<p align="center">
  <img src="images/chrom.svg" alt="Chromatogram" width="50%" display="block" margin="auto">
</p>

For GCMS data `pyvalence.analysis` will compile data, create regression curves and calculate concentrations in few lines of code. 

```
compiled_data = match_area(lib,area)
curves        = std_curves(comp,stnd)
conc          = concentrations(compiled_data,curves)
```

## Installation

### conda

`pyvalence` depends on scientific python packages that can be tricky to build from source.  For that reason, we recommend the [Anaconda python distribution](https://www.continuum.io/downloads) which utilizes the `conda` package management system.

With `conda`, binary installers for the planning version of `pyvalence` are accessible via:

``` bash
conda install -c blakeboswell pyvalence
```

### PyPi

``` bash
pip install pyvalence
```

### Installing from Source

> Forthcoming

## Dependencies

- [`Python`](https://www.python.org) >= 3.6

The following dependencies are bundled in the `pyvalence` install:

- [`pandas`](http://pandas.pydata.org) >= 0.20.2
- [`numpy`](https://www.scipy.org) >= 1.13.1
- [`scipy`](http://www.numpy.org)  >= 0.19.1


### Examples

Tour the _on-rails_ example notebooks at [`pyvalence` on-rails](https://github.com/audere-labs/pyvalence-on-rails).

## License

[BSD 3-clause](https://github.com/audere-labs/pyvalence/blob/master/LICENSE)


