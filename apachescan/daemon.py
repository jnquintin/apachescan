#!/usr/bin/env python

import argparse
import os.path
import logging
import math

from apachescan.analyzer import AnalyzerFactory
from apachescan.reader.filehandler import CopyTruncateFile
from apachescan.controller import Controller
from apachescan.guard import Guard
from apachescan import parser

logger = logging.getLogger(os.path.basename(__file__))
AVAILABLE_KEYS = parser.apache.AVAILABLE_KEYS + ['section']


class Display():
    def __init__(self, most_common, print_empty_statistics=False):
        self.alarm_raised = False
        self.most_common = most_common
        self.print_empty_statistics = print_empty_statistics

    def process(self, date, analyzer, guard):
        if analyzer.nb_requests != 0 or self.print_empty_statistics:
            logger.info("Number of requests last alert interval: %s %s" %
                        (guard.get_value(), date))
            logger.info("%s:\n%s" %
                        (date, analyzer.compute_statistics(self.most_common)))

        if guard.is_threshold_reach() and not self.alarm_raised:
            logger.critical('High traffic generated an alert'
                            ' - hits = %s, triggered at %s' %
                            (guard.get_value(), date))
            self.alarm_raised = True
        if not guard.is_threshold_reach() and self.alarm_raised:
            logger.critical('Recover from high traffic'
                            ' - hits = %s, triggered at %s' %
                            (guard.get_value(), date))
            self.alarm_raised = False


def main():
    args_parser = argparse.ArgumentParser(
        description='Scans log from apache server in CLF format.')
    args_parser.add_argument('-f', '--filename', action='store',
                             type=str, default='/tmp/access.log',
                             help='File containing the logs to be analyzed')

    args_parser.add_argument('-r', '--remove-offset', action='store_true',
                             default=False,
                             help='Remove offset file and'
                             ' start from beginning')

    args_parser.add_argument('-o', '--offset-directory', action='store',
                             type=str, default=None,
                             help='File to store the last log analyzed.'
                             ' If None, the file ')

    args_parser.add_argument('-i', '--interval', action='store',
                             type=int, default=10,
                             help='Time delta use to compute statistics.'
                             'The value 0 disable the display of statistics.'
                             ' (default: %(default)s seconds)')

    args_parser.add_argument('-t', '--threshold', action='store',
                             type=int, default=10,
                             help='Alert when the number of request by seconds'
                             ' is higher than the threshold'
                             ' (default: %(default)s)')

    args_parser.add_argument('-a', '--alert-interval', action='store',
                             type=int, default=120,
                             help='Number of seconds used to compute the mean'
                             ' value for alerting. The alert interval is '
                             'rounded to a fix number of statistic interval.'
                             ' (default: %(default)s seconds)')

    args_parser.add_argument('-k', '--keys', action='append',
                             type=int, default=None,
                             choices=AVAILABLE_KEYS,
                             help='Alert when the number of request by seconds'
                             ' is higher than the threshold. If None is among'
                             ' the values, no key is considered.'
                             ' (default: ALL the keys)')
    args_parser.add_argument('--highest', action='store',
                             type=int, default=5,
                             help='Display the X highest keys.'
                             ' (Default: %(default)s)')
    args_parser.add_argument('-l', '--loop', action='store', type=int,
                             default=0,
                             help='Number of retry before stopping.'
                             ' If the value is 0, the command run forever'
                             ' (default: %(default)s)')
    args_parser.add_argument('--wait-time', action='store',
                             type=float, default=0.5,
                             help='Time to wait before reading new logs after'
                             ' reaching the last log.'
                             ' (default: %(default)s) seconds')
    args_parser.add_argument('--out-of-order', action='store', type=int,
                             default=10,
                             help='Maximal number of seconds a message can be'
                             ' delayed compare to others'
                             ' (default: %(default)s)')

    args_parser.add_argument('-w', '--warnings',
                             help="Print only alerts and warnings",
                             action="store_const", dest="loglevel",
                             const=logging.WARNING, default=logging.INFO)

    args_parser.add_argument('-d', '--debug', help="Display debug messages",
                             action="store_const", dest="loglevel",
                             const=logging.DEBUG)

    args = args_parser.parse_args()
    logging.basicConfig(level=args.loglevel)

    offset_filename = None
    if args.offset_directory is not None:
        offset_filename = os.path.join(
            args.offset_directory, args.filename + '.offset')
    else:
        offset_filename = args.filename + '.offset'

    if args.remove_offset:
        if os.path.exists(offset_filename):
            os.remove(offset_filename)

    reader = CopyTruncateFile(args.filename, offset_filename)

    if args.interval == 0:
        raise Exception("Option interval should be greater than 0")

    if args.alert_interval < args.interval:
        raise Exception("Option alert interval"
                        " shoud be greater than the interval")

    guard = Guard(int(args.alert_interval / args.interval),
                  args.threshold * args.alert_interval, None)
    if args.keys is None:
        keys = AVAILABLE_KEYS
    else:
        if None in args.keys:
            keys = []
        else:
            keys = args.keys
    analyzer_factory = AnalyzerFactory(keys)

    class RequestUpdater(object):
        """
        Compute the section with the content before the second '/'
        """

        def process(self, request):
            """
            Process the request to add additionnal information

            Args:
                request: apache request to update
            """
            page = request['page']
            # first character index after the first '/'
            first_index = page.find('/')
            if first_index == -1:
                request['section'] = page
                return request

            first_index += 1
            # find the second '/'
            second_index = page[first_index:].find('/')
            if second_index == -1:
                request['section'] = page
                return request

            # keep only up to the second '/'
            section = page[:second_index + first_index]
            request['section'] = section
            return request

    apache_parser = parser.apache.Parser()

    display = Display(args.highest)

    controller = Controller(args.interval,
                            int(math.ceil((args.interval + args.out_of_order) /
                                          args.interval)),
                            reader,
                            apache_parser,
                            RequestUpdater(),
                            analyzer_factory,
                            guard, display)

    controller.run(args.wait_time, args.loop)


if __name__ == "__main__":
    main()
