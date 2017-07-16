import pandas as pd
from valence.build import AgilentGcms
from valence.analyze import (
    match_area,
    std_curves,
    concentrations,
    GCQuant
)


if __name__ == '__main__':
    
    agi = AgilentGcms.from_root('data/test3')

    lib = agi.results_lib
    area = agi.results_tic

    # print('library head')
    # print(lib.head())

    # print('area head')
    # print(area.head())

    standards = pd.read_csv('data/standards.csv')

    print('match area')
    comp = match_area(lib, area)
    print(comp.head())

    print('std curves')
    stdc = std_curves(comp, standards)
    print(stdc.head())

    print('concentations')
    conc = concentrations(comp, stdc)
