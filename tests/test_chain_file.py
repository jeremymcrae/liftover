
import gzip
import unittest
from pathlib import Path

from liftover import get_lifter


class TestChainFile(unittest.TestCase):
    ''' unittest the lifting operations
    '''
    @classmethod
    def setUpClass(self):
        self.lifter = get_lifter('hg19', 'hg38')

    def test_points(self):
        ''' compare to conversions found using UCSC liftover webtool

        There is a file of test cases in the test/data folder, which has the
        boundaries in the hg19 to hg38 chain file. For each region in the chain
        file these sites were included:
            region start - 1 (one base upstream of the region)
            region start
            region start + 4 (a point inside the region)
            region end
            region end + 1 (one base downstream of the region)
        '''
        # open test coordinates
        path = Path(__file__).parent / 'data' / 'hg19ToHg38.testcoords.txt.gz'
        with gzip.open(path, 'rt') as handle:
            for line in handle:
                chrom, pos, lft_chrom, lft_pos = line.strip('\n').split('\t')
                pos, lft_pos = int(pos), int(lft_pos)

                lifted = self.lifter[chrom][pos]
                if lft_chrom == '-':
                    self.assertEqual(lifted, [])
                else:
                    self.assertTrue(any((lft_chrom, lft_pos) == x[:2] for x in lifted))
    
    def test_keys_attribute(self):
        ''' check the lifter object has a keys() method
        '''
        self.assertTrue('keys' in dir(self.lifter))
    
    def test_missing_contig(self):
        ''' check we handle missing contigs corectly
        '''
        target = self.lifter['chr1']
        missing_contig = 'chrjhsdjkhsdgf'
        assert missing_contig not in self.lifter.keys()
        
        # make sure if we access a contig that does not exist in the lifter 
        # object, it still returns a PyTarget object
        missing_target = self.lifter[missing_contig]
        self.assertIsInstance(missing_target, target.__class__)
        
        # and make sure the target object still returns a list
        matches = missing_target[1000000]
        self.assertIsInstance(matches, list)
    
    def test_wrong_prefix(self):
        ''' check we can find the same target, even if we lack the correct prefix
        '''
        target1 = self.lifter['chr1']
        target2 = self.lifter['1']
        self.assertIs(target1, target2)
    
    def test_fail_types(self):
        ''' check we raise type errors if we access the ChainFile with invalid types
        '''
        with self.assertRaises(TypeError):
            # can't use integers for contigs
            self.lifter[1]
        
        with self.assertRaises(TypeError):
            # can't use string for position
            self.lifter['chr1']['f']
