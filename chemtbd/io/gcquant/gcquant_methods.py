import pandas as pd
import warnings
warnings.filterwarnings("ignore")

class GCMethods(object):
	def __init__(self):
		pass
	def _find_match(self,x, Y):
		''' find index of argmin lambda(x,Y)
        '''
		score = lambda y: (x - y)**2
		return Y.apply(score).idxmin()

	def _rt_match(self,lib_row, rt):
		''' find closest rt
        '''
		x, i = lib_row.rt, lib_row.name
		return self._find_match(x, rt[i:])

	def _matchiter(self,lib,area):
		'''match area on rt from single df
		'''
		xi = lib.apply(self._rt_match, rt=area.rt.sort_values(), axis=1)
		lib['area'] = area.area[xi].values
		return lib.set_index('key')
        
	def _matchlib2area(self,lib,area):
		'''match area from many dataframes
		'''
		lib_grouped = (lib.groupby(lib.index))
		area_grouped = (area.groupby(area.index))
		returndf = lib_grouped.apply(lambda x: self._matchiter(x.reset_index(),area_grouped.get_group(x.name).reset_index()))    
		return returndf

	def match_cal_conc(matcheddf, standards):
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

	def _match_cal_conc(self,aligned, standards):
	    '''
	    this  function takes a dataframe which contains species matched to an area (matched_df) 
	    and a calibration concentration dataframe and matches these two based on library_id
	    '''
	    standards_melted = pd.melt(standards, id_vars=['library_id'],value_vars=list(standards.keys()[1:]))
	    standards_melted.columns = ['library_id','key','cal_conc']
	    
	    return_df = pd.merge(aligned.reset_index(),standards_melted,how='left',on=['library_id','key'])
	    return return_df.dropna(subset=['cal_conc'])
	    return return_df