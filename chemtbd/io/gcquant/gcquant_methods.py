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
		area_grouped = (area.groupby(area.index))
		returndf = lib_grouped.apply(lambda x: self._matchiter(x.reset_index(),area_grouped.get_group(x.name).reset_index()))    
		return returndf