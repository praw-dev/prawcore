"""Test for prawcore.requestor.Requestor class."""
import prawcore
import unittest


class RequestorTest(unittest.TestCase):
    def test_initialize(self):
        requestor = prawcore.Requestor('prawcore:test (by /u/bboe)')
        self.assertEqual('prawcore:test (by /u/bboe) prawcore/{}'
                         .format(prawcore.__version__),
                         requestor._http.headers['User-Agent'])

    def test_initialize__failures(self):
        for agent in [None, 'shorty']:
            self.assertRaises(prawcore.InvalidInvocation, prawcore.Requestor,
                              agent)
