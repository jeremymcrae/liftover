
import gzip
import os
import tempfile
import unittest
from pathlib import Path

from liftover import get_lifter, ChainFile


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

    def test_mapping_interface(self):
        ''' check mapping protocol: in, iter, len, values, items
        '''
        # __contains__ with and without 'chr' prefix
        self.assertTrue('chr1' in self.lifter)
        self.assertTrue('1' in self.lifter)
        self.assertFalse('chrjhsdjkhsdgf' in self.lifter)
        self.assertFalse(123 in self.lifter)

        # __len__
        self.assertGreater(len(self.lifter), 0)
        self.assertEqual(len(self.lifter), len(self.lifter.keys()))

        # __iter__
        keys_from_iter = list(self.lifter)
        self.assertEqual(keys_from_iter, list(self.lifter.keys()))

        # values() and items()
        values = list(self.lifter.values())
        self.assertEqual(len(values), len(self.lifter))
        items = list(self.lifter.items())
        self.assertEqual(len(items), len(self.lifter))
        self.assertIs(items[0][1], self.lifter[items[0][0]])
    
    def test_missing_contig(self):
        ''' check we handle missing contigs corectly
        '''
        target = self.lifter['chr1']
        missing_contig = 'chrjhsdjkhsdgf'
        self.assertTrue(missing_contig not in self.lifter)
        self.assertTrue(missing_contig not in self.lifter.keys())
        
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

    def test_mixed_prefix(self):
        ''' check contig lookup works when chain file has mixed prefixes
        '''
        lines = [
            'chain 0 chr1 100 + 0 10 chrA 100 + 10 30 1\n',
            '5 0 5\n',
            '5 0 5\n',
            '\n',
            'chain 0 2 100 + 0 10 chrB 100 + 10 30 2\n',
            '5 0 5\n',
            '5 0 5\n',
            '\n',
        ]
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, 'mixed.chain.gz')
            with gzip.open(path, 'wt') as handle:
                handle.writelines(lines)

            chain = ChainFile(path)
            # targets in file are 'chr1' and '2'
            self.assertEqual(sorted(chain.keys()), ['2', 'chr1'])

            # lookups with and without 'chr' prefix should both find the right target
            self.assertEqual(chain['chr1'][6][0], ('chrA', 21, '+'))
            self.assertEqual(chain['1'][6][0], ('chrA', 21, '+'))
            self.assertEqual(chain['2'][6][0], ('chrB', 21, '+'))
            self.assertEqual(chain['chr2'][6][0], ('chrB', 21, '+'))

            # nonexistent contigs should return empty matches
            self.assertEqual(chain['chr3'][6], [])
            self.assertEqual(chain['3'][6], [])

    def test_empty_chain_file(self):
        ''' check chain file with no chains does not raise UnboundLocalError
        '''
        with tempfile.TemporaryDirectory() as tmp_dir:
            # comments-only file
            path1 = os.path.join(tmp_dir, 'comments_only.chain.gz')
            with gzip.open(path1, 'wt') as handle:
                handle.write('# comment only\n')
            chain1 = ChainFile(path1)
            self.assertEqual(list(chain1.keys()), [])
            self.assertEqual(chain1['chr1'][100], [])

            # empty gzip file
            path2 = os.path.join(tmp_dir, 'empty_gzip.chain.gz')
            with gzip.open(path2, 'wb') as handle:
                pass
            chain2 = ChainFile(path2)
            self.assertEqual(list(chain2.keys()), [])
            self.assertEqual(chain2['chr1'][100], [])

            # 0-byte file
            path3 = os.path.join(tmp_dir, 'zero_bytes.chain.gz')
            with open(path3, 'wb') as handle:
                pass
            chain3 = ChainFile(path3)
            self.assertEqual(list(chain3.keys()), [])
            self.assertEqual(chain3['chr1'][100], [])

    def test_get_lifter_url_structure(self):
        ''' check get_lifter constructs canonical goldenPath URL
        '''
        from unittest.mock import patch

        captured_urls = []

        def fake_download(url, dest):
            captured_urls.append(url)
            # write minimal chain file so ChainFile can load
            lines = ['chain 0 chr1 10 + 0 10 chr1 10 + 10 30 1\n',
                     '5 0 5\n',
                     '5 0 5\n',
                     '\n']
            with gzip.open(dest, 'wt') as h:
                h.writelines(lines)

        with tempfile.TemporaryDirectory() as tmp_dir:
            with patch('liftover.lifter.download_file', side_effect=fake_download):
                get_lifter('hg19', 'hg38', cache=tmp_dir)

        self.assertEqual(
            captured_urls,
            ['https://hgdownload.soe.ucsc.edu/goldenPath/hg19/liftOver/hg19ToHg38.over.chain.gz']
        )

    def test_get_lifter_empty_target_or_query(self):
        ''' check get_lifter raises ValueError when target or query is empty
        '''
        with self.assertRaises(ValueError) as context:
            get_lifter('', 'hg38')
        self.assertIn('must not be empty', str(context.exception))

        with self.assertRaises(ValueError) as context:
            get_lifter('hg19', '')
        self.assertIn('must not be empty', str(context.exception))

        with self.assertRaises(ValueError) as context:
            get_lifter('   ', 'hg38')
        self.assertIn('must not be empty', str(context.exception))

        with self.assertRaises(ValueError) as context:
            get_lifter('hg19', '   ')
        self.assertIn('must not be empty', str(context.exception))

    def test_get_lifter_pathlib(self):
        ''' check get_lifter accepts Path objects for chain file path and cache
        '''
        from unittest.mock import patch

        lines = ['chain 0 chr1 10 + 0 10 chr1 10 + 10 30 1\n',
                 '5 0 5\n',
                 '5 0 5\n',
                 '\n']
        with tempfile.TemporaryDirectory() as tmp_dir:
            chain_path = Path(tmp_dir) / 'test.chain.gz'
            with gzip.open(chain_path, 'wt') as h:
                h.writelines(lines)

            # test passing Path as target
            lifter = get_lifter(chain_path)
            self.assertEqual(lifter['chr1'][6][0], ('chr1', 21, '+'))

            # test passing Path as cache directory when downloading
            def fake_download(url, dest):
                with gzip.open(dest, 'wt') as h:
                    h.writelines(lines)

            cache_path = Path(tmp_dir) / 'cache'
            with patch('liftover.lifter.download_file', side_effect=fake_download):
                get_lifter('hg19', 'hg38', cache=cache_path)
            self.assertTrue(cache_path.exists())

    def test_get_lifter_cache_kwargs(self):
        ''' check get_lifter rejects conflicting cache args and unknown kwargs
        '''
        from unittest.mock import patch

        lines = ['chain 0 chr1 10 + 0 10 chr1 10 + 10 30 1\n',
                 '5 0 5\n',
                 '5 0 5\n',
                 '\n']
        def fake_download(url, dest):
            with gzip.open(dest, 'wt') as h:
                h.writelines(lines)

        with tempfile.TemporaryDirectory() as tmp_dir:
            # cache_dir alone works
            cache_path = Path(tmp_dir) / 'cache_dir_only'
            with patch('liftover.lifter.download_file', side_effect=fake_download):
                get_lifter('hg19', 'hg38', cache_dir=cache_path)
            self.assertTrue(cache_path.exists())

            # specifying both cache and cache_dir raises ValueError
            with self.assertRaises(ValueError) as context:
                get_lifter('hg19', 'hg38', cache=tmp_dir, cache_dir=tmp_dir)
            self.assertIn("cannot specify both 'cache' and 'cache_dir'", str(context.exception))

            # unexpected keyword arguments raise TypeError
            with self.assertRaises(TypeError) as context:
                get_lifter('hg19', 'hg38', one_baseed=True)
            self.assertIn("unexpected keyword argument", str(context.exception))

    def test_get_lifter_no_cache_created_for_local_chain(self):
        ''' check get_lifter does not create cache directory when target is a local chain file
        '''
        lines = ['chain 0 chr1 10 + 0 10 chr1 10 + 10 30 1\n',
                 '5 0 5\n',
                 '5 0 5\n',
                 '\n']
        with tempfile.TemporaryDirectory() as tmp_dir:
            chain_path = Path(tmp_dir) / 'test.chain.gz'
            with gzip.open(chain_path, 'wt') as h:
                h.writelines(lines)

            unused_cache = Path(tmp_dir) / 'should_not_exist'
            get_lifter(chain_path, cache=unused_cache)
            self.assertFalse(unused_cache.exists())

    def test_get_lifter_uncompressed_chain(self):
        ''' check get_lifter accepts uncompressed .chain files
        '''
        lines = ['chain 0 chr1 10 + 0 10 chr1 10 + 10 30 1\n',
                 '5 0 5\n',
                 '5 0 5\n',
                 '\n']
        with tempfile.TemporaryDirectory() as tmp_dir:
            chain_path = os.path.join(tmp_dir, 'test.chain')
            with open(chain_path, 'wt') as h:
                h.writelines(lines)

            # test as string path
            lifter_str = get_lifter(chain_path)
            self.assertEqual(lifter_str['chr1'][6][0], ('chr1', 21, '+'))

            # test as Path object
            lifter_path = get_lifter(Path(chain_path))
            self.assertEqual(lifter_path['chr1'][6][0], ('chr1', 21, '+'))

            # test directly via ChainFile
            chain_direct = ChainFile(chain_path)
            self.assertEqual(chain_direct['chr1'][6][0], ('chr1', 21, '+'))

    def test_pyi_stub_validity(self):
        ''' check that the pyi stub file has no undefined symbols
        '''
        import ast
        import builtins

        stub_path = Path(__file__).parent.parent / 'src' / 'liftover' / 'chain_file.pyi'
        with open(stub_path) as f:
            code = f.read()

        env = {}
        exec(code, env)

        tree = ast.parse(code)
        known = set(dir(builtins)) | set(env.keys()) | {'self'}
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.returns:
                    for sub in ast.walk(node.returns):
                        if isinstance(sub, ast.Name):
                            self.assertIn(sub.id, known)
            elif isinstance(node, ast.arg) and node.annotation:
                for sub in ast.walk(node.annotation):
                    if isinstance(sub, ast.Name):
                        self.assertIn(sub.id, known)

    def test_download_file_timeout(self):
        ''' check download_file passes timeout and handles timeout exceptions cleanly
        '''
        from unittest.mock import patch, MagicMock
        import urllib3
        from liftover.download_file import download_file

        # verify timeout parameter is passed to http.request
        with patch('urllib3.PoolManager') as mock_pm:
            mock_pool = MagicMock()
            mock_pm.return_value = mock_pool
            mock_response = MagicMock()
            mock_response.status = 200
            mock_response.stream.return_value = [b'data']
            mock_pool.request.return_value = mock_response

            with tempfile.TemporaryDirectory() as tmp_dir:
                dest = os.path.join(tmp_dir, 'dest.txt')
                download_file('https://example.com/file', dest, timeout=12.5)

            mock_pool.request.assert_called_once_with(
                'GET', 'https://example.com/file', preload_content=False, timeout=12.5
            )
            mock_pool.clear.assert_called_once()

        # verify timeout error is converted to ValueError
        with patch('urllib3.PoolManager') as mock_pm:
            mock_pool = MagicMock()
            mock_pm.return_value = mock_pool
            mock_pool.request.side_effect = urllib3.exceptions.TimeoutError("connection timed out")

            with tempfile.TemporaryDirectory() as tmp_dir:
                dest = os.path.join(tmp_dir, 'dest.txt')
                with self.assertRaises(ValueError) as context:
                    download_file('https://example.com/file', dest, timeout=5.0)
                self.assertIn("problem accessing", str(context.exception))
                self.assertIn("timed out", str(context.exception))
            mock_pool.clear.assert_called_once()

    def test_download_file_verification(self):
        ''' check download_file verifies content length, empty payloads, and gzip integrity
        '''
        from unittest.mock import patch, MagicMock
        from liftover.download_file import download_file

        # 1. Content-Length mismatch
        with patch('urllib3.PoolManager') as mock_pm:
            mock_pool = MagicMock()
            mock_pm.return_value = mock_pool
            mock_resp = MagicMock()
            mock_resp.status = 200
            mock_resp.headers = {'Content-Length': '1000'}
            mock_resp.stream.return_value = [b'short data']
            mock_pool.request.return_value = mock_resp

            with tempfile.TemporaryDirectory() as tmp_dir:
                dest = os.path.join(tmp_dir, 'test.chain.gz')
                with self.assertRaises(ValueError) as ctx:
                    download_file('https://example.com/file.gz', dest)
                self.assertIn('incomplete download', str(ctx.exception))
                self.assertFalse(os.path.exists(dest))

        # 2. Empty response
        with patch('urllib3.PoolManager') as mock_pm:
            mock_pool = MagicMock()
            mock_pm.return_value = mock_pool
            mock_resp = MagicMock()
            mock_resp.status = 200
            mock_resp.headers = {}
            mock_resp.stream.return_value = []
            mock_pool.request.return_value = mock_resp

            with tempfile.TemporaryDirectory() as tmp_dir:
                dest = os.path.join(tmp_dir, 'test.chain.gz')
                with self.assertRaises(ValueError) as ctx:
                    download_file('https://example.com/file.gz', dest)
                self.assertIn('empty response', str(ctx.exception))
                self.assertFalse(os.path.exists(dest))

        # 3. Non-gzip payload (e.g. HTML 200 error page)
        with patch('urllib3.PoolManager') as mock_pm:
            mock_pool = MagicMock()
            mock_pm.return_value = mock_pool
            mock_resp = MagicMock()
            mock_resp.status = 200
            html_payload = b'<html>404 Not Found</html>'
            mock_resp.headers = {'Content-Length': str(len(html_payload))}
            mock_resp.stream.return_value = [html_payload]
            mock_pool.request.return_value = mock_resp

            with tempfile.TemporaryDirectory() as tmp_dir:
                dest = os.path.join(tmp_dir, 'test.chain.gz')
                with self.assertRaises(ValueError) as ctx:
                    download_file('https://example.com/file.gz', dest)
                self.assertIn('not a valid gzip file', str(ctx.exception))
                self.assertFalse(os.path.exists(dest))

    def test_download_file_permissions(self):
        ''' check downloaded file respects standard umask permissions rather than 0600
        '''
        import stat
        from unittest.mock import patch, MagicMock
        from liftover.download_file import download_file

        with patch('urllib3.PoolManager') as mock_pm:
            mock_pool = MagicMock()
            mock_pm.return_value = mock_pool
            mock_resp = MagicMock()
            mock_resp.status = 200
            data = b'chain 0 chr1 10 + 0 10 chr1 10 + 10 30 1\n'
            # prepare gzipped bytes so verify_file passes
            import gzip, io
            bio = io.BytesIO()
            with gzip.GzipFile(fileobj=bio, mode='wb') as gz:
                gz.write(data)
            gz_bytes = bio.getvalue()

            mock_resp.headers = {'Content-Length': str(len(gz_bytes))}
            mock_resp.stream.return_value = [gz_bytes]
            mock_pool.request.return_value = mock_resp

            with tempfile.TemporaryDirectory() as tmp_dir:
                dest = os.path.join(tmp_dir, 'test.chain.gz')
                download_file('https://example.com/file.gz', dest)

                file_mode = stat.S_IMODE(os.stat(dest).st_mode)
                cur_umask = os.umask(0)
                os.umask(cur_umask)
                expected_mode = 0o666 & ~cur_umask
                self.assertEqual(file_mode, expected_mode)

    def test_one_based_coordinate_lifting(self):
        ''' check one_based=True lifts 1-based coordinates correctly compared to 0-based
        '''
        lines = [
            'chain 0 chr1 100 + 10 20 chrA 100 + 100 110 1\n',
            '10\n',
            '\n'
        ]
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, 'test.chain.gz')
            with gzip.open(path, 'wt') as h:
                h.writelines(lines)

            lifter_0 = ChainFile(path, one_based=False)
            lifter_1 = ChainFile(path, one_based=True)

            # In 0-based: [10, 20) -> [100, 110)
            self.assertEqual(lifter_0['chr1'][10], [('chrA', 100, '+')])
            self.assertEqual(lifter_0['chr1'][15], [('chrA', 105, '+')])
            self.assertEqual(lifter_0['chr1'][19], [('chrA', 109, '+')])
            self.assertEqual(lifter_0['chr1'][9], [])
            self.assertEqual(lifter_0['chr1'][20], [])

            # In 1-based: [11, 21) -> [101, 111)
            self.assertEqual(lifter_1['chr1'][11], [('chrA', 101, '+')])
            self.assertEqual(lifter_1['chr1'][16], [('chrA', 106, '+')])
            self.assertEqual(lifter_1['chr1'][20], [('chrA', 110, '+')])
            self.assertEqual(lifter_1['chr1'][10], [])
            self.assertEqual(lifter_1['chr1'][21], [])

    def test_chain_header_prefix_does_not_match_non_headers(self):
        ''' check that non-header lines starting with chainfoo are treated as alignment lines
        '''
        # If 'chainfoo' were treated as a header line, it would throw an invalid header line error
        # Instead, it is an invalid alignment line
        lines = [
            'chain 0 chr1 100 + 10 20 chrA 100 + 100 110 1\n',
            'chainfoo 10 10\n',
            '\n'
        ]
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, 'test.chain.gz')
            with gzip.open(path, 'wt') as h:
                h.writelines(lines)

            with self.assertRaises(ValueError) as context:
                ChainFile(path)
            self.assertIn('invalid alignment line', str(context.exception))

    def test_module_version_and_name(self):
        ''' check module __version__ is defined and __name__ is not overwritten
        '''
        import liftover
        self.assertEqual(lifter_module_name := liftover.__name__, 'liftover')
        self.assertIsInstance(liftover.__version__, str)
        self.assertTrue(len(liftover.__version__) > 0)
        self.assertIn('__version__', liftover.__all__)











