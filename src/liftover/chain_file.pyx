# cython: language_level=3, boundscheck=False, emit_linenums=True

import os

from cython.operator cimport dereference as deref, preincrement as inc
from libc.stdint cimport int64_t
from libcpp.string cimport string
from libcpp.vector cimport vector
from libcpp.map cimport map
from libcpp cimport bool

cdef extern from 'target.h' namespace 'liftover':
  cdef struct Match:
    string contig
    int64_t pos
    bool fwd_strand

  cdef cppclass Target:
    Target() except +
    vector[Match] query(int64_t)
    vector[Match] operator[](int64_t)
    void swap(Target &)

cdef extern from 'chain_file.h' namespace 'liftover':
  map[string, Target] open_chainfile(string, bool) except+

cdef class PyTarget():
    ''' class to hold cpp object for nucleotide position queries
    '''
    cdef Target thisptr
    cdef set_target(self, Target & target):
        self.thisptr.swap(target)
    def __getitem__(self, int64_t pos):
        cpp_matches = self.thisptr[pos]
        # optimization for the most common case
        if cpp_matches.size() == 1:
            x = cpp_matches[0]
            contig = x.contig.decode('utf8')
            strand = '+' if x.fwd_strand else '-'
            return [(contig, x.pos, strand)]

        matches = []
        for x in cpp_matches:
            contig = x.contig.decode('utf8')
            strand = '+' if x.fwd_strand else '-'
            matches.append((contig, x.pos, strand))
        return matches

cdef class ChainFile():
    cdef targets
    cdef str path
    cdef PyTarget missing_target
    def __cinit__(self, path, target: str='', query: str='', one_based: bool=False):
        ''' 
        open the chain file for lifting coordinates
        
        Args:
            path: path to chain file
            target: ID for target genome (deprecated, but don't drop since other 
                    code might already use this argument).
            query: ID for query genome (deprecated, but as above)
            one_based: whether query coordinates are one-based
        '''
        self.path = str(path)

        # open the chainfile and move the chromosome mappings to a python
        # dictionary, as accessing this is much faster than converting the
        # c++ Target object each time we query in a chromosome.
        self.targets = {}
        cdef map[string, Target] chainfile = open_chainfile(self.path.encode('utf8'), one_based)
        cdef map[string, Target].iterator it = chainfile.begin()
        cdef PyTarget tgt
        while it != chainfile.end():
            chrom = deref(it).first.decode('utf8')
            tgt = PyTarget()
            tgt.set_target(deref(it).second)
            self.targets[chrom] = tgt
            inc(it)
        
        self.missing_target = PyTarget()

    def __repr__(self):
        return f'ChainFile("{self.path}")'

    def __getitem__(self, str contig):
        ''' get the Target object for a target chromosome
        '''
        try:
            return self.targets[contig]
        except KeyError:
            alt = contig[3:] if contig.startswith('chr') else f'chr{contig}'
            return self.targets.get(alt, self.missing_target)

    def query(self, chrom, int64_t pos):
        '''  find the coordinate matches for a genome position
        '''
        return self[chrom][pos]

    def convert_coordinate(self, chrom, int64_t pos):
        '''  find the coordinate matches for a genome position (from pyliftover API)
        '''
        return self[chrom][pos]

    def __contains__(self, contig):
        ''' check whether a contig is present in the chain file
        '''
        if not isinstance(contig, str):
            return False
        if contig in self.targets:
            return True
        alt = contig[3:] if contig.startswith('chr') else f'chr{contig}'
        return alt in self.targets

    def __iter__(self):
        ''' iterate over contig names
        '''
        return iter(self.targets)

    def __len__(self):
        ''' return the number of contigs in the chain file
        '''
        return len(self.targets)

    def keys(self):
        ''' get contig names which can be converted from
        '''
        return self.targets.keys()

    def values(self):
        ''' get Target objects for each contig
        '''
        return self.targets.values()

    def items(self):
        ''' get (contig, Target) pairs
        '''
        return self.targets.items()