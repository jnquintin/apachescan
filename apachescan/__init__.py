"""
Apache Scan monitors the apache server usage by parsing the access log file

This module is organized for providing a good flexibility.

There is 5 sub-modules organized as following:
    - reader provides an iterator over the logs.
    - parser provides a dictionary with the informations about the last request
    - analyzer provides statistics about the requests
    - guard aggregates the statistics to raise alerts
    - controller handles the flow of data between the modules

The controller provides the summarized informations at the statistics
interval to a consumer.
The consumer may display message or store the informations.


"""
from .__version__ import __version__
