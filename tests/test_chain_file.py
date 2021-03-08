
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
