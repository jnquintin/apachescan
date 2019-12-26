"""
Module to centralize the exception raise by all sub modules
"""


class Error(Exception):
    """Base class for other exceptions"""
    pass


class WrongArguments(Error):
    """Guard wrong arguments"""
    pass
