
from collections import defaultdict

from liftover.target import Target
from liftover.chain import Chain

class ChainFile(object):
    ''' open a chain file for coordinate conversion
    '''
    def __init__(self, handle, target, query):
        self.handle = handle
        self.target = target
        self.query = query
        self.chains = defaultdict(Target)
        for x in self:
            self.chains[x.target_id].add_chain(x)
    
    def __repr__(self):
        return 'liftover({}->{})'.format(self.target, self.query)
    def __iter__(self):
        return self
    def __next__(self):
        ''' get the text lines for a complete chain
        '''
        lines = []
        for line in self.handle:
            if line.startswith('#'):  # skip comment lines
                continue
            if line == '\n':  # end chain data at blank lines
                break
            lines.append(line)
        
        if lines == []:
            raise StopIteration
        
        return Chain(lines)
    
    def query(self, chrom, pos):
        '''  find the coordinate matches for a genome position
        '''
        return self[chrom][pos]
    
    def __getitem__(self, target):
        ''' get the Target object for a target chromosome
        '''
        prefixed = target.startswith('chr')
        target = target if prefixed else 'chr{}'.format(target)
        return self.chains[target]
