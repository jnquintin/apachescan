"""
This Module organizes the interaction between others modules.

This module is the main part which Calls:
    - The reader to handle the logs; currently coming from a file.
    In the future a socket could be connected.
    - The parser split the information contains in the logs.
    - The interpreter that filters/adds informations from the request.
    - The Analyzer which computes online statistics
    - The Guard which aggregates the statistics over a larger period to
    raise alerts.
    - The Consumer which outputs the informations

The main feature of this module is to handle messages that can be out of order.
This is handled by selecting the right interval for each log/requests.
The overhead of this feature is only in memory.

For example, when computing statistics over the last 10 seconds,
by keeping 2 Analyzer, a message can be delayed by 10 seconds,

The second disadvantage is the delay in statistics display.

Both of them could be removed by setting the number of interval to 1.

In the current design, the statistics are computed only if log are received.
In the main loop, a date update can be done as it is in the __del__ function
to have more reactivity.
"""
import datetime
import logging
import time

from apachescan.exceptions import WrongArguments

LOGGER = logging.getLogger(__name__)


class WrongInterval(WrongArguments):
    """Wrong configuration of interval statistics"""
    pass


class MissingHandler(WrongArguments):
    """Missing handler for computing statistics"""
    pass


class EmptyRequestInterpreter(object):
    """
    Default interpreter of request which does nothing
    """

    @staticmethod
    def process(request):
        """
        Return the provided request

        Args:
            request returned
        """
        return request


class Controller(object):
    """
    The controller iterates over the logs to parse, interpret,
    compute statistics, compute alerts, and output informations.
    This is done by calling the different components over the logs.

    Args:
        statistic_interval:  number of seconds the log
                             should be aggregate for computing statistics
        nb_interval:         number of statistics set kept before displaying it
                             (allow out of order messages)
        reader:              provides logs
        parser:              translates logs into request dictionary
        request_interpreter: adds information to the request
        analyzer_factory:    creates request analyzers which compute statistics
                             over requests
        guard:               computes alert based on the statistics
        consumer:             outputs information to console, file, or socket

    Returns:
        Controller object
    """

    def __init__(self, statistic_interval,
                 nb_interval,
                 reader, parser,
                 request_interpreter,
                 analyzer_factory,
                 guard, consumer):

        # dates at which the interval starts
        # this will be transform into an array when the first log is received
        # buffer used as a ring buffer
        self.dates = None

        if nb_interval <= 0:
            raise WrongInterval("nb_interval %s <= 0" % nb_interval)

        if statistic_interval <= 0:
            raise WrongInterval("statistic_interval %s <= 0" %
                                statistic_interval)
        if reader is None:
            raise MissingHandler("reader is None")
        if analyzer_factory is None:
            raise MissingHandler("analyzer_factory is None")
        if parser is None:
            raise MissingHandler("parser is None")
        if guard is None:
            raise MissingHandler("guard is None")
        if consumer is None:
            raise MissingHandler("consumer is None")

        self.statistic_interval = statistic_interval
        self.statistic_interval_delta = datetime.timedelta(
            seconds=statistic_interval)
        LOGGER.debug("Computes statistics every %s seconds",
                     statistic_interval)

        self.nb_interval = nb_interval
        LOGGER.debug("Keep %s interval at the same time to "
                     "allow out of order messages",
                     nb_interval)

        self.reader = reader
        self.parser = parser
        self.request_interpreter = request_interpreter

        if self.request_interpreter is None:
            self.request_interpreter = EmptyRequestInterpreter()

        self.analyzer_factory = analyzer_factory
        self.guard = guard
        self.analyzers = []
        self.consumer = consumer

        # Create one Analyzer per interval
        # Each time the interval is output the Analyzer is recreated
        # buffer used as a ring buffer
        for _ in range(self.nb_interval):
            self.analyzers.append(analyzer_factory.get_analyzer())

        # index of the most recent interval
        self.lastest_index = 0
        self.first_date = None

    def _truncate_date(self, date):
        """
        Truncates the date to have statistics computed on nice intervals
        For example if the statistics are computed every 10 seconds,
        the date will have a number of seconds multiple of 10.

        Args:
            date: to be truncated

        Returns:
            date truncated depending on the statistics intervals
        """
        new_date = date
        new_date.replace(microsecond=0)
        new_date.replace(microsecond=0)
        seconds = (new_date.minute * 60 + new_date.second)
        seconds = int(seconds / self.statistic_interval) * \
            self.statistic_interval
        new_date = new_date.replace(minute=int(seconds/60))
        new_date = new_date.replace(second=seconds % 60)
        return new_date

    def _initialize_date(self, date):
        """
        Depending on the first log date compute the interval date

        Args:
            date: of the first log
        """
        if self.dates is None:
            self.first_date = date
            self.dates = []
            first_date = self._truncate_date(date)
            LOGGER.debug("First time considered %s", first_date)
            max_delta = datetime.timedelta(seconds=self.statistic_interval *
                                           (self.nb_interval - 1))
            oldest_date = first_date - max_delta
            for i in range(self.nb_interval):
                delta_time = datetime.timedelta(
                    seconds=self.statistic_interval * i)
                self.dates.append(oldest_date + delta_time)
                LOGGER.debug("date at index %s = %s", i, self.dates[-1])

    def _update_intervals(self, date):
        """
        Remove intervals that are too old compare depending on the new date

        Args:
            date: new date to be inserted
        """
        # while the new date is not reach continue to remove previous
        # Analyzer
        while (date >= self.dates[self.lastest_index]
                + self.statistic_interval_delta):
            oldest_index = self.oldest_index()
            LOGGER.debug("remove interval of date %s",
                         self.dates[oldest_index])

            # Updates the first date if some request have been received before
            if (self.dates[oldest_index] < self.first_date and
                    self.analyzers[oldest_index].nb_requests != 0):
                self.first_date = self.dates[oldest_index]
                LOGGER.debug("Update first time to %s", self.first_date)

            # Computes statistics only for intervals after the first log
            if self.dates[oldest_index] >= self.first_date:
                LOGGER.debug("Update compute statistics for date %s",
                             self.dates[oldest_index])
                # Call the guard to update mean statistics
                # over the alert interval
                self.guard.append(self.analyzers[oldest_index].nb_requests)
                self.consumer.process(self.dates[oldest_index],
                                      self.analyzers[oldest_index],
                                      self.guard)

            next_index = oldest_index
            self.dates[next_index] = self.dates[self.lastest_index] + \
                self.statistic_interval_delta

            self.analyzers[next_index] = self.analyzer_factory.get_analyzer()
            self.lastest_index = next_index

    def next_index(self, index):
        """
        Computes the next index of the ring buffers (dates and analyzers)

        Args:
            index: current index

        Returns:
            the following index
        """
        return (index + 1) % self.nb_interval

    def oldest_index(self):
        """
        Returns the oldest index
        """
        return self.next_index(self.lastest_index)

    def get_interval(self, date):
        """
        Computes the interval index in which the date fit

        Args:
            date: of the log

        Returns:
            index of the interval if found; if not found, None is returned

        Notes:
            This function calls _update_intervals so the interval
            should be found; Unless the date is too old.
        """
        self._update_intervals(date)
        index = self.oldest_index()
        deltat = (date - self.dates[index]).total_seconds()
        increment = int(deltat / self.statistic_interval)
        index = (index + increment) % self.nb_interval

        # Check that the computed is the right one
        if (date < self.dates[index] or
                date >= self.dates[index] + self.statistic_interval_delta):
            LOGGER.warning("Computed interval is wrong the equation "
                           "'%s <= %s < %s' is not True ",
                           self.dates[index], date,
                           self.dates[index] + self.statistic_interval_delta)
            return None

        return index

    def __del__(self):
        """
        Fake processing an log in the future to consume
        remaining statistics information.
        """
        if self.dates is None:
            return

        future_date = self.dates[self.lastest_index]
        future_date += self.statistic_interval_delta * self.nb_interval
        self._update_intervals(future_date)

    def run(self, wait, nb_loop=0):
        """
        Computes logs in loop

        Args:
            wait:       time to wait after computing all the logs
            nb_loop:    number of loop before existing (0 means infinity).
        """
        iteration = 0
        while nb_loop == 0 or nb_loop > iteration:
            iteration += 1
            nb_requests = self.run_once()

            if nb_requests == 0:
                LOGGER.debug("Wait for new incoming logs")
                time.sleep(wait)

    def run_once(self):
        """
        Iterates over all the logs
        """

        nb_requests = 0
        nb_computed_requests = 0

        # Reads logs
        for line in self.reader:
            nb_requests += 1

            # Interprets the line as a request
            request = self.parser.parse(line)
            if request is None:
                LOGGER.debug("Line '%s' has not be parsed correctly", line)
                continue

            # Populates request with additional informations
            request = self.request_interpreter.process(request)
            if request is None:
                LOGGER.debug("Line '%s' has not be"
                             " interpreted correctly", line)
                continue

            # Updates the controller state depending on the request date
            date = request['datetime']
            self._initialize_date(date)

            # Checks the log may fit into one interval
            if date < self.dates[self.oldest_index()]:
                LOGGER.warning("Receive Message too old ignore it;"
                               " message date %s < oldest date %s ",
                               date, self.dates[self.oldest_index()])
                continue

            # Gets the interval index for the request
            interval_index = self.get_interval(date)
            if interval_index is None:
                LOGGER.debug("Invalid index computed")
                continue

            nb_computed_requests += 1
            # Computes statistics about the request
            self.analyzers[interval_index].add_request(request)

        # return the number of logs handles
        LOGGER.debug("Computed %s/%s requests",
                     nb_computed_requests, nb_requests)
        return nb_requests
