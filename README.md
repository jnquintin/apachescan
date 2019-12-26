Apache Scanner
==============

Requirements
------------

    - Pygtail to read the log file continuously:
        * after a restart only new logs are read, thanks to an offset file
        * if the log file is copied and truncated pygtail with syslog,
        pygtail reads remaining logs in the copied file and continue on the truncate file
        * However if the file is just truncated, it does not works
    - six for the compatibility between python 2 and 3
    - datetime
    - argparse

Installation
------------

```bash
    python setup.py install
```

Content
-------

This package contains a apachascan python module and a command line apachescand.
The package is organized as follow:
    - apachescan
        * reader
            # iterates over the log
        * parser
            # converts the log into a dictionary
        * analyzer
            # computes statistics about the logs
        * guard
            # raises alert bases on the statistics 
        * controller
            # handles the data flow between the components up to the consumer
    - scripts
        * contains the daemon command
    - tests
        * contains the nosetests

Setup an example
----------------

An example of apache log can be found in the file: 'log\_example/access.log'

To avoid installing the module as root, set up a virtual environment or
run (change python version if required):

```bash
export PYTHONVERSION=2.7
export PYTHONPATH=$PYTHONPATH:$PWD/install/lib/python${PYTHONVERSION}/site-packages/
export PATH=$PATH:$PWD/install/bin/
python setup.py test
mkdir -p $PWD/install/lib/python2.7/site-packages/
python setup.py install --prefix $PWD/install
```

Note: the version of python depends of the system

Then to run the daemon on the example file:
```bash
    apachescand -f ./log_example/access.log -r  -l 1 
```

The options:
    - '-f' changes the log file name
    - '-r' removes the offset file to restart from the first log
    - '-l 1' stops after reaching the end of the file otherwise it will loop for ever

To log only the alerts and warning messages:
```bash
    apachescand -f ./log_example/access.log -r  -l 1 -w
```

The option:
    - '-w' displays warning and alert messages

To log the debug informations:
```bash
    apachescand -f ./log_example/access.log -r  -l 1 -d
```

The option:
    - '-d' displays debug informations

Design
------

### Flexibility

The chosen design is flexible by splitting the functionality by piece.

For example:
    - the format of the log change, only the parser is impacted and can be replaced
    - the logs are received from a socket only the reader is impacted and can be replaced

When developing this prototype the idea was to try have:
    - the possibility to receive message from sockets,
    - to connect it with influxDB to store the statistics and grafana to display them,
    - to send the statistics to another remote service.

### Memory and Computational Usage

From the computational cost point of view:
    - On each request:
        * parsing: conversion string to dictionary
        * analyzer: for each group do only constant number of operations
    - On each statistic interval:
        * analyzer: get the k most common key per group complexity
        in the worse case of O(n * log(n)) per group and for k lower than n: O(n * log(k))
        * guard: constant execution time only two operations

From the memory usage point of view:
    - Analyzer:
        * 2 intergers, one string per key in each group analyzed
        * depending on the out-of-order option;
        several analyzers are kept to handle out-of-order message.
        The option allows to use only one analyzer.
    - Guard:
        * one interger per statistic interval kept. For statistics computed every
        10 seconds and alert computed over 2 minutes, 120/10=12 integer are kept.

### Out of Order Messages

When logging message from several services or on a distributed platform the logs may
be received in the wrong order.
By using buckets of analyzer, the log can be set to the right one by just computing
its index.
The index computation is a real low computational cost.

However, this functionality requires some additional memory.
This option can be deactivated by setting the option '--out-of-order 0'.

### Possible improvements

The guard computes the alert over the statistics pre-computed over interval of 10 seconds.
The alerts are raised in a delay of 10 seconds and release by such too.
To raise the alert earlier, the design can be change to call the guard at each requests
and add a function to set the end of the interval like this the alert can be raise earlier.
The consumer can be call as soon as the guard raise the alert.

The design does not take into account that there is no log into intervals of time.
This allow additional delay in the log, however it delays alerts.
This can be handled in the main loop of the controller by enforcing the statistics computation
every X seconds.

