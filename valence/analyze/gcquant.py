""" describe this module
"""

import numpy as np
import pandas as pd
from scipy.stats import linregress


def match_area(lib, area, threshold=0.1):
    """ brief description ... match area from many dataframes

        Args
        ----
        lib : pandas.DataFrame
            describe lib
        area : pandas.DataFrame
            describe area
        threshold : float
            describe threshold, optional, default = 0.1

        Returns
        -------
        pandas.DataFrame
            describe what it returns

    """
    def find_match(x, Y):
        """ find index of argmin lambda(x,Y) """
        def score(y):
            u = (x - y)**2
            return u if u < threshold else np.nan
        return_value = Y.apply(score).idxmin()
        return return_value

    def rt_match(lib_row, rt):
        """ find closest rt """
        x, i = lib_row.rt, lib_row.name
        return find_match(x, rt[i:])

    def matchiter(lib, area):
        """ match area on rt from single df """
        lib = lib.assign(area=np.nan)
        if lib.shape[0] > area.shape[0]:
            xi = area.apply(rt_match, rt=lib.rt.sort_values(), axis=1)
            xi, yi = xi[~pd.isnull(xi)], xi[~pd.isnull(xi)].index
            lib.area[xi] = area.area[yi]
        else:
            xi = lib.apply(rt_match, rt=area.rt.sort_values(), axis=1)
            xi, yi = xi[~pd.isnull(xi)], xi[~pd.isnull(xi)].index
            lib.area[yi] = area.area[xi].values
        return lib.set_index('key')

    lib_grouped = (lib.groupby(lib.index))
    area_grouped = (area.groupby(area.index))
    returndf = lib_grouped.apply(
        lambda x: matchiter(
            x.reset_index(),
            area_grouped.get_group(x.name).reset_index())
    )
    return returndf.drop(['header=', 'pct_area', 'ref'], axis=1)


def std_curves(compiled, standards):
    """ brief description ...
        takes in compiled dataframe of species with areas and
        a standards df and calculates the corresponding RF
        this is only for cases where each molecule has a calibration
        curve i.e. tic and/or fid

        Args
        ----
        compiled : pandas.DataFrame
            describe compiled
        standards : pandas.DataFrame
            describe standards

        Returns
        -------
        pandas.DataFrame
            describe what it returns

    """
    def match_cal_conc(compiled, standards):
        """ this  function takes a dataframe which contains species
            matched to an area (matched_df) and a calibration concentration
            dataframe and matches these two based on library_id
        """
        standards_melted = pd.melt(
            standards,
            id_vars=['library_id'],
            value_vars=list(standards.keys()[1:])
        )
        standards_melted.columns = ['library_id', 'key', 'cal_conc']
        return (pd.merge(compiled.reset_index(),
                         standards_melted,
                         how='left',
                         on=['library_id', 'key'])
                  .dropna(subset=['cal_conc']))

    matched_cal_conc = match_cal_conc(compiled, standards)
    b = (matched_cal_conc.groupby('library_id')
                            .apply(lambda a: linregress(a.area, a.cal_conc))
                            .apply(pd.Series)
                            .reset_index())
    b.columns = ['library_id', 'responsefactor', 'intercept', 
                 'rvalue', 'pvalue', 'stderr']
    d = pd.DataFrame(
        {'max': matched_cal_conc.groupby('library_id')['area'].max(),
         'min': matched_cal_conc.groupby('library_id')['area'].min()}
    ).reset_index()
    return pd.merge(b, d, on='library_id')


def concentrations(compiled, stdcurves):
    """ this function takes a dataframe which contains species matched
        to an area (compiled) and a calibration curve dataframe (stdcurves)
        it uses these values to calculate the concentration using the 
        slope (responsefactors) and intercept
    """
    def conc_cal(x):
        aX = x['area'] * x['responsefactor']
        B = x['intercept']
        conc = aX + B if aX + B > 0 else np.nan
        return conc

    # calculate concentration of species
    compiled = compiled.reset_index()
    return_df = (pd.merge(compiled, stdcurves, on='library_id', how='outer')
                   .assign(conc=(lambda df: df.apply(conc_cal, axis=1)))
                   .drop(['rvalue', 'pvalue', 'stderr'], axis=1))

    # calculate concentration percentage
    totals_c = pd.DataFrame(
        {'totals_c': (return_df.groupby('key')['conc']
                               .apply(np.sum, axis=0))}
    ).reset_index()
    return_df = return_df.merge(totals_c, on=['key'])
    return_df['conc%'] = return_df['conc']/return_df['totals_c']
    return_df.drop(['totals_c'], axis=1, inplace=True)

    # calculate area percentage
    totals_a = pd.DataFrame(
        {'totals_a': (return_df.groupby('key')['area']
                               .apply(np.sum, axis=0))
        }
    ).reset_index()
    return_df = return_df.merge(totals_a, on=['key'])
    return_df['area%'] = return_df['area']/return_df['totals_a']
    drop_cols = ['totals_a', 'responsefactor', 'intercept', 'max','min']
    return_df.drop(drop_cols, axis=1, inplace=True)
    return return_df.set_index('key')


def concentrations_exp(concentrations, standards):
    std_keys = list(standards.keys())[1:]
    conc_df = concentrations.reset_index()
    return conc_df[-conc_df['key'].isin(std_keys)].set_index('key')

def concentrations_std(concentrations, standards):
    std_keys = list(standards.keys())[1:]
    conc_df = concentrations.reset_index()
    return conc_df[conc_df['key'].isin(std_keys)].set_index('key')


class GCQuant(object):
    """ quantifies the concentrations based on calibration curves using
        dataframes generated from AgilentGcms

        Args
        ----
        lib : pandas.DataFrame
            what is lib
        area : pandas.DataFrame
            what is area
        standards : pandas.DataFrame
            what is standards

    """
    def __init__(self, lib, area, standards):
        self._standards = standards
        self._compiled = match_area(lib, area)
        self._stdcurves = std_curves(self._compiled, self._standards)
        self._concentrations = concentrations(self._compiled, self._stdcurves)
        self._concentrations_exp = concentrations_exp(self._concentrations,
                                                      self._standards)
        self._concentrations_std = concentrations_std(self._concentrations, 
                                                      self._standards)
    
    @property
    def standards(self):
        """ pandas.DataFrame : describe what it is
        """
        return self._standards

    @property
    def compiled(self):
        """ pandas.DataFrame : describe what it is
        """
        return self._compiled

    @property
    def stdcurves(self):
        """ pandas.DataFrame : describe what it is
        """
        return self._stdcurves

    @property
    def concentrations(self):
        """ pandas.DataFrame : describe what it is
        """
        return self._concentrations

    @property
    def concentrations_exp(self):
        """ pandas.DataFrame : describe what it is
        """
        return self._concentrations_exp

    @property
    def concentrations_std(self):
        """ pandas.DataFrame : describe what it is
        """
        return self._concentrations_std

