# cython: language_level=3, boundscheck=False, emit_linenums=True

import os

from libc.stdint cimport int64_t
from libcpp.string cimport string
from libcpp.vector cimport vector
from libcpp.map cimport map
from libcpp cimport bool
from cython.operator cimport dereference as deref

cdef extern from 'target.h' namespace 'liftover':
  cdef struct Match:
    string contig
    int64_t pos
    bool fwd_strand

  cdef cppclass Target:
    Target() except +
    vector[Match] query(int)
    vector[Match] operator[](int)

cdef extern from 'chain_file.h' namespace 'liftover':
  map[string, Target] open_chainfile(string, bool) except+

cdef class PyTarget():
    ''' class to hold cpp object for nucleotide position queries
    '''
    cdef Target thisptr
    cdef Match x
    cdef set_target(self, Target target):
        self.thisptr = target
    def __getitem__(self, int64_t pos):
        cpp_matches = self.thisptr[pos]
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

cdef sanatize_prefix(str contig, bool target_prefixed):
    ''' if we can't find the contig, check if we need to fix the prefix.
    
    This is primarily for convenience when dealing with genome builds that omit
    a 'chr' prefix.
    '''
    cdef bool contig_prefixed = contig.startswith('chr')
    if contig_prefixed and target_prefixed:
        # both contig and targets use 'chr' prefix
        return contig
    elif not contig_prefixed and not target_prefixed:
        # neither contig nor targets use 'chr' prefix
        return contig
    elif contig_prefixed and not target_prefixed:
        # remove 'chr' prefix, since targets don't use it
        return contig[3:]
    elif not contig_prefixed and target_prefixed:
        # add 'chr' prefix, since targets use it
        return f'chr{contig}'
    else:
        raise ValueError('cannot sanatize contig')

cdef class ChainFile():
    cdef targets
    cdef str path
    cdef bool target_prefixed
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
        for x in chainfile:
            chrom = x.first.decode('utf8')
            tgt = PyTarget()
            tgt.set_target(x.second)
            self.targets[chrom] = tgt
        
        self.target_prefixed = chrom.startswith('chr')

    def __repr__(self):
        return f'ChainFile("{self.path}")'

    def __getitem__(self, str contig):
        ''' get the Target object for a target chromosome
        '''
        try:
            return self.targets[contig]
        except KeyError as err:
            contig = sanatize_prefix(contig, self.target_prefixed)
            if contig in self.targets:
                return self.targets[contig]
            else:
                return PyTarget()

    def query(self, chrom, int64_t pos):
        '''  find the coordinate matches for a genome position
        '''
        return self[chrom][pos]

    def convert_coordinate(self, chrom, int64_t pos):
        '''  find the coordinate matches for a genome position (from pyliftover API)
        '''
        return self[chrom][pos]

    def keys(self):
        ''' get contig names which can be converted from
        '''
        return self.targets.keys()