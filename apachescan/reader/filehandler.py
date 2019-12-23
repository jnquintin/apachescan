"""
Module to handle reading log continiously from a file
"""

from pygtail import Pygtail
import os


class Error(Exception):
    """Base class for other exceptions"""
    pass


class EmptyFile(Error):
    """Raise when an empty file is opened to allow reopen it later"""
    pass


class CopyTruncateFile(Pygtail):
    """
    Read file which may be copytruncated by log rotate

    Args:
        filename to be read
    """

    def __init__(self, filename):
        if not os.path.exists(filename):
            raise IOError("File '%s' does not"
                          " exist." % filename)
        if os.path.isdir(filename):
            raise IOError("File '%s' is a directory"
                          " provide a file as input." % filename)
        if os.stat(filename).st_size == 0:
            raise EmptyFile("File '%s' is a empty in this case the reader "
                            "needs to be recreated to see the updates"
                            " provide a file as input." % filename)

        super(CopyTruncateFile, self).__init__(filename)
        """
        Pygtail:
            filename
            offset_file   File to which offset data is written
                          (default: <logfile>.offset).
            paranoid      Update the offset file every time we read a line
                          (as opposed to only when we reach the end of
                          the file (default: False))
            every_n       Update the offset file every n'th line
                          (as opposed to only when
                          we reach the end of the file (default: 0))
            on_update     Execute this function when offset data is written
                          (default False)
            copytruncate  Support copytruncate-style log rotation
                          (default: True)
            log_patterns  List of custom rotated log patterns to match
                          (default: None)
            full_lines    Only log when line ends in a newline `\n`
                          (default: False)

        API:
            next          Return the next line in the file,
                          updating the offset.
            readlines     Read in all unread lines and return them as a list.
            read          Read in all unread lines and return them as
                          a single string.
        """

    def reopen(self):
        super(CopyTruncateFile, self).__init__(self.filename)

    def _filehandle(self):
        try:
            return super(CopyTruncateFile, self)._filehandle()
        except Exception:
            return None
