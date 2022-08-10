# cython: language_level=3, boundscheck=False, emit_linenums=True

import os

from libcpp.string cimport string
from libcpp.vector cimport vector
from libcpp.map cimport map
from libcpp cimport bool
from cython.operator cimport dereference as deref

cdef extern from 'target.h' namespace 'liftover':
  cdef struct Match:
    string contig
    long pos
    bool fwd_strand

  cdef cppclass Target:
    Target() except +
    vector[Match] query(int)
    vector[Match] operator[](int)

cdef extern from 'chain_file.h' namespace 'liftover':
  map[string, Target] open_chainfile(string)

cdef class PyTarget():
    ''' class to hold cpp object for nucleotide position queries
    '''
    cdef Target thisptr
    cdef Match x
    cdef set_target(self, Target target):
        self.thisptr = target
    def __getitem__(self, long pos):
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

cdef class ChainFile():
    cdef string target_id
    cdef string query_id
    cdef targets
    def __cinit__(self, path, target, query):
        if not os.path.exists(path):
            raise ValueError('cannot find chainfile at "{}"'.format(path))
        self.target_id = target.encode('utf8')
        self.query_id = query.encode('utf8')

        # open the chainfile and move the chromosome mappings to a python
        # dictionary, as accessing this is much faster than converting the
        # c++ Target object each time we query in a chromosome.
        path = path.encode('utf8')
        self.targets = {}
        cdef map[string, Target] chainfile = open_chainfile(path)
        for x in chainfile:
            chrom = x.first.decode('utf8')
            tgt = PyTarget()
            tgt.set_target(x.second)
            self.targets[chrom] = tgt

    def __repr__(self):
        return f'liftover({self.target_id}->{self.query_id})'

    def __getitem__(self, contig):
        ''' get the Target object for a target chromosome
        '''
        try:
            return self.targets[contig]
        except KeyError:
            return self.targets[f'chr{contig}']

    def query(self, chrom, long pos):
        '''  find the coordinate matches for a genome position
        '''
        return self[chrom][pos]

    def convert_coordinate(self, chrom, long pos):
        '''  find the coordinate matches for a genome position (from pyliftover API)
        '''
        return self[chrom][pos]

    def keys(self):
        ''' get contig names which can be converted from
        '''
        return self.targets.keys()