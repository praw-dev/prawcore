"""prawcore Unit test suite."""
from prawcore import Requestor


class UnitTest:
    """Base class for prawcore unit tests."""

    def setup(self):
        """Setup runs before all test cases."""
        self.requestor = Requestor("prawcore:test (by /u/bboe)")
