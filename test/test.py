import pandas as pd
from pyvalence.build import AgilentGcms
from pyvalence.analyze import (
    match_area,
    std_curves,
    concentrations,
    find_peaks
)


if __name__ == '__main__':

    agi = AgilentGcms.from_root('data/test4')
    # agi = AgilentGcms.from_dir('data/test4/FA02.D')

    lib = agi.results_lib
    area = agi.results_tic

    print('library head')
    print(type(lib))
    if not lib is None:
        print(lib.head())

    print('area head')
    print(type(area))
    if not area is None:
        print(area.head())

    print('match area')
    comp = match_area(lib, area)
    if not comp is None:
        print(comp.head())

    standards = pd.read_csv('data/standards.csv')

    print('std curves')
    stdc = std_curves(comp, standards)
    if not stdc is None:
        print(stdc.head())

    print('concentations')
    conc = concentrations(comp, stdc)
    if not conc is None:
        print(conc.head())

    print('chromotogram peaks')
    
    chrom = agi.chromatogram
    test_key = chrom.index.unique()[0]
    chrom = chrom.loc[test_key]

    print(chrom.head())
    peaks = find_peaks(chrom.tic, height = chrom.tic.mean())
    print(peaks)
