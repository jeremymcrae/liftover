# cython: language_level=3, boundscheck=False, emit_linenums=True

import os

from cpython.bool cimport PyBool_Check
from cpython.long cimport PyLong_AsLongLong, PyLong_CheckExact
from cpython.number cimport PyNumber_Index
from cython.operator cimport dereference as deref, preincrement as inc
from libc.stdint cimport int64_t, uint32_t
from libcpp.string cimport string
from libcpp.vector cimport vector
from libcpp.map cimport map
from libcpp cimport bool

cdef extern from 'target.h' namespace 'liftover':
  cdef struct Match:
    int64_t pos
    uint32_t query_id_idx
    bool fwd_strand

  cdef cppclass MatchBuffer:
    Match inline_matches[4]
    size_t size() const
    const Match & operator[](size_t) const

  cdef cppclass Target:
    Target() except +
    void query(int64_t, MatchBuffer &) const
    void swap(Target &)

cdef extern from 'chain_file.h' namespace 'liftover':
  cdef struct ChainFileResult:
    map[string, Target] targets
    vector[string] query_names

  ChainFileResult open_chainfile(int &, const string &, bool) except+

cdef inline int64_t _as_coord(object pos) except? -1:
    if PyLong_CheckExact(pos):
        return PyLong_AsLongLong(pos)
    if PyBool_Check(pos):
        raise TypeError('position must be an integer, not bool')
    return PyLong_AsLongLong(PyNumber_Index(pos))

cdef class PyTarget():
    ''' class to hold cpp object for nucleotide position queries
    '''
    cdef Target thisptr
    cdef list query_contigs
    cdef str strand_plus
    cdef str strand_minus

    def __cinit__(self):
        self.strand_plus = '+'
        self.strand_minus = '-'
        self.query_contigs = []

    cdef set_target(self, Target & target, list query_contigs):
        self.thisptr.swap(target)
        self.query_contigs = query_contigs

    cdef list query_fast(self, int64_t pos):
        cdef MatchBuffer cpp_matches
        self.thisptr.query(pos, cpp_matches)
        cdef size_t n = cpp_matches.size()
        cdef Match x
        # optimization for the most common cases
        if n == 1:
            x = cpp_matches.inline_matches[0]
            return [(<str>self.query_contigs[x.query_id_idx], x.pos, self.strand_plus if x.fwd_strand else self.strand_minus)]

        if n == 0:
            return []

        cdef list matches = []
        cdef size_t i
        for i in range(n):
            x = cpp_matches[i]
            matches.append((<str>self.query_contigs[x.query_id_idx], x.pos, self.strand_plus if x.fwd_strand else self.strand_minus))
        return matches

    def __getitem__(self, pos):
        return self.query_fast(_as_coord(pos))

cdef class ChainFile():
    '''ChainFile(path, target='', query='', one_based=False)
--

class for converting coordinates between genome builds
    '''
    cdef dict targets
    cdef dict lookup
    cdef str path
    cdef PyTarget missing_target
    cdef list query_contigs

    def __cinit__(self, path, target: str='', query: str='', one_based: bool=False):
        raw_path = os.fspath(path)
        if not isinstance(raw_path, str):
            raise TypeError(f'expected str or os.PathLike[str] for path, got {type(raw_path).__name__}')
        self.path = os.path.expanduser(raw_path)

        if os.path.isdir(self.path):
            raise ValueError(f'cannot open directory as chain file: {self.path}')

        cdef int fd
        try:
            fd = os.open(self.path, os.O_RDONLY | getattr(os, 'O_BINARY', 0))
        except OSError as e:
            raise ValueError(f'cannot open chain file at {self.path}: {e}') from e

        # open the chainfile and move the chromosome mappings to a python
        # dictionary, as accessing this is much faster than converting the
        # c++ Target object each time we query in a chromosome.
        self.targets = {}
        self.lookup = {}
        cdef ChainFileResult res
        try:
            res = open_chainfile(fd, self.path.encode('utf8'), one_based)
        finally:
            if fd >= 0:
                os.close(fd)
        
        # Pre-decode unique query chromosome names into Python str objects once
        self.query_contigs = [name.decode('utf8') for name in res.query_names]

        cdef map[string, Target].iterator it = res.targets.begin()
        cdef PyTarget tgt
        cdef str chrom
        while it != res.targets.end():
            chrom = deref(it).first.decode('utf8')
            tgt = PyTarget()
            tgt.set_target(deref(it).second, self.query_contigs)
            self.targets[chrom] = tgt
            inc(it)

        # Build fast lookup dictionary: exact keys first
        for chrom, tgt in self.targets.items():
            self.lookup[chrom] = tgt

        # Add alternate prefix keys (e.g. '1' -> 'chr1' target, or 'chr1' -> '1' target)
        for chrom, tgt in self.targets.items():
            alt = chrom[3:] if chrom.startswith('chr') else f'chr{chrom}'
            if alt not in self.lookup:
                self.lookup[alt] = tgt
        
        self.missing_target = PyTarget()
        self.missing_target.query_contigs = self.query_contigs

    def __init__(self, path, target: str='', query: str='', one_based: bool=False):
        ''' open the chain file for lifting coordinates

        Args:
            path: path to chain file
            target: ID for target genome (deprecated, but don't drop since other
                    code might already use this argument).
            query: ID for query genome (deprecated, but as above)
            one_based: whether query coordinates are one-based
        '''
        pass

    def __repr__(self):
        return f'ChainFile("{self.path}")'

    def __getitem__(self, str contig):
        ''' get the Target object for a target chromosome
        '''
        return self.lookup.get(contig, self.missing_target)

    def query(self, str chrom, pos):
        '''  find the coordinate matches for a genome position
        '''
        cdef int64_t c_pos = _as_coord(pos)
        cdef PyTarget tgt = <PyTarget>self.lookup.get(chrom)
        if tgt is not None:
            return tgt.query_fast(c_pos)
        return []

    def convert_coordinate(self, str chrom, pos):
        '''  find the coordinate matches for a genome position (from pyliftover API)
        '''
        cdef int64_t c_pos = _as_coord(pos)
        cdef PyTarget tgt = <PyTarget>self.lookup.get(chrom)
        if tgt is not None:
            return tgt.query_fast(c_pos)
        return []

    def __contains__(self, contig):
        ''' check whether a contig is present in the chain file
        '''
        if not isinstance(contig, str):
            return False
        return contig in self.lookup

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