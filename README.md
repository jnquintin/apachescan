Apache Scanner
==============

Requirements
------------

The module requires:
    - Pygtail to read the log file continuously:
        + take back from previous log when log rotate with copyandtruncate option is activated
        + if the log is copy and truncated pygtail continue to read logs remaining in the copy and in the truncated file
        + However if the file is just truncate it does not works
    - six for the compatibility between python 2 and 3
    - unittests
    - argparse

Installation
------------

In a terminal, run the command:
    - python setup.py install

Content
-------

This package contains a python module and a command line apachescand.
The package is organized as following:
    - apachescan
        + reader
            # iterates over the log
        + parser
            # converts the log into a dictionnary
        + analyzer
            # computes statistics about the logs
        + guard
            # raises alert bases on the statistics 
        + controller
            # handle the data flow between the components up to the consumer
    - scripts
        + contains the deamon command
    - tests
        + contains the nosetests

Setup an example
----------------

An example of apache log can be found in the file: log_example/access.log

To avoid installing the module as root, run:
    - python setup.py install --prefix $PWD/install
    - export PYTHONPATH=$PYTHONPATH:$PWD/install/lib/python2.7/site-packages/
    - export PATH=$PATH:$PWD/install/bin/

Note: the version of python depends of the system

Then to run the deamon on the example file:
    - apachescand -f ./log_example/access.log -r  -l 1 

The options:
    - '-f' to set the filename
    - '-r' to not take into account the offset file (avoid to redo nothing if run once)
    - '-l 1' stop after reaching the end of the file otherwise it will hang for ever

Design
------

The design is flexible and has a low computation cost.

The flexibility comes from the fact that each functionality is split and bounded.

For example:
    - the format of the log change, only the parser is impacted and can be replaced
    - the logs are received from a socket only the reader is impacted and can be replaced

When developing this prototype the idea was to connect it with influxDB to store the
statistics and grafana to display them. The statistics can also be send to another 
service to aggregate the information from several daemons like this one.
For doing it only the consumer provided to the controller has to be adapted.

The design takes into account the ability to receive message in out-of-order.
To handle this, only some additional memory is required, the computational cost is the same.
However the alert may be delayed in this case. This option can be deactivated
by setting the option '--out-of-order 0'.

The guard computes the alert over the statistics pre-computed over interval of 10 seconds.
The alerts are raised in a delay of 10 seconds and release by such too.

The design does not take into account that log are not received.
This allow additional delay in the log, however it adds delays for the alerts.
This can be handle in the loop of the controller by enforcing the statistics computation
every X seconds.

To raise the alert earlier, the design can be change to call the guard at each requests
and add a function to set the end of the interval like this the alert can be raise earlier.
The consumer can be call as soos as the guard raise the alert.




