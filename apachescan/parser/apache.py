"""
This module parse a string into a request

The Parser class could/should have been done as a singleton.

The Parser has no state and there is no requirements to create it twice.
"""

import re
import logging

from datetime import datetime, timedelta

LOGGER = logging.getLogger(__name__)

AVAILABLE_KEYS = ["ip", "local_user", "remote_user",
                  "action", "page", "protocol",
                  "status_code"]

ALL_KEYS = AVAILABLE_KEYS + ["date", "datetime", "response_size"]


class Parser(object):
    """
    Parse the Apache log in the CLF format
    """

    def __init__(self):

        # IP address compound by 4 numbers
        regexp = r'^(?P<ip>[\d\.]+) +'
        # two user separate by spaces
        regexp += r'(?P<local_user>[^ ]+) +(?P<remote_user>[^ ]+) +'
        # date + time zone enter []
        regexp += r'\[(?P<date>([^\]](\\])?)+ [+-]\d{4})\] +'
        # request enter quote
        regexp += r'"(?P<request_details>([^"](\\\")?)+)" +'
        # status code
        regexp += r'(?P<status_code>\d+) +'
        # response size followed by space optional additional information
        regexp += r'(?P<response_size>\d+)( (?P<remaining>.*))?'

        self.main_regular_expression = regexp

        self.main_regexp = re.compile(self.main_regular_expression)

        # The request is formed by Action in uppercase
        self.details_regular_expression = r'^ *(?P<action>[A-Z]+) +'
        # an url
        self.details_regular_expression += r'(?P<page>[^ ]+)'
        # and a protocol
        self.details_regular_expression += r' +(?P<protocol>[^ ]+)'
        self.details_regexp = re.compile(self.details_regular_expression)

    @staticmethod
    def parse_date(date_str):
        """
        Parses a date in the apache log format without timezone

        Args:
            date_str: string containing a date in the format: %d/%b/%Y:%H:%M:%S

        Returns:
            date in datetime format

        Notes:
            The timezone is not handle here because python2 does not handle it.
            The code is compliant python 2 and 3.
            Some tests could be added to check corner cases for this function

        Raises:
            Error from datetime strptime
        """
        date = datetime.strptime(date_str, "%d/%b/%Y:%H:%M:%S")
        return date

    def parse(self, line):
        """
        Parse a string of apache log

        Args:
            line: string log in apache CLF format

        Returns:
            a dictionary with the informations contained
            in the log on Success; None otherwise.
        """
        if line is None:
            return
        match = self.main_regexp.match(line)
        if match is None:
            LOGGER.debug("Can not parse line: '%s'", line)
            return
        request_dict = match.groupdict()

        match = self.details_regexp.match(request_dict['request_details'])
        if match is None:
            LOGGER.debug("Can not parse request"
                         " information on line: '%s'", line)
            return

        request_dict['response_size'] = int(request_dict['response_size'])

        request_dict.update(match.groupdict())

        date_str = request_dict['date']
        try:
            date = self.parse_date(date_str[:-6])

            # parse timezone
            delta = timedelta(hours=int(date_str[-4:-2]),
                              minutes=int(date_str[-2:]))
            if date_str[-5] == '+':
                date += delta
            else:
                date -= delta
        except Exception:
            LOGGER.exception("Can not translate date '%s'", date_str)
            return

        request_dict['datetime'] = date
        LOGGER.debug("date %s translate into %s", date_str, date)

        return request_dict
