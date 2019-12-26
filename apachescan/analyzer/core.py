"""
Computes statistics about a set of requests

To reduce the memory foot print the number of request and
the size of the response are kept by groups.

The collections has a low memory foot print.
One integer for each possible value.
The computation of the most_common is small
O(n * log(k)) when keeping k elements.

The memory foot print may be reduces by having 2 integers for each possible
value. It would remove one reference by possible value.

Possible additional feature:
    - Computes the variance of the data sent by the server could be computed only.
"""

import logging
from collections import Counter
from six import string_types

LOGGER = logging.getLogger(__name__)


class Statistics(object):
    """
    Summarizes the Statistics computed by the analyzer
    """

    def __init__(self):
        # number of request in the interval
        self.nb_requests = 0
        # number of bytes sends by the server in the interval
        self.nb_bytes = 0
        # mean of bytes sends per requests
        self.mean_bytes = 0
        # number of requests for each value in the analyzed groups
        self.requests_by_groups = dict()
        # response size for each value in the analyzed groups
        self.bytes_by_groups = dict()

    def string(self, prefix, header=None):
        """
        Return a string summarize the computed statistics

        Args:
            prefix: for each line of the summary
            header: added to the string

        Returns:
            string with the statistics
        """
        string = "############### Statistics ##################\n"
        if header is not None:
            string += header.strip() + "\n"
        string += prefix + "Number of Requests: %s\n" % self.nb_requests
        string += prefix + "Total size:         %s Bytes\n" % self.nb_bytes
        string += prefix + "Mean request size:  %s Bytes\n" % self.mean_bytes

        for key in self.requests_by_groups:
            string += prefix + "Request summary for key '%s':\n" % key
            for result in self.requests_by_groups[key]:
                string += prefix + "\t '%s': %s requests\n" % result

        for key in self.bytes_by_groups:
            string += prefix + "Request size summary for key '%s':\n" % key
            for result in self.bytes_by_groups[key]:
                string += prefix + "\t '%s': %s requests\n" % result
        string += "############################################\n"
        return string

    def __str__(self):
        return self.string("")


class AnalyzerFactory(object):
    """
    Creates analyzer with the same parameters as the one provided

    Args:
        analyzed_groups: keys to be analyzed in the request
    """

    def __init__(self, analyzed_groups=None):
        self.analyzed_groups = analyzed_groups

    def get_analyzer(self):
        """
        Build an Analyzer with the same parameters

        Returns:
            new Analyzer
        """
        return Analyzer(self.analyzed_groups)


class Analyzer(object):
    """
    Compute statistics over the requests

    Args:
        analyzed_groups: keys to be analyzed in the request
    """

    def __init__(self, analyzed_groups):
        self.nb_requests = 0
        self.nb_bytes = 0
        self.request_counters = dict()
        self.size_counters = dict()

        if analyzed_groups is None:
            analyzed_groups = []

        if isinstance(analyzed_groups, string_types):
            analyzed_groups = [analyzed_groups]

        self.analyzed_groups = analyzed_groups

        for key in self.analyzed_groups:
            self.request_counters[key] = Counter()
            self.size_counters[key] = Counter()

    def add_request(self, request):
        """
            Aggregates the request to the statistics

            Notes:
                This method is called for each requests
                Its complexity should be kept low
        """
        request_size = request['response_size']
        self.nb_requests += 1
        self.nb_bytes += request_size

        # Update information for each analyzed keys
        # complexity O(k)
        # by considering the hash table to return the element in O(1)
        # i.e. no collision of the keys
        for key in self.analyzed_groups:
            self.request_counters[key].update([request[key]])
            self.size_counters[key].update({request[key]: request_size})

    def compute_statistics(self, most_common=3):
        """
        Compute the summary statistics

        Args:
            most_common: keeps only the most_common values

        Notes:
            This method is called only once per intervals by default
            every 10 seconds.
            Thus, the complexity of this method is less critical than
            the add_request.
        """
        statistics = Statistics()
        statistics.nb_requests = self.nb_requests
        statistics.nb_bytes = self.nb_bytes
        if self.nb_requests == 0:
            statistics.mean_bytes = 0
        else:
            statistics.mean_bytes = self.nb_bytes / self.nb_requests

        for key in self.analyzed_groups:
            # complexity of O(n * log(k)) with n the number of possible
            # value in the Counter and k the most_common value
            stats = self.request_counters[key].most_common(most_common)
            statistics.requests_by_groups[key] = stats
            stats = self.size_counters[key].most_common(most_common)
            statistics.bytes_by_groups[key] = stats
        return statistics
