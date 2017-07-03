import os
import numpy as np
import pandas as pd
from .gcquant_methods import GCMethods

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

    def __init__(self, lib, area,standards):

        self._compiled = gcm._compiled(lib,area)
        self._stdcurves = gcm._stdcurves(self._compiled,standards)
        self._concentrations = gcm._concentrations(self.compiled,self._stdcurves)
        self._concentrations_exp = gcm._concentrations_exp(self._concentrations,standards)
        self._concentrations_std = gcm._concentrations_std(self._concentrations,standards)
        self._plots = []

    @property
    def compiled(self):
        return self._compiled

    @property
    def stdcurves(self):
        return self._stdcurves

    @property 
    def concentrations(self):
        return self._concentrations

    @property 
    def concentrations_exp(self):
        return self._concentrations_exp   

    @property 
    def concentrations_std(self):
        return self._concentrations_std


