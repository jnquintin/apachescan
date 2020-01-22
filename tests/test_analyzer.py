import unittest
from apachescan.analyzer import AnalyzerFactory
import sys

AVAILABLE_KEYS = ["ip", "local_user", "remote_user",
                  "date", "datetime", "action", "page", "protocol",
                  "status_code", "response_size"]


class TestLogAnalyzer(unittest.TestCase):

    def test_analyzer(self):
        default_request = {"ip": None, "local_user": None, "remote_user": None,
                           "date": None, "datetime": None,
                           "action": "GET", "page": "/index.html",
                           "protocol": "HTTP/1.0",
                           "status_code": 200, "response_size": 0}

        filtered_keys = ['ip', 'local_user', 'remote_user']
        analyzer_factory = AnalyzerFactory(filtered_keys)
        analyzer = analyzer_factory.get_analyzer()
        self.assertIsNotNone(analyzer)

        stats = analyzer.compute_statistics(3)
        self.assertEqual(stats.nb_requests, 0)
        self.assertEqual(stats.nb_bytes, 0)
        self.assertEqual(stats.mean_bytes, 0)
        self.assertEqual(len(stats.requests_by_groups), len(filtered_keys))
        for key in stats.requests_by_groups:
            self.assertTrue(key in filtered_keys)
            self.assertEqual(len(stats.requests_by_groups[key]), 0)

        number_of_requests = 0
        size_of_requests = 0
        for ip in range(10):
            for local_user in range(3):
                for response_size in range(local_user):
                    for status_code in [200, 403, 503]:
                        default_request["ip"] = ip
                        default_request["local_user"] = "user" + \
                            str(local_user)
                        default_request["response_size"] = 1 + \
                            response_size * 10
                        default_request["status_code"] = status_code
                        size_of_requests += default_request["response_size"]
                        number_of_requests += 1

                        analyzer.add_request(default_request)

        stats = analyzer.compute_statistics(-1)
        self.assertEqual(stats.nb_requests, number_of_requests)
        self.assertEqual(stats.nb_bytes, size_of_requests)
        self.assertEqual(stats.mean_bytes,
                         size_of_requests/number_of_requests)
        self.assertEqual(len(stats.requests_by_groups), len(filtered_keys))
        for key in stats.requests_by_groups:
            self.assertTrue(key in filtered_keys)
            self.assertEqual(len(stats.requests_by_groups[key]), 0)

        self.assertEqual(len(stats.bytes_by_groups), len(filtered_keys))
        for key in stats.bytes_by_groups:
            self.assertTrue(key in filtered_keys)
            self.assertEqual(len(stats.bytes_by_groups[key]), 0)

        stats = analyzer.compute_statistics(3)
        self.assertEqual(stats.nb_requests, number_of_requests)
        self.assertEqual(stats.nb_bytes, size_of_requests)
        self.assertEqual(stats.mean_bytes,
                         size_of_requests/number_of_requests)
        self.assertEqual(len(stats.requests_by_groups), len(filtered_keys))

        for key in stats.requests_by_groups:
            self.assertTrue(key in filtered_keys)
            if key == 'ip':
                self.assertEqual(len(stats.requests_by_groups[key]), 3)
                for ip in stats.requests_by_groups[key]:
                    self.assertEqual(ip[1], 9)
            if key == 'remote_user':
                self.assertEqual(len(stats.requests_by_groups[key]), 1)
                self.assertEqual(stats.requests_by_groups[key][0][1],
                                 number_of_requests)
            if key == 'local_user':
                self.assertEqual(len(stats.requests_by_groups[key]), 2)
                self.assertEqual(stats.requests_by_groups[key][0][0], 'user2')
                self.assertEqual(stats.requests_by_groups[key][1][0], 'user1')
                self.assertEqual(stats.requests_by_groups[key][0][1], 60)
                self.assertEqual(stats.requests_by_groups[key][1][1], 30)

        self.assertEqual(len(stats.bytes_by_groups), len(filtered_keys))
        for key in stats.bytes_by_groups:
            self.assertTrue(key in filtered_keys)
            if key == 'ip':
                self.assertEqual(len(stats.bytes_by_groups[key]), 3)
                for ip in stats.bytes_by_groups[key]:
                    self.assertEqual(ip[1], 39)
            if key == 'remote_user':
                self.assertEqual(len(stats.bytes_by_groups[key]), 1)
                self.assertEqual(stats.bytes_by_groups[key][0][1],
                                 size_of_requests)
            if key == 'local_user':
                self.assertEqual(len(stats.bytes_by_groups[key]), 2)
                self.assertEqual(stats.bytes_by_groups[key][0][0], 'user2')
                self.assertEqual(stats.bytes_by_groups[key][1][0], 'user1')
                self.assertEqual(stats.bytes_by_groups[key][0][1], 360)
                self.assertEqual(stats.bytes_by_groups[key][1][1], 30)

        stats_str = stats.string("Custom prefix")
        self.assertIsNotNone(stats_str)
        stats_str = stats.string("Custom prefix", "custom header")
        self.assertIsNotNone(stats_str)
        self.assertNotEqual("", "%s" % stats)


if __name__ == "__main__":
    unittest.main()
