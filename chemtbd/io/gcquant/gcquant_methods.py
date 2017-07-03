import pandas as pd
import numpy as np
import warnings
from scipy.stats import linregress
warnings.filterwarnings("ignore")

class GCMethods(object):
	def __init__(self):
		pass

	def _find_match(self,x, Y):
		''' find index of argmin lambda(x,Y)
		'''
		threshold = 0.1
		def score(y):
			u = (x - y)**2
			return u if u < threshold else np.nan

		return_value = Y.apply(score).idxmin()
		return return_value

	def _rt_match(self,lib_row, rt):
		''' find closest rt
		'''
		x, i = lib_row.rt, lib_row.name
		return self._find_match(x, rt[i:])

	def _matchiter(self,lib,area):
		'''match area on rt from single df
		'''
		lib = lib.assign(area=np.nan)

		if lib.shape[0] > area.shape[0]:
			xi = area.apply(self._rt_match, rt=lib.rt.sort_values(), axis=1)
			xi, yi = xi[~pd.isnull(xi)], xi[~pd.isnull(xi)].index
			lib.area[xi] = area.area[yi]
		else:  
			xi = lib.apply(self._rt_match, rt=area.rt.sort_values(), axis=1)
			xi, yi = xi[~pd.isnull(xi)], xi[~pd.isnull(xi)].index
			lib.area[yi] = area.area[xi].values
		return lib.set_index('key')
		
	def _compiled(self,lib,area):
		'''match area from many dataframes
		'''
		lib_grouped = (lib.groupby(lib.index))
		area_grouped = (area.groupby(area.index))
		returndf = lib_grouped.apply(lambda x: self._matchiter(x.reset_index(),area_grouped.get_group(x.name).reset_index()))	
		returndf.drop(['header=','pct_area','ref'],1,inplace=True)
		return returndf

	def _match_cal_conc(matcheddf, standards):
		'''
		this  function takes a dataframe which contains species matched to an area (matched_df) 
		and a calibration concentration dataframe and matches these two based on library_id
		'''
		standards_melted = pd.melt(standards, id_vars=['library_id'],value_vars=cal_files)
		standards_melted.columns = ['library_id','key','cal_conc']
		
		return_df = pd.merge(matcheddf.reset_index(),standards_melted,how='left',on=['library_id','key'])
		return return_df.dropna(subset=['cal_conc'])

	def cal_curves(matched_cal_conc):
		'''
		this function takes a matched calibration concentration dataframe (matched_cal_conc)
		and does a linear regression and returns a dataframe of the library_ids with 
		linregress stats and the min/max areas which is the range for which the calibration
		curve can (should only) be used.
		
		this is only for cases where each molecule has a calibration curve i.e. tic and/or fid
		'''
		b = (matched_cal_conc.groupby('library_id')
							 .apply(lambda a: linregress(a.area,a.cal_conc))
							 .apply(pd.Series)
							 .reset_index())
		b.columns = ['library_id','slope','intercept','rvalue','pvalue','stderr']
		
		d = pd.DataFrame({'max':matched_cal_conc.groupby('library_id')['area'].max(),
						'min':matched_cal_conc.groupby('library_id')['area'].min()}).reset_index()
		return pd.merge(b,d,on='library_id')

	def _match_cal_conc(self,compiled, standards):
		'''
		this  function takes a dataframe which contains species matched to an area (matched_df) 
		and a calibration concentration dataframe and matches these two based on library_id
		'''
		standards_melted = pd.melt(standards, id_vars=['library_id'],value_vars=list(standards.keys()[1:]))
		standards_melted.columns = ['library_id','key','cal_conc']
		
		return_df = pd.merge(compiled.reset_index(),standards_melted,how='left',on=['library_id','key'])
		return return_df.dropna(subset=['cal_conc'])
		return return_df

	def _stdcurves(self,compiled,standards):
		'''
		takes in compiled dataframe of species compiled with areas and a standards df
		and calculates the corresponding RF
		s
		this is only for cases where each molecule has a calibration curve i.e. tic and/or fid
		'''
		matched_cal_conc = self._match_cal_conc(compiled, standards)
		b = (matched_cal_conc.groupby('library_id')
							 .apply(lambda a: linregress(a.area,a.cal_conc))
							 .apply(pd.Series)
							 .reset_index())
		b.columns = ['library_id','responsefactor','intercept','rvalue','pvalue','stderr']
		
		d = pd.DataFrame({'max':matched_cal_conc.groupby('library_id')['area'].max(),
						'min':matched_cal_conc.groupby('library_id')['area'].min()}).reset_index()
		return pd.merge(b,d,on='library_id')
		# return matched_cal_conc

	def _concentrations(self,compiled,stdcurves):
		'''
		this  function takes a dataframe which contains species matched to an area (compiled) 
		and a calibration curve dataframe (stdcurves)
		
		it uses these values to calculate the concentration using the slope (responsefactors) and intercept
		'''
		def conc_cal(x):
			conc = (x['area']*x['responsefactor']+x['intercept'] if x['area']*x['responsefactor']+x['intercept']>0 else np.nan)
			return conc
	
		# calculate concentration of species
		compiled = compiled.reset_index()
		return_df = pd.merge(compiled,stdcurves,on='library_id',how='outer')
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
		return_df.drop(['totals_a','responsefactor','intercept','max','min'],1,inplace=True)
		
		return return_df.set_index('key')

	def _concentrations_exp(self,concentrations,standards):
		std_keys = list(standards.keys())[1:]
		conc_df = concentrations.reset_index()
		return conc_df[-conc_df['key'].isin(std_keys)].set_index('key')

	def _concentrations_std(self,concentrations,standards):
		std_keys = list(standards.keys())[1:]
		conc_df = concentrations.reset_index()
		return conc_df[conc_df['key'].isin(std_keys)].set_index('key')