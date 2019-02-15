
import time

from intervaltree import IntervalTree

class Target(object):
    ''' collect chains for a single target chromosome
    '''
    def __init__(self):
        self.tree = IntervalTree()
        self.target_id = None
    
    def add_chain(self, chain):
        ''' add Intervals from a Chain object to the current target
        '''
        if self.target_id is None:
            self.target_id = chain.target_id
        assert self.target_id == chain.target_id
        
        for x in chain.intervals:
            self.tree.add(x)
        
    def __getitem__(self, pos):
        results = []
        for region in self.tree[pos]:
            data = region.data
            offset = pos - region.begin
            remapped = data.begin + offset
            if data.strand == '-':
                remapped = data.size - remapped - 1
            
            results.append((data.id, remapped, data.strand))
        
        return results
