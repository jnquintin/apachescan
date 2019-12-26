"""
Module to handle reading log continuously from a file
"""

import os
from pygtail import Pygtail


class CopyTruncateFile(Pygtail):
    """
    Reads file which may be copytruncated by log rotate

    Args:
        filename: to be read
    """

    def __init__(self, filename, offset_filename=None):
        if not os.path.exists(filename):
            raise IOError("File '%s' does not"
                          " exist." % filename)
        if os.path.isdir(filename):
            raise IOError("File '%s' is a directory. Please "
                          "provide a file as input." % filename)

        # Informations about Pygtail:
        #     filename
        #     offset_file   File to which offset data is written
        #                   (default: <logfile>.offset).
        #     paranoid      Update the offset file every time we read a line
        #                   (as opposed to only when we reach the end of
        #                   the file (default: False))
        #     every_n       Update the offset file every n'th line
        #                   (as opposed to only when
        #                   we reach the end of the file (default: 0))
        #     on_update     Execute this function when offset data is written
        #                   (default False)
        #     copytruncate  Support copytruncate-style log rotation
        #                   (default: True)
        #     log_patterns  List of custom rotated log patterns to match
        #                   (default: None)
        #     full_lines    Only log when line ends in a newline `\n`
        #                   (default: False)

        # API:
        #     next          Return the next line in the file,
        #                   updating the offset.
        #     readlines     Read in all unread lines and return them as a list.
        #     read          Read in all unread lines and return them as
        #                   a single string.
        super(CopyTruncateFile, self).__init__(filename, offset_filename)

    def _filehandle(self):
        try:
            return super(CopyTruncateFile, self)._filehandle()
        except AttributeError:
            # On delete the Attribute exception is raise
            # This catch it to avoid warning message
            return None
