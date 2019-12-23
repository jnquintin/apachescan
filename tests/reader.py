import unittest
import tempfile
import shutil
import os.path as path
import apachescan.reader as reader


class TestStringMethods(unittest.TestCase):

    def setUp(self):
        self.directory = tempfile.mkdtemp()

    def tearDown(self):
        try:
            shutil.rmtree(self.directory)
        except OSError as e:
            print ("Error: %s - %s." % (e.filename, e.strerror))

    def test_directory(self):
        """
        Test the file reader with a directory
        """
        self.assertRaises(IOError, reader.filehandler.CopyTruncateFile,
                          self.directory)

    def test_notexisting_file(self):
        """
        Test the file reader with not existing file
        """
        log_file = path.join(self.directory, "noexisting.file")
        self.assertRaises(IOError, reader.filehandler.CopyTruncateFile,
                          log_file)

    def test_growing_empty_file(self):
        """
        Test the file reader with an empty file
        """
        log_file = path.join(self.directory, "growing_empty.file")
        f = open(log_file, "w+")
        f.close()
        self.assertTrue(path.exists(log_file))

        self.assertRaises(reader.filehandler.EmptyFile,
                          reader.filehandler.CopyTruncateFile,
                          log_file)

    def test_growing_existing_file(self):
        """
        Test the file reader with an empty file
        """
        log_file = path.join(self.directory, "growing.file")

        writen_lines = [
            "Now the file has more content!",
            "Now the file has and even more content!",
            "Now the file has and even more content!"
        ]

        f = open(log_file, "a+")
        for lines in writen_lines:
            f.write(lines + "\n")
        f.close()

        try:
            log_reader = reader.filehandler.CopyTruncateFile(log_file)
        except Exception:
            self.fail("apachescan reader "
                      "should handle not existing file")

        number_of_line = 0
        for expected_line, read_line in zip(writen_lines, log_reader):
            self.assertEqual(read_line.strip(), expected_line)
            number_of_line += 1

        self.assertEqual(number_of_line, len(writen_lines))

        writen_lines = [
            "Now the file has additionnal content!",
            "Now the file has and even more content! 1",
            "Now the file has and even more content! 2"
        ]

        f = open(log_file, "a")
        for lines in writen_lines:
            f.write(lines + "\n")
        f.close()

        number_of_line = 0
        for expected_line, read_line in zip(writen_lines, log_reader):
            self.assertEqual(read_line.strip(), expected_line)
            number_of_line += 1

        self.assertEqual(number_of_line, len(writen_lines))


if __name__ == "__main__":
    unittest.main()
