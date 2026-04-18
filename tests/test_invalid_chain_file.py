
import gzip
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

        with tempfile.NamedTemporaryFile(suffix='.chain.gz') as tmp_file:
            # create a temporary file with invalid content
            with gzip.open(tmp_file.name, 'wt') as handle:
                handle.write('invalid content')

            with self.assertRaises(ValueError):
                ChainFile(tmp_file.name)
    
    def test_invalid_chain_file_incomplete(self):
        ''' check we raise an error when parsing an incomplete chain file
        '''

        lines = ['chain 21270171362 chr1 249250621 + 10000 249233096 chr1 247249719 + 0 247199719 2\n',
                 '619 137 0\n',
                 '166661 50000 50000\n',
                 '\n']

        with tempfile.NamedTemporaryFile(suffix='.chain.gz') as tmp_file:
            # create a temporary file with invalid content
            with gzip.open(tmp_file.name, 'wt') as handle:
                handle.writelines(lines)
            
            with self.assertRaises(ValueError) as context:
                ChainFile(tmp_file.name)
            self.assertTrue('target end does not match expectations' in context.exception.args[0])
    
    def test_invalid_chain_file_wrong_header(self):
        ''' check we raise an error when parsing an incomplete chain file
        '''

        lines = ['chain 21270171362 chr1 249250621 + 10000 249233096 chr1 247249719 + 0 247199719\n',
                 '619 137 0\n',
                 '166661 50000 50000\n',
                 '\n']

        with tempfile.NamedTemporaryFile(suffix='.chain.gz') as tmp_file:
            # create a temporary file with invalid content
            with gzip.open(tmp_file.name, 'wt') as handle:
                handle.writelines(lines)
            
            with self.assertRaises(ValueError) as context:
                ChainFile(tmp_file.name)
            self.assertTrue('invalid header line' in context.exception.args[0])

    def test_invalid_chain_file_shortline(self):
        ''' check we raise an error when parsing a truncated chain file line
        '''

        lines = ['chain 21270171362 chr1 249250621 + 10000 249233096 chr1 247249719 + 0 247199719 2\n',
                 '619 137 0\n',
                 '166661 50000\n',
                 '\n']

        with tempfile.NamedTemporaryFile(suffix='.chain.gz') as tmp_file:
            # create a temporary file with invalid content
            with gzip.open(tmp_file.name, 'wt') as handle:
                handle.writelines(lines)

            with self.assertRaises(ValueError) as context:
                ChainFile(tmp_file.name)
            self.assertTrue('invalid alignment line' in context.exception.args[0])

    def test_chain_file_minimal(self):
        ''' check a minimal chain file is fine
        '''
        
        lines = ['chain 0 chr1 10 + 0 10 chr1 10 + 10 30 2\n',
                 '5 0 5\n',
                 '5 0 5\n',
                 '\n']

        with tempfile.NamedTemporaryFile(suffix='.chain.gz') as tmp_file:
            # create a temporary file with valid content
            with gzip.open(tmp_file.name, 'wt') as handle:
                handle.writelines(lines)
            
            chain = ChainFile(tmp_file.name)
            mapped = chain['chr1'][6]
            self.assertEqual(mapped[0][1], 21)

    def test_chain_file_missing_newline(self):
        ''' check a chain file is fine without a final newline
        '''
        
        lines = ['chain 0 chr1 10 + 0 10 chr1 10 + 10 30 2\n',
                 '5 0 5\n',
                 '5 0 5\n',
                 ]

        with tempfile.NamedTemporaryFile(suffix='.chain.gz') as tmp_file:
            # create a temporary file with valid content
            with gzip.open(tmp_file.name, 'wt') as handle:
                handle.writelines(lines)
            
            chain = ChainFile(tmp_file.name)
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

        with tempfile.NamedTemporaryFile(suffix='.chain.gz') as tmp_file:
            # create a temporary file with valid content
            with gzip.open(tmp_file.name, 'wt') as handle:
                handle.writelines(lines)
            
            chain = ChainFile(tmp_file.name)
            mapped = chain['chr1'][6]
            self.assertEqual(mapped[0][1], 21)

    def test_chain_file_longline(self):
        ''' check slightly long chain file lines can be parsed
        '''

        lines = ['chain 0 chr1 10 + 0 10 chr1 10 + 10 30 2\n',
                 '5 0 5\n',
                 '5 0 5 5\n',
                 '\n']

        with tempfile.NamedTemporaryFile(suffix='.chain.gz') as tmp_file:
            # create a temporary file with mostly valid content
            with gzip.open(tmp_file.name, 'wt') as handle:
                handle.writelines(lines)

            chain = ChainFile(tmp_file.name)

    def test_invalid_chain_file_text_in_number(self):
        ''' check chain file lines with text in a number field fail
        '''

        lines = ['chain 21270171362 chr1 249250621 + 10000 249233096 chr1 247249719 + 0 247199719 2\n',
                 's619 137 0\n',
                 '166661 50000 50000 50000\n',
                 '\n']

        with tempfile.NamedTemporaryFile(suffix='.chain.gz') as tmp_file:
            # create a temporary file with invalid content
            with gzip.open(tmp_file.name, 'wt') as handle:
                handle.writelines(lines)
            
            with self.assertRaises(ValueError) as context:
                ChainFile(tmp_file.name)
            self.assertTrue('invalid alignment line' in context.exception.args[0])

    def test_chain_file_large_number(self):
        ''' check chain file lines with extremely large numbers are fine
        '''

        large = 2**63 - 50
        lines = [f'chain 0 chr1 {large} + 0 {large} chr1 {large} + 10 {large + 20} 2\n',
                 '5 0 5\n',
                 f'{large - 5} 0 5\n',
                 '\n']

        with tempfile.NamedTemporaryFile(suffix='.chain.gz') as tmp_file:
            # create a temporary file with valid content
            with gzip.open(tmp_file.name, 'wt') as handle:
                handle.writelines(lines)
            
            chain = ChainFile(tmp_file.name)
            mapped = chain['chr1'][large - 50]
            self.assertEqual(mapped[0][1], large - 40 + 5)

