import unittest
import sys

from apachescan.exceptions import WrongArguments
from apachescan.controller import Controller
from apachescan.analyzer import AnalyzerFactory
from apachescan.guard import Guard
from apachescan import parser


class OutOrderDisplay():
    def __init__(self, unittest, keys, alarm_array, alarm_down_array):
        self.total_request = 0
        self.nb_alert = 0
        self.alarm_raised = False
        self.unittest = unittest
        self.keys = keys
        self.alarm_array = alarm_array
        self.alarm_down_array = alarm_down_array

    def process(self, date, analyzer, guard):
        self.total_request += analyzer.nb_requests

        # if analyzer.nb_requests == 0:
        #     print("%s:\n%s" %
        #           (date, guard))
        # else:
        #     print("%s:\n%s\n%s" %
        #           (date, analyzer.compute_statistics(), guard))

        if analyzer.nb_requests != 0:
            self.unittest.assertLessEqual(analyzer.nb_requests, 2)
            stats = analyzer.compute_statistics()
            self.unittest.assertEqual(stats.nb_requests, 1)
            self.unittest.assertEqual(len(stats.requests_by_groups),
                                      len(self.keys))
            for key in stats.requests_by_groups:
                self.unittest.assertIn(key, self.keys)
                self.unittest.assertEqual(
                    len(stats.requests_by_groups[key]), 1)

            for key in stats.bytes_by_groups:
                self.unittest.assertIn(key, self.keys)
                self.unittest.assertEqual(len(stats.bytes_by_groups[key]), 1)

        if guard.is_threshold_reach() and not self.alarm_raised:
            self.unittest.assertIn(date, self.alarm_array)
            self.nb_alert += 1
            self.alarm_raised = True
        if not guard.is_threshold_reach() and self.alarm_raised:
            self.unittest.assertIn(date, self.alarm_down_array)
            self.alarm_raised = False


class Display():
    def __init__(self, unittest, keys, alarm_array, alarm_down_array):
        self.total_request = 0
        self.nb_alert = 0
        self.alarm_raised = False
        self.unittest = unittest
        self.keys = keys
        self.alarm_array = alarm_array
        self.alarm_down_array = alarm_down_array

    def process(self, date, analyzer, guard):
        self.total_request += analyzer.nb_requests

        # if analyzer.nb_requests == 0:
        #     print("%s:\n%s" %
        #           (date, guard))
        # else:
        #     print("%s:\n%s\n%s" %
        #           (date, analyzer.compute_statistics(), guard))

        if analyzer.nb_requests != 0:
            self.unittest.assertEqual(analyzer.nb_requests, 1)
            stats = analyzer.compute_statistics()
            self.unittest.assertEqual(stats.nb_requests, 1)
            self.unittest.assertEqual(len(stats.requests_by_groups),
                                      len(self.keys))
            for key in stats.requests_by_groups:
                self.unittest.assertIn(key, self.keys)
                self.unittest.assertEqual(
                    len(stats.requests_by_groups[key]), 1)

            for key in stats.bytes_by_groups:
                self.unittest.assertIn(key, self.keys)
                self.unittest.assertEqual(len(stats.bytes_by_groups[key]), 1)

        if guard.is_threshold_reach() and not self.alarm_raised:
            self.unittest.assertIn(date, self.alarm_array)
            self.nb_alert += 1
            self.alarm_raised = True
        if not guard.is_threshold_reach() and self.alarm_raised:
            self.unittest.assertIn(date, self.alarm_down_array)
            self.alarm_raised = False


class TestLogController(unittest.TestCase):
    def test_wrong_controller_arguments(self):
        apache_parser = parser.apache.Parser()
        logs_array = []
        guard = Guard(6, 1, None)

        analyzer_builder = AnalyzerFactory("section")

        display = Display(self, [], [], [])

        self.assertRaises(WrongArguments, Controller, -1, 2, logs_array,
                          apache_parser,
                          None,
                          analyzer_builder,
                          guard, display)
        self.assertRaises(WrongArguments, Controller, 0, 2, logs_array,
                          apache_parser,
                          None,
                          analyzer_builder,
                          guard, display)
        self.assertRaises(WrongArguments, Controller, 1, 0, logs_array,
                          apache_parser,
                          None,
                          analyzer_builder,
                          guard, display)
        self.assertRaises(WrongArguments, Controller, 1, 1, None,
                          apache_parser,
                          None,
                          analyzer_builder,
                          guard, display)
        self.assertRaises(WrongArguments, Controller, 1, 1, logs_array,
                          None,
                          None,
                          analyzer_builder,
                          guard, display)
        self.assertRaises(WrongArguments, Controller, 1, 1, logs_array,
                          apache_parser,
                          None,
                          None,
                          guard, display)
        self.assertRaises(WrongArguments, Controller, 1, 1, logs_array,
                          apache_parser,
                          None,
                          analyzer_builder,
                          None, display)
        self.assertRaises(WrongArguments, Controller, 1, 1, logs_array,
                          apache_parser,
                          None,
                          analyzer_builder,
                          guard, None)

    def test_controller_out_order_message(self):
        # for the test the statistics are computed every 10s (named interval)
        # an alarm is raised when there is more than 2 requests in 6 intervals in row
        # i.e. in 1 min
        #
        # alarm should raise at:
        # 24/Dec/2019:21:11:57 +0100
        # 24/Dec/2019:21:16:12 +0100
        # 24/Dec/2019:21:42:11 +0100
        # 24/Dec/2019:22:17:58 +0100
        # 24/Dec/2019:22:29:43 +0100
        # 24/Dec/2019:22:45:05 +0100
        # rounded to
        # 24/Dec/2019:21:11:50 +0100
        # 24/Dec/2019:21:16:10 +0100
        # 24/Dec/2019:21:42:10 +0100
        # 24/Dec/2019:22:17:50 +0100
        # 24/Dec/2019:22:29:40 +0100
        # 24/Dec/2019:22:45:00 +0100
        #
        # not raised 24/Dec/2019:22:37:30
        # because the number of request is considered in the 6 intervals
        # the row of 6 intervals are:
        #   - 24/Dec/2019:22:36:30 +0100 to 24/Dec/2019:22:37:29 +0100 (only one request)
        #   - 24/Dec/2019:22:36:40 +0100 to 24/Dec/2019:22:37:39 +0100 (only one request)
        #
        # the third and second log are out of order, the controller should handle it

        apache_parser = parser.apache.Parser()
        alarm_array = [
            apache_parser.parse_date("24/Dec/2019:22:11:50"),
            apache_parser.parse_date("24/Dec/2019:22:16:40"),
            apache_parser.parse_date("24/Dec/2019:22:42:10"),
            apache_parser.parse_date("24/Dec/2019:23:17:50"),
            apache_parser.parse_date("24/Dec/2019:23:29:40"),
            apache_parser.parse_date("24/Dec/2019:23:45:00"),
        ]
        alarm_down_array = [
            apache_parser.parse_date("24/Dec/2019:22:12:40"),
            apache_parser.parse_date("24/Dec/2019:22:17:10"),
            apache_parser.parse_date("24/Dec/2019:22:42:20"),
            apache_parser.parse_date("24/Dec/2019:23:18:00"),
            apache_parser.parse_date("24/Dec/2019:23:29:50"),
            apache_parser.parse_date("24/Dec/2019:23:45:30"),
        ]

        logs_string = """3.102.108.241 - - [24/Dec/2019:21:06:56 +0100] "GET /search/tag/list HTTP/1.0" 200 5006
246.39.109.158 - - [24/Dec/2019:21:11:57 +0100] "GET /list/posts/explore HTTP/1.0" 200 5007
53.146.196.230 - - [24/Dec/2019:21:11:45 +0100] "GET /list HTTP/1.0" 200 5007
169.115.37.82 - - [24/Dec/2019:21:15:11 +0100] "GET /list HTTP/1.0" 200 4969
39.22.190.138 - - [24/Dec/2019:21:16:12 +0100] "GET /app/main/posts HTTP/1.0" 200 5007
131.242.185.90 - - [24/Dec/2019:21:16:45 +0100] "PUT /wp-admin HTTP/1.0" 301 4985
72.163.17.221 - - [24/Dec/2019:21:18:58 +0100] "PUT /wp-content HTTP/1.0" 200 5010
242.69.100.22 - - [24/Dec/2019:21:21:29 +0100] "GET /app/main/posts HTTP/1.0" 200 5039
227.193.3.107 - - [24/Dec/2019:21:22:24 +0100] "GET /app/main/posts HTTP/1.0" 200 4924
145.140.220.28 - - [24/Dec/2019:21:26:59 +0100] "GET /app/main/posts HTTP/1.0" 200 5053
75.52.20.153 - - [24/Dec/2019:21:31:20 +0100] "GET /wp-admin HTTP/1.0" 301 5088
114.86.39.197 - - [24/Dec/2019:21:35:23 +0100] "PUT /app/main/posts HTTP/1.0" 500 5036
19.188.117.71 - - [24/Dec/2019:21:39:08 +0100] "GET /posts/posts/explore HTTP/1.0" 200 4943
116.191.140.14 - - [24/Dec/2019:21:41:28 +0100] "PUT /search/tag/list HTTP/1.0" 200 4939
69.136.17.189 - - [24/Dec/2019:21:42:11 +0100] "GET /app/main/posts HTTP/1.0" 200 4986
209.3.236.41 - - [24/Dec/2019:21:46:19 +0100] "GET /explore HTTP/1.0" 200 4980
231.159.240.61 - - [24/Dec/2019:21:50:38 +0100] "GET /wp-content HTTP/1.0" 200 4930
30.220.64.89 - - [24/Dec/2019:21:54:36 +0100] "PUT /apps/cart.jsp?appID=7851 HTTP/1.0" 301 5083
147.226.28.156 - - [24/Dec/2019:21:56:57 +0100] "GET /list HTTP/1.0" 200 5038
62.68.69.123 - - [24/Dec/2019:21:59:52 +0100] "GET /wp-admin HTTP/1.0" 200 5050
75.90.152.231 - - [24/Dec/2019:22:02:41 +0100] "POST /wp-content HTTP/1.0" 200 4935
103.73.254.19 - - [24/Dec/2019:22:06:28 +0100] "POST /explore HTTP/1.0" 200 5025
89.179.111.71 - - [24/Dec/2019:22:10:57 +0100] "GET /explore HTTP/1.0" 200 5045
158.193.106.210 - - [24/Dec/2019:22:14:51 +0100] "PUT /search/tag/list HTTP/1.0" 200 4902
86.153.15.141 - - [24/Dec/2019:22:17:06 +0100] "GET /search/tag/list HTTP/1.0" 200 5068
49.105.193.97 - - [24/Dec/2019:22:17:58 +0100] "GET /posts/posts/explore HTTP/1.0" 200 4994
4.197.78.58 - - [24/Dec/2019:22:22:16 +0100] "GET /search/tag/list HTTP/1.0" 200 4956
130.142.137.221 - - [24/Dec/2019:22:24:19 +0100] "GET /wp-content HTTP/1.0" 500 5065
67.100.63.54 - - [24/Dec/2019:22:25:48 +0100] "GET /search/tag/list HTTP/1.0" 200 5049
135.23.110.86 - - [24/Dec/2019:22:27:23 +0100] "GET /posts/posts/explore HTTP/1.0" 200 4941
199.155.79.182 - - [24/Dec/2019:22:28:50 +0100] "PUT /app/main/posts HTTP/1.0" 200 5070
10.229.27.28 - - [24/Dec/2019:22:29:43 +0100] "GET /app/main/posts HTTP/1.0" 404 5025
204.140.167.197 - - [24/Dec/2019:22:32:25 +0100] "DELETE /wp-content HTTP/1.0" 200 5003
49.185.82.138 - - [24/Dec/2019:22:36:31 +0100] "PUT /app/main/posts HTTP/1.0" 200 5003
249.131.83.40 - - [24/Dec/2019:22:37:30 +0100] "DELETE /wp-content HTTP/1.0" 200 5043
249.131.83.40 - - [24/Dec/2019:22:38:30 +0100] "DELETE /wp-content HTTP/1.0" 200 5043
235.21.193.81 - - [24/Dec/2019:22:40:43 +0100] "GET /search/tag/list HTTP/1.0" 301 5045
119.88.2.184 - - [24/Dec/2019:22:43:29 +0100] "GET /apps/cart.jsp?appID=8771 HTTP/1.0" 200 5030
75.30.112.203 - - [24/Dec/2019:22:44:30 +0100] "PUT /search/tag/list HTTP/1.0" 200 5068
196.22.126.183 - - [24/Dec/2019:22:45:05 +0100] "DELETE /search/tag/list HTTP/1.0" 404 4984
191.85.37.204 - - [24/Dec/2019:22:46:38 +0100] "GET /posts/posts/explore HTTP/1.0" 200 4981
6.185.185.40 - - [24/Dec/2019:22:49:55 +0100] "GET /wp-content HTTP/1.0" 200 5028
178.19.69.97 - - [24/Dec/2019:22:51:04 +0100] "PUT /wp-admin HTTP/1.0" 301 4996
186.27.220.235 - - [24/Dec/2019:22:52:48 +0100] "GET /list HTTP/1.0" 200 4968
49.226.159.16 - - [24/Dec/2019:22:57:36 +0100] "GET /explore HTTP/1.0" 301 5018
21.208.248.218 - - [24/Dec/2019:23:02:03 +0100] "POST /explore HTTP/1.0" 200 5034
42.253.54.222 - - [24/Dec/2019:23:03:41 +0100] "DELETE /search/tag/list HTTP/1.0" 200 5089
64.144.49.59 - - [24/Dec/2019:23:07:07 +0100] "PUT /apps/cart.jsp?appID=9264 HTTP/1.0" 200 4935
106.181.223.111 - - [24/Dec/2019:23:11:28 +0100] "PUT /app/main/posts HTTP/1.0" 200 4969
12.30.184.103 - - [24/Dec/2019:23:12:51 +0100] "GET /wp-content HTTP/1.0" 200 4932
86.47.203.130 - - [24/Dec/2019:23:14:48 +0100] "GET /wp-admin HTTP/1.0" 200 4941 """
        logs_array = logs_string.split('\n')

        # raise alarm if there is more than 1 request over 6 intervals
        # the interval are
        guard = Guard(6, 1, None)

        total_request = 0

        analyzer_builder = AnalyzerFactory()

        display = OutOrderDisplay(self, [], alarm_array, alarm_down_array)

        # create intervals of 10 seconds
        # compute two intervals in
        # // (i.e. a message can arrive with 10 seconds late and not be out of order)
        controller = Controller(10, 3, logs_array,
                                apache_parser, None, analyzer_builder,
                                guard, display)
        nb_request = controller.run_once()
        del controller
        self.assertEqual(nb_request, len(logs_array))
        self.assertEqual(display.total_request, len(logs_array))
        self.assertEqual(display.nb_alert, len(alarm_array))

    def test_controller_functionnal_behavior(self):

        # for the test the statistics are computed every 10s (named interval)
        # an alarm is raised when there is more than 2 requests in 6 intervals in row
        # i.e. in 1 min
        #
        # alarm should raise at:
        # 24/Dec/2019:21:11:45 +0100
        # 24/Dec/2019:21:16:12 +0100
        # 24/Dec/2019:21:42:11 +0100
        # 24/Dec/2019:22:17:58 +0100
        # 24/Dec/2019:22:29:43 +0100
        # 24/Dec/2019:22:45:05 +0100
        # rounded to
        # 24/Dec/2019:21:11:40 +0100
        # 24/Dec/2019:21:16:10 +0100
        # 24/Dec/2019:21:42:10 +0100
        # 24/Dec/2019:22:17:50 +0100
        # 24/Dec/2019:22:29:40 +0100
        # 24/Dec/2019:22:45:00 +0100
        #
        # not raised 24/Dec/2019:22:37:30
        # because the number of request is considered in the 6 intervals
        # the row of 6 intervals are:
        #   - 24/Dec/2019:22:36:30 +0100 to 24/Dec/2019:22:37:29 +0100 (only one request)
        #   - 24/Dec/2019:22:36:40 +0100 to 24/Dec/2019:22:37:39 +0100 (only one request)

        apache_parser = parser.apache.Parser()
        alarm_array = [
            apache_parser.parse_date("24/Dec/2019:22:11:40"),
            apache_parser.parse_date("24/Dec/2019:22:16:40"),
            apache_parser.parse_date("24/Dec/2019:22:42:10"),
            apache_parser.parse_date("24/Dec/2019:23:17:50"),
            apache_parser.parse_date("24/Dec/2019:23:29:40"),
            apache_parser.parse_date("24/Dec/2019:23:45:00"),
        ]
        alarm_down_array = [
            apache_parser.parse_date("24/Dec/2019:22:12:00"),
            apache_parser.parse_date("24/Dec/2019:22:17:10"),
            apache_parser.parse_date("24/Dec/2019:22:42:20"),
            apache_parser.parse_date("24/Dec/2019:23:18:00"),
            apache_parser.parse_date("24/Dec/2019:23:29:50"),
            apache_parser.parse_date("24/Dec/2019:23:45:30"),
        ]

        logs_string = """3.102.108.241 - - [24/Dec/2019:21:06:56 +0100] "GET /search/tag/list HTTP/1.0" 200 5006
246.39.109.158 - - [24/Dec/2019:21:11:07 +0100] "GET /posts/posts/explore HTTP/1.0" 200 5007
53.146.196.230 - - [24/Dec/2019:21:11:45 +0100] "GET /list HTTP/1.0" 200 5007
169.115.37.82 - - [24/Dec/2019:21:15:11 +0100] "GET /list HTTP/1.0" 200 4969
39.22.190.138 - - [24/Dec/2019:21:16:12 +0100] "GET /app/main/posts HTTP/1.0" 200 5007
131.242.185.90 - - [24/Dec/2019:21:16:45 +0100] "PUT /wp-admin HTTP/1.0" 301 4985
72.163.17.221 - - [24/Dec/2019:21:18:58 +0100] "PUT /wp-content HTTP/1.0" 200 5010
242.69.100.22 - - [24/Dec/2019:21:21:29 +0100] "GET /app/main/posts HTTP/1.0" 200 5039
227.193.3.107 - - [24/Dec/2019:21:22:24 +0100] "GET /app/main/posts HTTP/1.0" 200 4924
145.140.220.28 - - [24/Dec/2019:21:26:59 +0100] "GET /app/main/posts HTTP/1.0" 200 5053
75.52.20.153 - - [24/Dec/2019:21:31:20 +0100] "GET /wp-admin HTTP/1.0" 301 5088
114.86.39.197 - - [24/Dec/2019:21:35:23 +0100] "PUT /app/main/posts HTTP/1.0" 500 5036
19.188.117.71 - - [24/Dec/2019:21:39:08 +0100] "GET /posts/posts/explore HTTP/1.0" 200 4943
116.191.140.14 - - [24/Dec/2019:21:41:28 +0100] "PUT /search/tag/list HTTP/1.0" 200 4939
69.136.17.189 - - [24/Dec/2019:21:42:11 +0100] "GET /app/main/posts HTTP/1.0" 200 4986
209.3.236.41 - - [24/Dec/2019:21:46:19 +0100] "GET /explore HTTP/1.0" 200 4980
231.159.240.61 - - [24/Dec/2019:21:50:38 +0100] "GET /wp-content HTTP/1.0" 200 4930
30.220.64.89 - - [24/Dec/2019:21:54:36 +0100] "PUT /apps/cart.jsp?appID=7851 HTTP/1.0" 301 5083
147.226.28.156 - - [24/Dec/2019:21:56:57 +0100] "GET /list HTTP/1.0" 200 5038
62.68.69.123 - - [24/Dec/2019:21:59:52 +0100] "GET /wp-admin HTTP/1.0" 200 5050
75.90.152.231 - - [24/Dec/2019:22:02:41 +0100] "POST /wp-content HTTP/1.0" 200 4935
103.73.254.19 - - [24/Dec/2019:22:06:28 +0100] "POST /explore HTTP/1.0" 200 5025
89.179.111.71 - - [24/Dec/2019:22:10:57 +0100] "GET /explore HTTP/1.0" 200 5045
158.193.106.210 - - [24/Dec/2019:22:14:51 +0100] "PUT /search/tag/list HTTP/1.0" 200 4902
86.153.15.141 - - [24/Dec/2019:22:17:06 +0100] "GET /search/tag/list HTTP/1.0" 200 5068
49.105.193.97 - - [24/Dec/2019:22:17:58 +0100] "GET /posts/posts/explore HTTP/1.0" 200 4994
4.197.78.58 - - [24/Dec/2019:22:22:16 +0100] "GET /search/tag/list HTTP/1.0" 200 4956
130.142.137.221 - - [24/Dec/2019:22:24:19 +0100] "GET /wp-content HTTP/1.0" 500 5065
67.100.63.54 - - [24/Dec/2019:22:25:48 +0100] "GET /search/tag/list HTTP/1.0" 200 5049
135.23.110.86 - - [24/Dec/2019:22:27:23 +0100] "GET /posts/posts/explore HTTP/1.0" 200 4941
199.155.79.182 - - [24/Dec/2019:22:28:50 +0100] "PUT /app/main/posts HTTP/1.0" 200 5070
10.229.27.28 - - [24/Dec/2019:22:29:43 +0100] "GET /app/main/posts HTTP/1.0" 404 5025
204.140.167.197 - - [24/Dec/2019:22:32:25 +0100] "DELETE /wp-content HTTP/1.0" 200 5003
49.185.82.138 - - [24/Dec/2019:22:36:31 +0100] "PUT /app/main/posts HTTP/1.0" 200 5003
249.131.83.40 - - [24/Dec/2019:22:37:30 +0100] "DELETE /wp-content HTTP/1.0" 200 5043
249.131.83.40 - - [24/Dec/2019:22:38:30 +0100] "DELETE /wp-content HTTP/1.0" 200 5043
235.21.193.81 - - [24/Dec/2019:22:40:43 +0100] "GET /search/tag/list HTTP/1.0" 301 5045
119.88.2.184 - - [24/Dec/2019:22:43:29 +0100] "GET /apps/cart.jsp?appID=8771 HTTP/1.0" 200 5030
75.30.112.203 - - [24/Dec/2019:22:44:30 +0100] "PUT /search/tag/list HTTP/1.0" 200 5068
196.22.126.183 - - [24/Dec/2019:22:45:05 +0100] "DELETE /search/tag/list HTTP/1.0" 404 4984
191.85.37.204 - - [24/Dec/2019:22:46:38 +0100] "GET /posts/posts/explore HTTP/1.0" 200 4981
6.185.185.40 - - [24/Dec/2019:22:49:55 +0100] "GET /wp-content HTTP/1.0" 200 5028
178.19.69.97 - - [24/Dec/2019:22:51:04 +0100] "PUT /wp-admin HTTP/1.0" 301 4996
186.27.220.235 - - [24/Dec/2019:22:52:48 +0100] "GET /list HTTP/1.0" 200 4968
49.226.159.16 - - [24/Dec/2019:22:57:36 +0100] "GET /explore HTTP/1.0" 301 5018
21.208.248.218 - - [24/Dec/2019:23:02:03 +0100] "POST /explore HTTP/1.0" 200 5034
42.253.54.222 - - [24/Dec/2019:23:03:41 +0100] "DELETE /search/tag/list HTTP/1.0" 200 5089
64.144.49.59 - - [24/Dec/2019:23:07:07 +0100] "PUT /apps/cart.jsp?appID=9264 HTTP/1.0" 200 4935
106.181.223.111 - - [24/Dec/2019:23:11:28 +0100] "PUT /app/main/posts HTTP/1.0" 200 4969
12.30.184.103 - - [24/Dec/2019:23:12:51 +0100] "GET /wp-content HTTP/1.0" 200 4932
12.30.184.103 - - [23/Dec/2019:23:12:51 +0100] "GET /wp-content HTTP/1.0" 200 4932
86.47.203.130 - - [24/Dec/2019:23:14:48 +0100] "GET /wp-admin HTTP/1.0" 200 4941 """
        logs_array = logs_string.split('\n')

        # raise alarm if there is more than 1 request over 6 intervals
        # the interval are
        guard = Guard(6, 1, None)

        total_request = 0

        analyzer_builder = AnalyzerFactory()

        display = Display(self, [], alarm_array, alarm_down_array)

        # create intervals of 10 seconds
        # compute two intervals in
        # // (i.e. a message can arrive with 10 seconds late and not be out of order)
        controller = Controller(10, 2, logs_array,
                                apache_parser, None, analyzer_builder,
                                guard, display)
        nb_request = controller.run_once()
        del controller
        self.assertEqual(nb_request, len(logs_array))
        self.assertEqual(display.total_request,
                         len(logs_array)-1)  # One log is too old
        self.assertEqual(display.nb_alert, len(alarm_array))

        guard = Guard(6, 1, None)
        nb_request = 0
        display = Display(self, ['section'], alarm_array, alarm_down_array)

        analyzer_builder = AnalyzerFactory("section")

        # create intervals of 10 seconds
        # compute two intervals in
        # // (i.e. a message can arrive with 10 seconds late and not be out of order)
        class RequestUpdater(object):
            def process(self, x):
                x['section'] = '/'.join([x["page"].split('/')[1]])
                return x

        controller = Controller(10, 2, logs_array,
                                apache_parser,
                                RequestUpdater(),
                                analyzer_builder,
                                guard, display)
        nb_request = controller.run_once()
        del controller
        self.assertEqual(nb_request, len(logs_array))
        self.assertEqual(display.total_request,
                         len(logs_array) - 1)  # One log is too old
        self.assertEqual(display.nb_alert, len(alarm_array))

        logs_array = []
        controller = Controller(10, 2, logs_array,
                                apache_parser,
                                RequestUpdater(),
                                analyzer_builder,
                                guard, display)
        nb_request = controller.run_once()
        del controller
        self.assertEqual(nb_request, len(logs_array))

        controller = Controller(10, 2, logs_array,
                                apache_parser,
                                RequestUpdater(),
                                analyzer_builder,
                                guard, display)
        nb_request = controller.run(0.1, 2)
        del controller


if __name__ == "__main__":
    unittest.main()
