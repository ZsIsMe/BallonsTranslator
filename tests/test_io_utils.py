import os.path as osp
import tempfile
import unittest

from ballontranslator.utils.io_utils import find_all_imgs, find_tif_files, is_macos_metadata_file


class ImageFileDiscoveryTest(unittest.TestCase):

    def test_macos_metadata_files_are_ignored(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            for filename in ('001.jpg', '002.png', '._001.jpg', '._002.png', 'notes.txt'):
                open(osp.join(temp_dir, filename), 'wb').close()

            self.assertEqual(find_all_imgs(temp_dir, sort=True), ['001.jpg', '002.png'])

    def test_macos_metadata_tif_files_are_ignored(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            for filename in ('page.tif', '._page.tif', 'cover.tiff', '._cover.tiff'):
                open(osp.join(temp_dir, filename), 'wb').close()

            self.assertEqual(find_tif_files(temp_dir, sort=True), ['cover.tiff', 'page.tif'])

    def test_macos_metadata_detection_only_matches_appledouble_prefix(self):
        self.assertTrue(is_macos_metadata_file('._001.jpg'))
        self.assertFalse(is_macos_metadata_file('.hidden.jpg'))
        self.assertFalse(is_macos_metadata_file('001.jpg'))


if __name__ == '__main__':
    unittest.main()
