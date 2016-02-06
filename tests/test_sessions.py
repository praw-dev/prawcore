"""Test for prawcore.Sessions module."""
import prawcore
import unittest


class SessionTest(unittest.TestCase):
    def setUp(self):
        self.session = prawcore.Session()

    def test_close(self):
        self.session.close()

    def test_context_manager(self):
        with self.session as session:
            self.assertIsInstance(session, prawcore.Session)


class SessionFunctionTest(unittest.TestCase):
    def test_session(self):
        self.assertIsInstance(prawcore.session(), prawcore.Session)
