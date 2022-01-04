"""prawcore Integration test suite."""
import inspect
import logging

from betamax import Betamax

from prawcore import Requestor


class IntegrationTest:
    """Base class for prawcore integration tests."""

    logger = logging.getLogger(__name__)

    def setup(self):
        """Setup runs before all test cases."""
        self.requestor = Requestor("prawcore:test (by /u/bboe)")
        self.recorder = Betamax(self.requestor)

    def use_cassette(self, cassette_name=None, **kwargs):
        """Use a cassette. The cassette name is dynamically generated.

        :param cassette_name: (Deprecated) The name to use for the cassette. All names
            that are not equal to the dynamically generated name will be logged.
        :param kwargs: All keyword arguments for the main function
            (``Betamax.use_cassette``).

        """
        dynamic_name = self.get_cassette_name()
        if cassette_name:
            self.logger.debug(
                f"Static cassette name provided by {dynamic_name}. The following name "
                f"was provided: {cassette_name}"
            )
            if cassette_name != dynamic_name:
                self.logger.warning(
                    f"Dynamic cassette name for function {dynamic_name} does not match"
                    f" the provided cassette name: {cassette_name}"
                )
        return self.recorder.use_cassette(cassette_name or dynamic_name, **kwargs)

    def get_cassette_name(self) -> str:
        function_name = inspect.currentframe().f_back.f_back.f_code.co_name
        return f"{type(self).__name__}.{function_name}"
