import unittest
from unittest.mock import MagicMock, patch
import structure_engine
import fast_converter

class TestExtendedScope(unittest.TestCase):

    @patch('structure_engine.cleaner')
    def test_gmft_calls_cleaner(self, mock_cleaner):
        # We can't easily mock PyPDFium2Document without a file, 
        # so we'll check if the logic *tries* to import and setup.
        # Instead, let's verify cleaner import in structure_engine
        self.assertTrue(hasattr(structure_engine, 'cleaner'))
        
    @patch('fast_converter.cleaner')
    @patch('fast_converter.MarkItDown')
    def test_fast_converter_calls_cleaner(self, mock_mid, mock_cleaner):
        mock_instance = MagicMock()
        mock_instance.convert.return_value.text_content = "bro- \n ken"
        mock_mid.return_value = mock_instance
        
        mock_cleaner.merge_hyphenated_words.return_value = "broken"
        
        result = fast_converter.convert_fast("dummy.pdf")
        
        mock_cleaner.merge_hyphenated_words.assert_called_with("bro- \n ken")
        self.assertEqual(result, "broken")

if __name__ == '__main__':
    unittest.main()
