
import gzip
import os
import sys
import tempfile
import unittest
from pathlib import Path

from liftover import get_lifter, ChainFile


class TestChainFile(unittest.TestCase):
    ''' unittest the lifting operations
    '''
    @classmethod
    def setUpClass(self):
        # CI sets LIFTOVER_TEST_CACHE to a pre-fetched chain file folder, to
        # avoid every job downloading from UCSC
        self.lifter = get_lifter('hg19', 'hg38', cache=os.environ.get('LIFTOVER_TEST_CACHE'))

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

        for bad_pos in (100.9, True, False, None):
            with self.assertRaises(TypeError):
                self.lifter['chr1'][bad_pos]
            with self.assertRaises(TypeError):
                self.lifter.query('chr1', bad_pos)
            with self.assertRaises(TypeError):
                self.lifter.convert_coordinate('chr1', bad_pos)
            with self.assertRaises(TypeError):
                self.lifter.query('chr_missing', bad_pos)

        class IntLike:
            def __index__(self):
                return 103786442

        self.assertEqual(self.lifter['chr1'][IntLike()], self.lifter['chr1'][103786442])
        self.assertEqual(self.lifter.query('chr1', IntLike()), self.lifter.query('chr1', 103786442))

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

    def test_get_lifter_chain_server_trailing_slash(self):
        ''' check get_lifter strips trailing slashes from chain_server
        '''
        from unittest.mock import patch

        captured_urls = []

        def fake_download(url, dest):
            captured_urls.append(url)
            lines = ['chain 0 chr1 10 + 0 10 chr1 10 + 10 30 1\n',
                     '5 0 5\n',
                     '5 0 5\n',
                     '\n']
            with gzip.open(dest, 'wt') as h:
                h.writelines(lines)

        with tempfile.TemporaryDirectory() as tmp_dir:
            with patch('liftover.lifter.download_file', side_effect=fake_download):
                get_lifter('hg19', 'hg38', cache=tmp_dir, chain_server='https://example.org/mirror///')

        self.assertEqual(
            captured_urls,
            ['https://example.org/mirror/goldenPath/hg19/liftOver/hg19ToHg38.over.chain.gz']
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
        self.assertEqual(liftover.__name__, 'liftover')
        self.assertIsInstance(liftover.__version__, str)
        self.assertTrue(len(liftover.__version__) > 0)
        self.assertIn('__version__', liftover.__all__)

    def test_default_cache_dir_xdg(self):
        ''' check default_cache_dir returns XDG cache location
        '''
        from unittest.mock import patch
        from liftover import default_cache_dir

        cache_dir = default_cache_dir()
        self.assertEqual(os.path.basename(os.path.normpath(cache_dir)), 'liftover')

        # test XDG_CACHE_HOME override on non-Windows platforms
        if sys.platform != 'win32':
            with tempfile.TemporaryDirectory() as tmp_dir:
                with patch.dict(os.environ, {'XDG_CACHE_HOME': tmp_dir}):
                    xdg_cache = default_cache_dir()
                    self.assertEqual(os.path.normpath(xdg_cache), os.path.normpath(os.path.join(tmp_dir, 'liftover')))

        # test Windows LOCALAPPDATA resolution
        with tempfile.TemporaryDirectory() as tmp_dir:
            with patch.object(sys, 'platform', 'win32'), \
                 patch.dict(os.environ, {'LOCALAPPDATA': tmp_dir}):
                win_cache = default_cache_dir()
                self.assertEqual(os.path.normpath(win_cache), os.path.normpath(os.path.join(tmp_dir, 'liftover')))

    def test_get_lifter_legacy_cache_fallback(self):
        ''' check get_lifter falls back to ~/.liftover when present
        '''
        from unittest.mock import patch

        lines = [
            'chain 0 chr1 100 + 0 10 chrA 100 + 10 30 1\n',
            '5 0 5\n',
            '5 0 5\n',
            '\n'
        ]

        with tempfile.TemporaryDirectory() as tmp_dir:
            new_cache = os.path.join(tmp_dir, 'new_cache')
            legacy_dir = os.path.join(tmp_dir, 'legacy_liftover')
            os.makedirs(legacy_dir, exist_ok=True)
            legacy_file = os.path.join(legacy_dir, 'hg19ToHg38.over.chain.gz')
            with gzip.open(legacy_file, 'wt') as h:
                h.writelines(lines)

            real_expanduser = os.path.expanduser

            def fake_expanduser(path):
                if path == '~/.liftover':
                    return legacy_dir
                return real_expanduser(path)

            download_mock = unittest.mock.MagicMock()

            with patch('liftover.lifter.default_cache_dir', return_value=new_cache), \
                 patch('os.path.expanduser', side_effect=fake_expanduser), \
                 patch('liftover.lifter.download_file', download_mock):
                lifter = get_lifter('hg19', 'hg38')

            # Should use legacy file without downloading
            self.assertEqual(lifter['chr1'][6][0], ('chrA', 21, '+'))
            download_mock.assert_not_called()
            self.assertFalse(os.path.exists(new_cache))

    def test_get_lifter_downloads_to_new_cache(self):
        ''' check get_lifter downloads to default cache when legacy cache is absent
        '''
        from unittest.mock import patch

        lines = [
            'chain 0 chr1 100 + 0 10 chrA 100 + 10 30 1\n',
            '5 0 5\n',
            '5 0 5\n',
            '\n'
        ]

        with tempfile.TemporaryDirectory() as tmp_dir:
            new_cache = os.path.join(tmp_dir, 'new_cache')
            empty_legacy_dir = os.path.join(tmp_dir, 'empty_legacy')

            def fake_download(url, dest):
                with gzip.open(dest, 'wt') as h:
                    h.writelines(lines)

            real_expanduser = os.path.expanduser

            def fake_expanduser(path):
                if path == '~/.liftover':
                    return empty_legacy_dir
                return real_expanduser(path)

            with patch('liftover.lifter.default_cache_dir', return_value=new_cache), \
                 patch('os.path.expanduser', side_effect=fake_expanduser), \
                 patch('liftover.lifter.download_file', side_effect=fake_download):
                lifter = get_lifter('hg19', 'hg38')

            self.assertEqual(lifter['chr1'][6][0], ('chrA', 21, '+'))
            # Verified downloaded to new_cache
            self.assertTrue(os.path.exists(os.path.join(new_cache, 'hg19ToHg38.over.chain.gz')))

    def test_multiple_overlapping_matches(self):
        ''' check positions matching multiple overlapping chains (inline and >4 overflow)
        '''
        lines = []
        for idx in range(6):
            q_start = 100 * (idx + 1)
            lines.extend([
                f'chain 0 chr1 100 + 10 30 chrQ{idx} 1000 + {q_start} {q_start + 20} {idx + 1}\n',
                '20\n',
                '\n',
            ])
        # Also add a chain covering only [10, 20) so pos=25 has 6 matches and pos=15 has 7
        lines.extend([
            'chain 0 chr1 100 + 10 20 chrExtra 1000 - 50 60 7\n',
            '10\n',
            '\n',
        ])

        with tempfile.TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, 'multi.chain.gz')
            with gzip.open(path, 'wt') as h:
                h.writelines(lines)

            chain = ChainFile(path)
            matches_25 = chain['chr1'][25]
            self.assertEqual(len(matches_25), 6)
            self.assertEqual(
                sorted(matches_25),
                sorted((f'chrQ{i}', 100 * (i + 1) + 15, '+') for i in range(6)),
            )

            matches_15 = chain['chr1'][15]
            self.assertEqual(len(matches_15), 7)
            self.assertIn(('chrExtra', 1000 - 55 - 1, '-'), matches_15)

    def test_nested_and_unsorted_overlapping_chains(self):
        ''' check nested and out-of-order overlapping chains query accurately at all boundaries
        '''
        lines = [
            'chain 0 chr1 2000 + 300 400 chrInner2 2000 + 3000 3100 1\n',
            '100\n\n',
            'chain 0 chr1 2000 + 10 1000 chrOuter 2000 + 1000 1990 2\n',
            '990\n\n',
            'chain 0 chr1 2000 + 100 200 chrInner1 2000 + 2000 2100 3\n',
            '100\n\n',
            'chain 0 chr1 2000 + 500 600 chrInner3 2000 + 4000 4100 4\n',
            '100\n\n',
        ]
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, 'nested.chain.gz')
            with gzip.open(path, 'wt') as h:
                h.writelines(lines)

            chain = ChainFile(path)
            self.assertEqual(chain['chr1'][-1], [])
            self.assertEqual(chain['chr1'][-2**63], [])
            self.assertEqual(chain['chr1'][9], [])
            self.assertEqual(chain['chr1'][10], [('chrOuter', 1000, '+')])
            self.assertEqual(chain['chr1'][99], [('chrOuter', 1089, '+')])
            self.assertEqual(
                sorted(chain['chr1'][100]),
                [('chrInner1', 2000, '+'), ('chrOuter', 1090, '+')],
            )
            self.assertEqual(
                sorted(chain['chr1'][199]),
                [('chrInner1', 2099, '+'), ('chrOuter', 1189, '+')],
            )
            self.assertEqual(chain['chr1'][200], [('chrOuter', 1190, '+')])
            self.assertEqual(chain['chr1'][950], [('chrOuter', 1940, '+')])
            self.assertEqual(chain['chr1'][999], [('chrOuter', 1989, '+')])
            self.assertEqual(chain['chr1'][1000], [])

    def test_download_file_midstream_errors_and_status(self):
        ''' check mid-stream urllib3 errors, HTTP status codes, and decode_content handling
        '''
        import io
        from unittest.mock import patch, MagicMock
        import urllib3
        from liftover.download_file import download_file

        # 1. Mid-stream ReadTimeoutError / ProtocolError wrapped as ValueError and cleans temp file
        with patch('urllib3.PoolManager') as mock_pm:
            mock_pool = MagicMock()
            mock_pm.return_value = mock_pool
            mock_resp = MagicMock()
            mock_resp.status = 200
            mock_resp.headers = {}

            def broken_stream(*args, **kwargs):
                yield b'partial'
                raise urllib3.exceptions.ReadTimeoutError(mock_pool, 'https://example.com/f.gz', 'read timed out')

            mock_resp.stream.side_effect = broken_stream
            mock_pool.request.return_value = mock_resp

            with tempfile.TemporaryDirectory() as tmp_dir:
                dest = os.path.join(tmp_dir, 'test.chain.gz')
                with self.assertRaises(ValueError) as ctx:
                    download_file('https://example.com/f.gz', dest)
                self.assertIn('problem downloading', str(ctx.exception))
                self.assertEqual(os.listdir(tmp_dir), [])

        # 2. Non-200 HTTP status includes status code
        with patch('urllib3.PoolManager') as mock_pm:
            mock_pool = MagicMock()
            mock_pm.return_value = mock_pool
            mock_resp = MagicMock()
            mock_resp.status = 404
            mock_pool.request.return_value = mock_resp

            with tempfile.TemporaryDirectory() as tmp_dir:
                dest = os.path.join(tmp_dir, 'test.chain.gz')
                with self.assertRaises(ValueError) as ctx:
                    download_file('https://example.com/f.gz', dest)
                self.assertIn('HTTP 404', str(ctx.exception))

        # 3. .gz downloads pass decode_content=False and never call os.umask
        bio = io.BytesIO()
        with gzip.GzipFile(fileobj=bio, mode='wb') as gz:
            gz.write(b'chain 0 chr1 10 + 0 10 chr1 10 + 0 10 1\n10\n\n')
        gz_bytes = bio.getvalue()

        with patch('urllib3.PoolManager') as mock_pm, \
             patch('os.umask', side_effect=AssertionError('os.umask should not be called')):
            mock_pool = MagicMock()
            mock_pm.return_value = mock_pool
            mock_resp = MagicMock()
            mock_resp.status = 200
            mock_resp.headers = {'Content-Length': str(len(gz_bytes)), 'Content-Encoding': 'gzip'}
            mock_resp.stream.return_value = [gz_bytes]
            mock_pool.request.return_value = mock_resp

            with tempfile.TemporaryDirectory() as tmp_dir:
                dest = os.path.join(tmp_dir, 'test.chain.gz')
                download_file('https://example.com/f.gz', dest)
                mock_resp.stream.assert_called_once_with(65536, decode_content=False)
                self.assertTrue(os.path.exists(dest))

    def test_path_validation_and_tilde_expansion(self):
        ''' check os.fspath validation, ~ expansion, and build name path-traversal rejection
        '''
        from unittest.mock import patch

        for bad_path in (123, None, b'bytes.chain.gz'):
            with self.assertRaises(TypeError):
                ChainFile(bad_path)
            with self.assertRaises(TypeError):
                get_lifter(bad_path)

        for bad_build in ('../hg19', 'hg19/extra', 'hg19\\extra', '..'):
            with self.assertRaises(ValueError):
                get_lifter(bad_build, 'hg38')
            with self.assertRaises(ValueError):
                get_lifter('hg19', bad_build)

        with tempfile.TemporaryDirectory() as tmp_dir:
            chain_file = os.path.join(tmp_dir, 'home.chain.gz')
            with gzip.open(chain_file, 'wt') as h:
                h.write('chain 0 chr1 10 + 0 10 chr1 10 + 0 10 1\n10\n\n')

            real_expanduser = os.path.expanduser
            def fake_expanduser(p):
                if isinstance(p, str) and p.startswith('~/'):
                    return os.path.join(tmp_dir, p[2:])
                return real_expanduser(p)

            with patch('os.path.expanduser', side_effect=fake_expanduser):
                cf1 = ChainFile('~/home.chain.gz')
                self.assertEqual(cf1['chr1'][5], [('chr1', 5, '+')])
                cf2 = get_lifter('~/home.chain.gz')
                self.assertEqual(cf2['chr1'][5], [('chr1', 5, '+')])

    def test_unicode_chain_file_path(self):
        ''' check chain files in non-ASCII directory and file names load cleanly
        '''
        with tempfile.TemporaryDirectory() as tmp_dir:
            unicode_dir = os.path.join(tmp_dir, 'пользователи_用户_λ')
            os.makedirs(unicode_dir)
            chain_path = os.path.join(unicode_dir, 'tëst_链.chain.gz')
            with gzip.open(chain_path, 'wt') as h:
                h.write('chain 0 chr1 10 + 0 10 chr1 10 + 0 10 1\n10\n\n')

            cf = ChainFile(chain_path)
            self.assertEqual(cf['chr1'][5], [('chr1', 5, '+')])
            with self.assertRaises(ValueError):
                ChainFile(unicode_dir)

    def test_chain_file_docstrings_and_signature(self):
        ''' check ChainFile exposes class and __init__ docstrings and signature at runtime
        '''
        import inspect
        self.assertIsNotNone(ChainFile.__doc__)
        self.assertIn('coordinates', ChainFile.__doc__)
        self.assertIsNotNone(ChainFile.__init__.__doc__)
        self.assertIn('one_based', ChainFile.__init__.__doc__)
        sig = inspect.signature(ChainFile)
        self.assertEqual(list(sig.parameters), ['path', 'target', 'query', 'one_based'])

    def test_convert_coordinate_strand(self):
        ''' check convert_coordinate supports pyliftover's optional strand argument
        '''
        lines = [
            'chain 0 chr1 100 + 0 10 chrFwd 100 + 10 20 1\n10\n\n',
            'chain 0 chr2 100 + 0 10 chrRev 100 - 10 20 2\n10\n\n',
        ]
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, 'strand.chain.gz')
            with gzip.open(path, 'wt') as h:
                h.writelines(lines)
            cf = ChainFile(path)

            self.assertEqual(cf.convert_coordinate('chr1', 5), [('chrFwd', 15, '+')])
            self.assertEqual(cf.convert_coordinate('chr1', 5, '+'), [('chrFwd', 15, '+')])
            self.assertEqual(cf.convert_coordinate('chr1', 5, '-'), [('chrFwd', 15, '-')])

            self.assertEqual(cf.convert_coordinate('chr2', 5), [('chrRev', 84, '-')])
            self.assertEqual(cf.convert_coordinate('chr2', 5, '+'), [('chrRev', 84, '-')])
            self.assertEqual(cf.convert_coordinate('chr2', 5, '-'), [('chrRev', 84, '+')])

            with self.assertRaises(ValueError):
                cf.convert_coordinate('chr1', 5, '?')
            with self.assertRaises(TypeError):
                cf.convert_coordinate('chr1', 5, None)

    def test_get_lifter_zero_byte_cached_file(self):
        ''' check a 0-byte file in primary cache triggers fallback or re-download
        '''
        from unittest.mock import patch

        lines = ['chain 0 chr1 100 + 0 10 chrA 100 + 10 20 1\n10\n\n']

        with tempfile.TemporaryDirectory() as tmp_dir:
            # 1. Explicit cache with 0-byte file re-downloads
            cache_dir = os.path.join(tmp_dir, 'cache')
            os.makedirs(cache_dir)
            empty_cached = os.path.join(cache_dir, 'hg19ToHg38.over.chain.gz')
            open(empty_cached, 'wb').close()

            def fake_download(url, dest):
                with gzip.open(dest, 'wt') as h:
                    h.writelines(lines)

            with patch('liftover.lifter.download_file', side_effect=fake_download) as dl_mock:
                lifter = get_lifter('hg19', 'hg38', cache=cache_dir)
            dl_mock.assert_called_once()
            self.assertEqual(lifter['chr1'][5], [('chrA', 15, '+')])

            # 2. Default cache with 0-byte file falls back to non-empty legacy cache
            new_cache = os.path.join(tmp_dir, 'new_cache')
            os.makedirs(new_cache)
            open(os.path.join(new_cache, 'hg19ToHg38.over.chain.gz'), 'wb').close()

            legacy_dir = os.path.join(tmp_dir, 'legacy')
            os.makedirs(legacy_dir)
            with gzip.open(os.path.join(legacy_dir, 'hg19ToHg38.over.chain.gz'), 'wt') as h:
                h.writelines(lines)

            real_expanduser = os.path.expanduser
            def fake_expanduser(p):
                return legacy_dir if p == '~/.liftover' else real_expanduser(p)

            with patch('liftover.lifter.default_cache_dir', return_value=new_cache), \
                 patch('os.path.expanduser', side_effect=fake_expanduser), \
                 patch('liftover.lifter.download_file') as dl_mock2:
                lifter2 = get_lifter('hg19', 'hg38')
            dl_mock2.assert_not_called()
            self.assertEqual(lifter2['chr1'][5], [('chrA', 15, '+')])



