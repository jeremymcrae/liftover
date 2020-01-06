
from collections import namedtuple

from intervaltree import Interval

from liftover.header import ChainHeader

Mapped = namedtuple('Mapped', ['begin', 'end', 'id', 'strand', 'size'])

class Chain(object):
    def __init__(self, lines):
        ''' build a set of Intervals for mapping betwen coordinates
        '''
        header = ChainHeader(lines.pop(0))
        self.target_id = header.target_id
        self.intervals = []
        
        target = header.target_start
        query = header.query_start
        for line in lines:
            size, target_gap, query_gap = self.parse(line)
            
            i = Interval(target, target + size, data=Mapped(query, query + size,
                header.query_id, header.query_strand, header.query_size))
            self.intervals.append(i)
            
            target += size + target_gap
            query += size + query_gap
        
        assert target == header.target_end
        assert query == header.query_end
    
    def parse(self, line):
        ''' parse an alignment data line
        
        Args:
            line: an alignment data line e.g. '5000\t10\t5\n' or '5000\n'
                Most lines have 3 values (size, reference delta, query delta),
                but the final line has only one value (size).
        
        Returns:
            (size, delta_reference, delta_query) tuple. Last line's deltas = 0.
        '''
        try:
            size, delta_t, delta_q = line.strip('\n').split('\t')
            return int(size), int(delta_t), int(delta_q)
        except ValueError:
            return int(line.strip('\n')), 0, 0
