"""
Computes the alert based on the statistics computed by the analyzer.

The analyzer computes statistics over small intervals.
This module aggregates the information to have statistics over
larger intervals.

However the alerts are updated only at the frequency of the analyzer intervals
"""

import logging

from apachescan.exceptions import WrongArguments

LOGGER = logging.getLogger(__name__)


class WrongInterval(WrongArguments):
    """Guard wrong argument 'nb_intervals' should be greater than 0 """
    pass


class WrongThreshold(WrongArguments):
    """Guard wrong argument 'threshold' should not be None"""
    pass


class Guard(object):
    """
    Computes statistics over larger laps of time

    Args:
        nb_intervals: to be aggregated
        threshold:    after which an alert should be raised
        key:          to allow associate a name to the guard
    """

    def __init__(self, nb_intervals, threshold, key):
        if nb_intervals is None or nb_intervals <= 0:
            raise WrongInterval("nb_intervals value: %s" % nb_intervals)

        if threshold is None:
            raise WrongThreshold("threshold is None")

        # ring buffer to keep the value for each intervals
        # this buffer allow to recompute the information
        self.history = [0] * nb_intervals
        self.nb_intervals = nb_intervals
        # index for using the history buffer as a ring buffer
        self.current_index = 0
        self.threshold = threshold
        self.accumulate = 0
        self.key = key

    def _update_index(self):
        """
        Update the current index of the newest value
        """
        self.current_index = (self.current_index + 1) % self.nb_intervals

    def append(self, stat):
        """
        Aggregates the statistics to the new ones

        Args:
            stat: Statistics from the Analyzer
        """
        # instead of recomputing the sum every time
        # just update the value simply over the time
        # this method may lead to precision issue with floats
        self.accumulate -= self.history[self.current_index]
        self.history[self.current_index] = stat
        self.accumulate += self.history[self.current_index]
        self._update_index()

    def __str__(self):
        if self.is_threshold_reach():
            return "Limit reach with %s > %s" % \
                (self.get_value(), self.threshold)
        else:
            return "Limit not reach: %s <= %s" % \
                (self.get_value(), self.threshold)

    def is_threshold_reach(self):
        """
        Returns if the threshold has be reached

        Returns:
            True if the threshold has be reached: Otherwise False
        """
        return self.accumulate > self.threshold

    def get_value(self):
        """
        Returns the effective current value

        Returns:
            The number of requests in the aggregate interval
        """
        return self.accumulate

    def get_key(self):
        """
        Returns the key stored
        Returns:
            the key provided at the creation
        """
        return self.key
