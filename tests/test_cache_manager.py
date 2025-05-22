import unittest
import time

from cache_manager import write_to_cache, read_from_cache, is_cache_valid, clear_cache


class TestCacheManager(unittest.TestCase):
    def tearDown(self):
        clear_cache()

    def test_write_and_read(self):
        write_to_cache('foo', 'bar')
        self.assertEqual(read_from_cache('foo'), 'bar')
        self.assertTrue(is_cache_valid('foo'))

    def test_expiry(self):
        write_to_cache('temp', 'value', expiry=0.1)
        time.sleep(0.2)
        self.assertIsNone(read_from_cache('temp'))
        self.assertFalse(is_cache_valid('temp'))

    def test_missing_key(self):
        self.assertIsNone(read_from_cache('missing'))
        self.assertFalse(is_cache_valid('missing'))

    def test_clear_cache(self):
        write_to_cache('a', 'b')
        clear_cache('a')
        self.assertIsNone(read_from_cache('a'))

    def test_read_returns_copy_for_mutable(self):
        data = [1, 2, 3]
        write_to_cache('list', data)
        cached = read_from_cache('list')
        cached.append(4)
        self.assertEqual(read_from_cache('list'), [1, 2, 3])


if __name__ == '__main__':
    unittest.main()
