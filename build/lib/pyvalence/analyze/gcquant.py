""" pyvalence.analyze contains the methods necessary to calculate
    concentrations from an Agilent GCMS where the species and areas have
    already been determined and are retained in a .csv file.
"""

import numpy as np
import pandas as pd
from scipy.stats import linregress


def match_area(lib, area, threshold=0.1, metrics=False):
    """ Matches areas to identified via MS spectra based on retention times.

        The method matches the species which have the smallest difference
        between the two retention times that is smaller than the set
        threshold.

        Args
        ----
        lib : pandas.DataFrame
            A dataframe containing identified species and associated
            retention time. The dataframe can be created from csv
            files by using AgilentGcms class from the build module
            within Valence. It can also be created manually but must
            contain a 'library_id' and 'rt' column.
        area : pandas.DataFrame
            A dataframe containing peak area integrations and associated
            retention time. The dataframe can be created from csv files by
            using AgilentGcms class from the build module within Valence.
            It can also be created manually but must contain a 'area' and
            'rt' column.
        threshold : float
            The threshold is an optional falue (default = 0.1) for which the
            difference of two RTs, one from lib and one from area, must be
            below for the match to be accepted.
        metrics: boolean
            When metrics is true the area peak, rt and delta between the
            matched lib peak is returned in additional columns of the
            dataframe. This allows for easy verification that matching
            worked correctly.

        Returns
        -------
        pandas.DataFrame
            Returned is a dataframe which has library IDs matched to an area
            based on the difference of the retention times.
    """
    def area_percent(comp):
        """
        """
        comp_g = comp.groupby(comp.index)
        comp['area%'] = (comp_g.apply(lambda x: x.area/x.area.sum())
                               .reset_index(level=0)
                               .drop('key', axis=1).area)
        return comp

    def matchiter(lib, area, threshold):
        """
        """
        df = (pd.DataFrame({
                    'xi': list(range(len(area))) * len(lib),
                    'yi': [k for j in [[i]*len(area)
                                       for i in range(len(lib))] for k in j]
        }))

        def distance(row, x, y):
            return abs(x[row.xi] - y[row.yi])

        def find_mins(df):
            xys, xs, ys = [], [], []
            while df.shape[0] > 0:
                top = df[df.index == df.distance.idxmin()]
                xys.append(top)
                xs.append(top.xi)
                ys.append(top.yi)
                df = df[~(df.xi.isin(xs) | (df.yi.isin(ys)))]
            return pd.concat(xys)

        df['distance'] = df.apply(
            distance,
            axis=1, x=area.rt.values, y=lib.rt.values
        )
        df = df[df.distance <= threshold]

        match = find_mins(df)
        xi, yi = match.xi, match.yi

        lib['area'] = np.nan
        lib.loc[yi, 'area'] = area.area[xi].values

        if metrics:
            lib['area_pk'] = lib['area_rt'] = lib['delta_rt'] = np.nan
            lib.loc[yi, 'area_pk'] = area.peak[xi].values
            lib.loc[yi, 'area_rt'] = area.rt[xi].values
            lib['delta_rt'] = np.abs(lib.loc[yi, 'rt']-lib.loc[yi, 'area_rt'])

        return lib.set_index('key')

    if lib is None or area is None:
        print('Not enough info for `match_area`.')
        return None

    lib_grouped = lib.groupby(lib.index)
    area_grouped = area.groupby(area.index)
    returndf = lib_grouped.apply(
        lambda x: matchiter(
            lib=x.reset_index(),
            area=area_grouped.get_group(x.name).reset_index(),
            threshold=threshold)
    )
    return area_percent(
        (returndf.reset_index(level=0)
                 .drop(['header=', 'pct_area', 'ref', 'key'], axis=1))
        )


def std_curves(compiled, standards):
    """ Takes matched_area dataframe (compiled), of species with areas and ids
        and a standards dataframe to calculate the corresponding response
        factor (RF)

        Args
        ----
        compiled : pandas.DataFrame
            Compiled is a dataframe containing identified species and an
            associated area with unknown concentrations. It can be generated
            from match_area
        standards : pandas.DataFrame
            Standards is a dataframe containing all species for which there is
            calibration standard. The first column should be 'library_id' and
            each subsequent column should contain the file name for a stanards
            vial. The value of each row for file should be the concentration
            in molar for that species in that vial.

        Returns
        -------
        pandas.DataFrame
            Returns a dataframe with linearly regressed response factors and
            associated statics for the calculation.
    """
    def match_cal_conc(compiled, standards):
        """ this  function takes a dataframe which contains species
            matched to an area (matched_df) and a calibration concentration
            dataframe and matches these two based on library_id.
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

    if compiled is None or standards is None:
        print('Not enough info for `std_curves`.')
        return None

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
        it uses these values to calculate the concentration using the slope
        (response factors) and intercept

        Args
        ----
        compiled : pandas.DataFrame
            Compiled is a dataframe containing identified species and an
            associated area with unknown concentrations. It can be generated
            from match_area
        stdcurves : pandas.DataFrame
            This is a dataframe containing the calculated response factors.
            It is generated from std_curves

        Returns
        -------
        pandas.DataFrame
            A dataframe is returned which contains all data from compiled plus
            the calculated concentrations, concentration percentages,
            & area percentages
    """
    def conc_cal(x):
        aX = x['area'] * x['responsefactor']
        B = x['intercept']
        conc = aX + B if aX + B > 0 else np.nan
        return conc

    if compiled is None or stdcurves is None:
        print('Not enough info for `concentrations`.')
        return None

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

    return return_df.set_index('key')


def concentrations_exp(concentrations, standards):
    """ Returns only species with unknown concentrations, no standards.

        This is a subset of the data generated from concentrations. It provides
         a simple way to remove any standards in the dataset.

        Args
        ----
        concentrations : pandas.DataFrame
            Compiled is a dataframe containing identified species and an
            associated area with unknown concentrations. It can be generated
            from match_area
        standards : pandas.DataFrame
            Standards is a dataframe containing all species for which there is
            calibration standard. The first column should be 'library_id' and
            each subsequent column should contain the file name for a stanards
            vial. The value of each row for file should be the concentration
            in Molar for that species in that vial.

        Returns
        -------
        pandas.DataFrame
            A dataframe is returned which contains only data from
            concentrations which had unknown concentrations
    """
    if concentrations is None or standards is None:
        print('Not enough info for `concentrations_exp`.')
        return None
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
            Compiled is a dataframe containing identified species and an
            associated area with unknown concentrations. It can be generated
            from match_area
        standards : pandas.DataFrame
            Standards is a dataframe containing all species for which there is
            calibration standard. The first column should be 'library_id' and
            each subsequent column should contain the file name for a stanards
            vial. The value of each row for file should be the concentration
            in Molar for that species in that vial.

        Returns
        -------
        pandas.DataFrame
            A dataframe is returned which contains only data for standards/
    """
    if concentrations is None or standards is None:
        print('Not enough info for `concentrations_std`.')
        return None
    std_keys = list(standards.keys())[1:]
    conc_df = concentrations.reset_index()
    return conc_df[conc_df['key'].isin(std_keys)].set_index('key')
