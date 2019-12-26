import unittest
import apachescan.parser as parser
import sys


class TestLogParser(unittest.TestCase):

    def test_apache_parser_wrong_logs(self):
        apache_parser = parser.apache.Parser()
        request = apache_parser.parse(None)
        self.assertIsNone(request)
        request = apache_parser.parse("")
        self.assertIsNone(request)

        array_wrong_logs = [
            '127.0.0.1  james [09/May/2018:16:00 +0000] '
            '"GET /report HTTP/1.0" 200 123',  # missing user
            '127.0.0.1 -  [09/May/2018:16:00:39 +0000] '
            '"GET /report HTTP/1.0" 200 123',  # missing second user
            '127.0.0.1 - jill [09/May/2018:16:00:41 +0000] '
            '"GET /api/user HTTP/1.0" 200',  # missing response size
            '127.0.0.1 - frank [09/May/2018:16:00:42 +0000] '
            '"POST  HTTP/1.0" 200 34',  # missing page
            '127.0.0.1 - mary [09/May/2018:16:00:42 +0000] '
            '"POST /api/user HTTP/1.0"  12',  # missing code
            '127.0.0.1 - mary [09/May/2018:16:00:42 +0000] '
            '" /api/user HTTP/1.0" 503 12',  # missing action
            '127.0.0.1 - mary [09/May/2018:16:00:42 +0000] '
            '"GET /api/"user HTTP/1.0" 503 12',  # quote in request
            '127.0.0.1 - mary [09/May/2018:]16:00:42 +0000] '
            '"GET /api/user HTTP/1.0" 503 12',  # embrace in date
            '127.0.0.1 - mary [09/May/2018:]16:00:42 +00] '
            '"GET /api/user HTTP/1.0" 503 12',  # wrong time zone
        ]
        for log in array_wrong_logs:
            request = apache_parser.parse(log)
            self.assertIsNone(request)

    def test_apache_parser_valid_logs(self):
        apache_parser = parser.apache.Parser()
        array_valid_logs = [
            '127.0.0.1 - james [09/May/2018:16:00:39 +0000] '
            '"GET /report HTTP/1.0" 200 123',
            '127.0.0.1 - james [09/May/2018:16:00:39 +0000] '
            '"GET /report HTTP/1.0" 200 123',
            '127.0.0.1 - frank [09/May/2018:16:00:42 +0000] '
            '"POST /api/u\\"ser HTTP/1.0" 200 34',
            # allow escape quote in request
            '127.0.0.1 - frank [09/May/2018:17:00:42 -0000] '
            '"POST /api/u\\"ser HTTP/1.0" 200 34',
            '127.0.0.1 - mary [09/May/2018:16:00:42 +0000] '
            '"POST /api/user HTTP/1.0" 503 12 amleopz " "rop',
            # allow additionnal information
        ]

        for log in array_valid_logs:
            request = apache_parser.parse(log)
            self.assertIsNotNone(request)


if __name__ == "__main__":
    unittest.main()
