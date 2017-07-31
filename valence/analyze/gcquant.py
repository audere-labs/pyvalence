""" describe this module
"""

import numpy as np
import pandas as pd
from scipy.stats import linregress


class MatchHack():

    def __init__(self, threshold):
        self.threshold = threshold
        self.last_match = 0

    @staticmethod
    def find_match(x, Y, threshold):
        """ find index of argmin lambda(x,Y) """
        def score(y):
            u = abs(x - y)
            return u if u < threshold else np.nan
        return_value = Y.apply(score).idxmin()
        return return_value

    def rt_match(self, lib_row, rt):
        x, i = lib_row.rt, self.last_match
        match = self.find_match(x, rt[i:], self.threshold)
        if not pd.isnull(match):
            self.last_match = match + 1
        return match

    def rt_matcher(self, longs, shorts):
        return shorts.apply(self.rt_match, rt=longs.rt.sort_values(), axis=1)
    


def match_area(lib, area, threshold=0.1):
    """ Matches areas to identified via MS spectra based on retention times. 

    The method matches the species which have the smallest difference
    between the two retention times that is smaller than the set threshold.

        Args
        ----
        lib : pandas.DataFrame
            A dataframe containing identified species and associated retention time.
            the dataframe can be created from csv files by using AgilentGcms class
            from the build module within Valence. It can also be created manually
            but must contain a 'library_id' and 'rt' column.
        area : pandas.DataFrame
            A dataframe containing peak area integrations and associated
            retention time. The dataframe can be created from csv files by 
            using AgilentGcms class from the build module within Valence. 
            It can also be created manually but must contain a 'area' and 'rt' column.
        threshold : float
            The threshold is an optional falue (default = 0.1) for which the difference
            of two RTs, one from lib and one from area, must be below for the 
            match to be accepted.

        Returns
        -------
        pandas.DataFrame
            Returned is a dataframe which has library IDs matched to an area based 
            on the difference of the retention times.

    """
    def find_match(x, Y):
        """ find index of argmin lambda(x,Y) """
        def score(y):
            u = abs(x - y)
            return u if u < threshold else np.nan
        return_value = Y.apply(score).idxmin()
        return return_value

    # def rt_match(lib_row, rt):        
    #     """ find closest rt """   
    #     x, i = lib_row.rt, lib_row.name
    #     return find_match(x, rt[i:])

    def matchiter(lib, area):
        """ match area on rt from single df """
        match_hack = MatchHack(threshold)
        lib = lib.assign(area=np.nan)
        lib = lib.assign(rt_area=np.nan)
        if lib.shape[0] > area.shape[0]:
            xi = match_hack.rt_matcher(lib, area)
            xi, yi = xi[~pd.isnull(xi)], xi[~pd.isnull(xi)].index
            lib.area[xi] = area.area[yi]
            lib.rt_area[xi] = area.rt[yi]
        else:
            xi = match_hack.rt_matcher(area, lib)
            xi, yi = xi[~pd.isnull(xi)], xi[~pd.isnull(xi)].index
            lib.area[yi] = area.area[xi].values
            lib.rt_area[yi] = area.rt[xi]
        return lib.set_index('key')

    lib_grouped = (lib.groupby(lib.index))
    area_grouped = (area.groupby(area.index))
    returndf = lib_grouped.apply(
        lambda x: matchiter(
            x.reset_index(),
            area_grouped.get_group(x.name).reset_index())
    )
    return returndf.reset_index(level=0).drop(['header=', 'pct_area', 'ref','key'], axis=1)

def std_curves(compiled, standards):
    """ Takes matched_area dataframe (compiled), of species with areas and ids
        and a standards dataframe to calculate the corresponding response factor (RF)

        Args
        ----
        compiled : pandas.DataFrame
            Compiled is a dataframe containing identified species and an associated
            area with unknown concentrations. It can be generated from match_area
        standards : pandas.DataFrame
            Standards is a dataframe containing all species for which there is 
            calibration standard. The first column should be 'library_id' and each
            subsequent column should contain the file name for a stanards vial. The
            value of each row for file should be the concentration in Molar for that 
            species in that vial.

        Returns
        -------
        pandas.DataFrame
            Returns a dataframe with linearly regressed response factors and 
            associated statics for the calculation.

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
    def lin_wrap(group):
        """ """
        if group.shape[0] > 1:
            return linregress(group.area, group.cal_conc)
        else:
            pass

    matched_cal_conc = match_cal_conc(compiled, standards)
    b = (matched_cal_conc.groupby('library_id')
                            .apply(lambda df: lin_wrap(df))
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
    """ Calculates the concentration of species.

        Concentrations takes a dataframe which contains species matched
        to an area (compiled) and a calibration curve dataframe (stdcurves)
        it uses these values to calculate the concentration using the 
        slope (response factors) and intercept

        Args
        ----
        compiled : pandas.DataFrame
            Compiled is a dataframe containing identified species and an associated
            area with unknown concentrations. It can be generated from match_area
        stdcurves : pandas.DataFrame
            This is a dataframe containing the calculated response factors. It is 
            generated from std_curves

        Returns
        -------
        pandas.DataFrame
            A dataframe is returned which contains all data from compiled plus the
            calculated concentrations, concentration percentages, & area percentages
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
    """ Returns only species with unknown concentrations, no standards.

        This is a subset of the data generated from concentrations. It 
        provides a simple way to remove any standards in the dataset.

        Args
        ----
        concentrations : pandas.DataFrame
            Compiled is a dataframe containing identified species and an associated
            area with unknown concentrations. It can be generated from match_area
        standards : pandas.DataFrame
            Standards is a dataframe containing all species for which there is 
            calibration standard. The first column should be 'library_id' and each
            subsequent column should contain the file name for a stanards vial. The
            value of each row for file should be the concentration in Molar for that 
            species in that vial.

        Returns
        -------
        pandas.DataFrame
            A dataframe is returned which contains only data from concentrations
            which had unknown concentrations
    """
    std_keys = list(standards.keys())[1:]
    conc_df = concentrations.reset_index()
    return conc_df[-conc_df['key'].isin(std_keys)].set_index('key')

def concentrations_std(concentrations, standards):
    """ Returns only species with known concentrations, i.e. standards.

        This is a subset of the data generated from concentrations. It 
        provides a simple way get the standards from the dataset.

        Args
        ----
        concentrations : pandas.DataFrame
            Compiled is a dataframe containing identified species and an associated
            area with unknown concentrations. It can be generated from match_area
        standards : pandas.DataFrame
            Standards is a dataframe containing all species for which there is 
            calibration standard. The first column should be 'library_id' and each
            subsequent column should contain the file name for a stanards vial. The
            value of each row for file should be the concentration in Molar for that 
            species in that vial.

        Returns
        -------
        pandas.DataFrame
            A dataframe is returned which contains only data for standards/
    """
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

