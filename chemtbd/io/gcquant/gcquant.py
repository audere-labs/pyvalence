import os
import numpy as np
import pandas as pd
from .gcquant_methods import GCMethods
from scipy.stats import linregress
gcm = GCMethods()

class GCQuant(object):
    ''' quantifies the concentrations based on calibration curves using dataframes
        generated from Agilent

        Constructors:
            align: aligns lib and tic/fid on r.t.

        Attributes:
            keys: dir_keys
            datams: data collected from data.ms files as DataFrame
            results_fid: fid table from results.csv files as DataFrame
            resutls_lib: lib table from results.csv files as DataFrame
            results_tic: tic table from result.csv files as DataFrame
    '''

    def __init__(self, lib, area):

        self._align = gcm._matchlib2area(lib,area)


    @property
    def align(self):
        return self._align

    @classmethod
    def stdcurves(self,aligned,standards):
        '''
        takes in aligned dataframe of species aligned with areas and a standards df
        and calculates the corresponding RF
        s
        this is only for cases where each molecule has a calibration curve i.e. tic and/or fid
        '''
        matched_cal_conc = gcm._match_cal_conc(aligned, standards)
        b = (matched_cal_conc.groupby('library_id')
                             .apply(lambda a: linregress(a.area,a.cal_conc))
                             .apply(pd.Series)
                             .reset_index())
        b.columns = ['library_id','responsefactor','intercept','rvalue','pvalue','stderr']
        
        d = pd.DataFrame({'max':matched_cal_conc.groupby('library_id')['area'].max(),
                        'min':matched_cal_conc.groupby('library_id')['area'].min()}).reset_index()
        return pd.merge(b,d,on='library_id')
        return matched_cal_conc

    @classmethod
    def concentrations(self,aligned,rfactors):
        '''
        this  function takes a dataframe which contains species matched to an area (aligned) 
        and a calibration curve dataframe (rfactors)
        
        it uses these values to calculate the concentration using the slope (responsefactors) and intercept
        '''
        def conc_cal(x):
            conc = (x['area']*x['responsefactor']+x['intercept'] if x['area']*x['responsefactor']+x['intercept']>0 else np.nan)
            return conc
    
        # calculate concentration of species
        aligned = aligned.reset_index()
        return_df = pd.merge(aligned,rfactors,on='library_id',how='outer')
        return_df['conc'] = return_df.apply(conc_cal,axis=1)
        return_df.drop(['rvalue','pvalue','stderr'],1,inplace=True)

        #calculate concentration percentage 
        totals_c = pd.DataFrame({'totals_c':(return_df.groupby('key')['conc']
                                                .apply(np.sum,axis=0))}).reset_index()                     
        return_df = return_df.merge(totals_c, on=['key'])
        return_df['conc%']=return_df['conc']/return_df['totals_c']
        return_df.drop(['totals_c'],1,inplace=True)
        
        #calculate area percentage
        totals_a = pd.DataFrame({'totals_a':(return_df.groupby('key')['area']
                                                .apply(np.sum,axis=0))}).reset_index()                     
        return_df = return_df.merge(totals_a, on=['key'])
        return_df['area%']=return_df['area']/return_df['totals_a']
        return_df.drop(['totals_a'],1,inplace=True)
        
        return return_df.set_index('key')