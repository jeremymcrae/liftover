import os
from typing import KeysView

class PyTarget:
    ''' class to hold cpp object for nucleotide position queries
    '''
    def __init__(self) -> None: ...
    def __getitem__(self, pos: int) -> list[tuple[str, int, str]]:
        ''' find the coordinate matches for a position on this contig

        each match is a (contig, position, strand) tuple, where strand is '+' or '-'
        '''
        ...

class ChainFile:
    ''' class for converting coordinates between genome builds
    '''
    def __init__(
        self,
        path: str | os.PathLike[str],
        target: str = ...,
        query: str = ...,
        one_based: bool = ...,
    ) -> None:
        '''
        open the chain file for lifting coordinates

        Args:
            path: path to chain file
            target: ID for target genome (deprecated, but don't drop since other
                    code might already use this argument).
            query: ID for query genome (deprecated, but as above)
            one_based: whether query coordinates are one-based
        '''
        ...
    def __repr__(self) -> str: ...
    def __getitem__(self, contig: str) -> PyTarget:
        ''' get the Target object for a target chromosome
        '''
        ...
    def query(self, chrom: str, pos: int) -> list[Match]:
        ''' find the coordinate matches for a genome position
        '''
        ...
    def convert_coordinate(self, chrom: str, pos: int) -> list[Match]:
        ''' find the coordinate matches for a genome position (from pyliftover API)
        '''
        ...
    def keys(self) -> KeysView[str]:
        ''' get contig names which can be converted from
        '''
        ...
