"""Test for prawcore.requestor.Requestor class."""
import pickle

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

    def test_pickle(self):
        requestor = prawcore.Requestor('prawcore:test (by /u/bboe)')
        for protocol in range(pickle.HIGHEST_PROTOCOL + 1):
            pickle.loads(pickle.dumps(requestor, protocol=protocol))
