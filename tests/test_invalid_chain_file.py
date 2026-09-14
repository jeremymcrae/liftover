
import gzip
import os
import unittest
from pathlib import Path
import tempfile

from liftover import ChainFile

class TestChainFile(unittest.TestCase):
    ''' check for failures when parsing invalid chain files
    '''
    
    def test_invalid_chain_file(self):
        ''' check we raise an error when parsing an invalid chain file
        '''

        with tempfile.TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, 'test.chain.gz')
            # create a temporary file with invalid content
            with gzip.open(path, 'wt') as handle:
                handle.write('invalid content')

            with self.assertRaises(ValueError):
                ChainFile(path)
    
    def test_invalid_chain_file_incomplete(self):
        ''' check we raise an error when parsing an incomplete chain file
        '''

        lines = ['chain 21270171362 chr1 249250621 + 10000 249233096 chr1 247249719 + 0 247199719 2\n',
                 '619 137 0\n',
                 '166661 50000 50000\n',
                 '\n']

        with tempfile.TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, 'test.chain.gz')
            # create a temporary file with invalid content
            with gzip.open(path, 'wt') as handle:
                handle.writelines(lines)
            
            with self.assertRaises(ValueError) as context:
                ChainFile(path)
            self.assertTrue('target end does not match expectations' in context.exception.args[0])
    
    def test_invalid_chain_file_wrong_header(self):
        ''' check we raise an error when parsing an incomplete chain file
        '''

        lines = ['chain 21270171362 chr1 249250621 + 10000 249233096 chr1 247249719 + 0 247199719\n',
                 '619 137 0\n',
                 '166661 50000 50000\n',
                 '\n']

        with tempfile.TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, 'test.chain.gz')
            # create a temporary file with invalid content
            with gzip.open(path, 'wt') as handle:
                handle.writelines(lines)
            
            with self.assertRaises(ValueError) as context:
                ChainFile(path)
            self.assertTrue('invalid header line' in context.exception.args[0])

    def test_invalid_chain_file_shortline(self):
        ''' check we raise an error when parsing a truncated chain file line
        '''

        lines = ['chain 21270171362 chr1 249250621 + 10000 249233096 chr1 247249719 + 0 247199719 2\n',
                 '619 137 0\n',
                 '166661 50000\n',
                 '\n']

        with tempfile.TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, 'test.chain.gz')
            # create a temporary file with invalid content
            with gzip.open(path, 'wt') as handle:
                handle.writelines(lines)

            with self.assertRaises(ValueError) as context:
                ChainFile(path)
            self.assertTrue('invalid alignment line' in context.exception.args[0])

    def test_invalid_chain_file_alignment_before_header(self):
        ''' check we raise an error when alignment lines appear before any chain header
        '''

        lines = ['5 0 5\n',
                 'chain 0 chr1 10 + 0 10 chr1 10 + 10 30 2\n',
                 '5 0 5\n',
                 '5 0 5\n',
                 '\n']

        with tempfile.TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, 'test.chain.gz')
            with gzip.open(path, 'wt') as handle:
                handle.writelines(lines)

            with self.assertRaises(ValueError) as context:
                ChainFile(path)
            self.assertTrue('before chain header' in context.exception.args[0])

    def test_chain_file_minimal(self):
        ''' check a minimal chain file is fine
        '''
        
        lines = ['chain 0 chr1 10 + 0 10 chr1 10 + 10 30 2\n',
                 '5 0 5\n',
                 '5 0 5\n',
                 '\n']

        with tempfile.TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, 'test.chain.gz')
            # create a temporary file with valid content
            with gzip.open(path, 'wt') as handle:
                handle.writelines(lines)
            
            chain = ChainFile(path)
            mapped = chain['chr1'][6]
            self.assertEqual(mapped[0][1], 21)

    def test_chain_file_missing_newline(self):
        ''' check a chain file is fine without a final newline
        '''
        
        lines = ['chain 0 chr1 10 + 0 10 chr1 10 + 10 30 2\n',
                 '5 0 5\n',
                 '5 0 5\n',
                 ]

        with tempfile.TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, 'test.chain.gz')
            # create a temporary file with valid content
            with gzip.open(path, 'wt') as handle:
                handle.writelines(lines)
            
            chain = ChainFile(path)
            mapped = chain['chr1'][6]
            self.assertEqual(mapped[0][1], 21)

    def test_chain_file_missing_commentline(self):
        ''' check a chain file containing comment lines is fine
        '''
        
        lines = ['chain 0 chr1 10 + 0 10 chr1 10 + 10 30 2\n',
                 '#5 0 5\n',
                 '5 0 5\n',
                 '5 0 5\n',
                 ]

        with tempfile.TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, 'test.chain.gz')
            # create a temporary file with valid content
            with gzip.open(path, 'wt') as handle:
                handle.writelines(lines)
            
            chain = ChainFile(path)
            mapped = chain['chr1'][6]
            self.assertEqual(mapped[0][1], 21)

    def test_chain_file_no_blank_line_between_chains(self):
        ''' check multiple chains without separating blank line are all loaded
        '''

        lines = ['chain 0 chr1 10 + 0 10 chr1 10 + 10 30 1\n',
                 '5 0 5\n',
                 '5 0 5\n',
                 'chain 0 chr2 10 + 0 10 chr2 10 + 10 30 2\n',
                 '5 0 5\n',
                 '5 0 5\n',
                 '\n']

        with tempfile.TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, 'test.chain.gz')
            with gzip.open(path, 'wt') as handle:
                handle.writelines(lines)

            chain = ChainFile(path)
            self.assertEqual(sorted(chain.keys()), ['chr1', 'chr2'])
            self.assertEqual(chain['chr1'][6][0][1], 21)
            self.assertEqual(chain['chr2'][6][0][1], 21)

    def test_chain_file_longline(self):
        ''' check slightly long chain file lines can be parsed
        '''

        lines = ['chain 0 chr1 10 + 0 10 chr1 10 + 10 30 2\n',
                 '5 0 5\n',
                 '5 0 5 5\n',
                 '\n']

        with tempfile.TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, 'test.chain.gz')
            # create a temporary file with mostly valid content
            with gzip.open(path, 'wt') as handle:
                handle.writelines(lines)

            chain = ChainFile(path)

    def test_invalid_chain_file_text_in_number(self):
        ''' check chain file lines with text in a number field fail
        '''

        lines = ['chain 21270171362 chr1 249250621 + 10000 249233096 chr1 247249719 + 0 247199719 2\n',
                 's619 137 0\n',
                 '166661 50000 50000 50000\n',
                 '\n']

        with tempfile.TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, 'test.chain.gz')
            # create a temporary file with invalid content
            with gzip.open(path, 'wt') as handle:
                handle.writelines(lines)
            
            with self.assertRaises(ValueError) as context:
                ChainFile(path)
            self.assertTrue('invalid alignment line' in context.exception.args[0])

    def test_chain_file_large_number(self):
        ''' check chain file lines with extremely large numbers are fine
        '''

        large = 2**63 - 50
        lines = [f'chain 0 chr1 {large} + 0 {large} chr1 {large} + 10 {large + 20} 2\n',
                 '5 0 5\n',
                 f'{large - 5} 0 5\n',
                 '\n']

        with tempfile.TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, 'test.chain.gz')
            # create a temporary file with valid content
            with gzip.open(path, 'wt') as handle:
                handle.writelines(lines)
            
            chain = ChainFile(path)
            mapped = chain['chr1'][large - 50]
            self.assertEqual(mapped[0][1], large - 40 + 5)

    def test_invalid_chain_file_header_overflow(self):
        ''' check header number exceeding 64-bit integer raises ValueError
        '''
        large = 2**64
        lines = [f'chain 0 chr1 {large} + 0 10 chr1 {large} + 0 10 2\n',
                 '10\n',
                 '\n']

        with tempfile.TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, 'test.chain.gz')
            with gzip.open(path, 'wt') as handle:
                handle.writelines(lines)

            with self.assertRaises(ValueError) as context:
                ChainFile(path)
            self.assertTrue('invalid header line' in context.exception.args[0])

    def test_invalid_chain_file_header_text_in_number(self):
        ''' check header with letters in numeric field raises ValueError
        '''
        lines = ['chain 21270171362 chr1 249250621abc + 10 20 chr1 247249719 + 0 10 2\n',
                 '10\n',
                 '\n']

        with tempfile.TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, 'test.chain.gz')
            with gzip.open(path, 'wt') as handle:
                handle.writelines(lines)

            with self.assertRaises(ValueError) as context:
                ChainFile(path)
            self.assertTrue('invalid header line' in context.exception.args[0])

    def test_invalid_chain_file_header_negative_coord(self):
        ''' check header with negative coordinate raises ValueError
        '''
        lines = ['chain 21270171362 chr1 249250621 + -10 20 chr1 247249719 + 0 10 2\n',
                 '10\n',
                 '\n']

        with tempfile.TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, 'test.chain.gz')
            with gzip.open(path, 'wt') as handle:
                handle.writelines(lines)

            with self.assertRaises(ValueError) as context:
                ChainFile(path)
            self.assertTrue('invalid header line' in context.exception.args[0])

    def test_invalid_chain_file_alignment_overflow(self):
        ''' check alignment line number exceeding 64-bit integer raises ValueError
        '''
        large = 2**64
        lines = ['chain 0 chr1 10 + 0 10 chr1 10 + 0 10 2\n',
                 f'{large} 0 0\n',
                 '\n']

        with tempfile.TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, 'test.chain.gz')
            with gzip.open(path, 'wt') as handle:
                handle.writelines(lines)

            with self.assertRaises(ValueError) as context:
                ChainFile(path)
            self.assertTrue('invalid alignment line' in context.exception.args[0])

    def test_invalid_chain_file_negative_size(self):
        ''' check alignment line with negative size raises ValueError
        '''
        lines = ['chain 0 chr1 10 + 0 10 chr1 10 + 0 10 2\n',
                 '-5 0 0\n',
                 '\n']

        with tempfile.TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, 'test.chain.gz')
            with gzip.open(path, 'wt') as handle:
                handle.writelines(lines)

            with self.assertRaises(ValueError) as context:
                ChainFile(path)
            self.assertTrue('invalid alignment line' in context.exception.args[0])

    def test_invalid_chain_file_negative_gap(self):
        ''' check alignment line with negative gap raises ValueError
        '''
        lines = ['chain 0 chr1 10 + 0 10 chr1 10 + 0 10 2\n',
                 '5 -1 0\n',
                 '\n']

        with tempfile.TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, 'test.chain.gz')
            with gzip.open(path, 'wt') as handle:
                handle.writelines(lines)

            with self.assertRaises(ValueError) as context:
                ChainFile(path)
            self.assertTrue('invalid alignment line' in context.exception.args[0])

    def test_invalid_chain_file_zero_size(self):
        ''' check alignment line with zero size raises ValueError
        '''
        lines = ['chain 0 chr1 10 + 0 10 chr1 10 + 0 10 2\n',
                 '0 5 5\n',
                 '\n']

        with tempfile.TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, 'test.chain.gz')
            with gzip.open(path, 'wt') as handle:
                handle.writelines(lines)

            with self.assertRaises(ValueError) as context:
                ChainFile(path)
            self.assertTrue('invalid alignment line' in context.exception.args[0])

    def test_chain_file_trailing_whitespace_final_line(self):
        ''' check alignment line with trailing whitespace on final line is accepted
        '''
        lines = ['chain 0 chr1 10 + 0 10 chr1 30 + 10 30 2\n',
                 '5 0 10\n',
                 '5 \n',
                 '\n']

        with tempfile.TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, 'test.chain.gz')
            with gzip.open(path, 'wt') as handle:
                handle.writelines(lines)

            chain = ChainFile(path)
            self.assertEqual(chain['chr1'][6][0][1], 26)

    def test_chain_file_header_multiple_spaces(self):
        ''' check header with runs of multiple spaces between fields is accepted
        '''
        lines = ['chain  0   chr1  10  +   0  10   chr1  30  +   10  30   2\n',
                 '5 0 10\n',
                 '5\n',
                 '\n']

        with tempfile.TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, 'test.chain.gz')
            with gzip.open(path, 'wt') as handle:
                handle.writelines(lines)

            chain = ChainFile(path)
            self.assertEqual(chain['chr1'][6][0][1], 26)

    def test_chain_file_header_mixed_tabs_spaces(self):
        ''' check header with mixed tabs and spaces between fields is accepted
        '''
        lines = ['chain\t0 chr1\t10 + 0\t10 chr1\t30 + 10\t30 2\n',
                 '5 0 10\n',
                 '5\n',
                 '\n']

        with tempfile.TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, 'test.chain.gz')
            with gzip.open(path, 'wt') as handle:
                handle.writelines(lines)

            chain = ChainFile(path)
            self.assertEqual(chain['chr1'][6][0][1], 26)

    def test_chain_file_header_trailing_whitespace(self):
        ''' check header with trailing whitespace is accepted
        '''
        lines = ['chain 0 chr1 10 + 0 10 chr1 30 + 10 30 2 \t \n',
                 '5 0 10\n',
                 '5\n',
                 '\n']

        with tempfile.TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, 'test.chain.gz')
            with gzip.open(path, 'wt') as handle:
                handle.writelines(lines)

            chain = ChainFile(path)
            self.assertEqual(chain['chr1'][6][0][1], 26)

    def test_invalid_chain_file_truncated_gzip(self):
        ''' check truncated gzip chain file raises ValueError
        '''
        lines = ['chain 0 chr1 1000 + 0 1000 chrA 1000 + 0 1000 1\n']
        for _ in range(100):
            lines.append('10 0 0\n')
        lines.append('10\n\n')

        with tempfile.TemporaryDirectory() as tmp_dir:
            valid_path = os.path.join(tmp_dir, 'valid.chain.gz')
            with gzip.open(valid_path, 'wt') as h:
                h.writelines(lines)

            with open(valid_path, 'rb') as f:
                data = f.read()
            trunc_path = os.path.join(tmp_dir, 'trunc.chain.gz')
            with open(trunc_path, 'wb') as h:
                h.write(data[:len(data) // 2])

            with self.assertRaises(ValueError):
                ChainFile(trunc_path)

    def test_invalid_chain_file_corrupt_gzip(self):
        ''' check corrupt gzip chain file raises ValueError
        '''
        lines = ['chain 0 chr1 1000 + 0 1000 chrA 1000 + 0 1000 1\n']
        for _ in range(100):
            lines.append('10 0 0\n')
        lines.append('10\n\n')

        with tempfile.TemporaryDirectory() as tmp_dir:
            valid_path = os.path.join(tmp_dir, 'valid.chain.gz')
            with gzip.open(valid_path, 'wt') as h:
                h.writelines(lines)

            with open(valid_path, 'rb') as f:
                data = f.read()
            corrupt_path = os.path.join(tmp_dir, 'corrupt.chain.gz')
            mid = len(data) // 2
            with open(corrupt_path, 'wb') as h:
                h.write(data[:mid] + b'corrupted_bytes_1234' + data[mid + 20:])

            with self.assertRaises(ValueError):
                ChainFile(corrupt_path)




