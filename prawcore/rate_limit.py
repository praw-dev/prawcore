"""Provide the RateLimiter class."""
import time


class RateLimiter(object):
    """Facilitates the rate limiting of requests to reddit.

    Rate limits are controlled based on feedback from requests to reddit.

    """

    def __init__(self):
        """Create an instance of the RateLimit class."""
        self.remaining = None
        self.reset_timestamp = None
        self.used = None

    def call(self, request_function, *args, **kwargs):
        """Rate limit the call to request_function.

        :param request_function: A function call that returns an HTTP response
        object.
        :param *args: The positional arguments to ``request_function``.
        :param **kwargs: The keyword arguments to ``request_function``.

        """
        self.delay()
        response = request_function(*args, **kwargs)
        self.update(response.headers)
        return response

    def delay(self):
        """Sleep for an amount of time to remain under the rate limit."""
        if self.remaining is None:
            return
        print(self.remaining)
        print(self.reset_timestamp)
        print(self.used)
        print('---')

    def update(self, response_headers):
        """Update the state of the rate limiter based on the response headers.

        This method should only be called following a HTTP request to reddit.

        Response headers that do not contain x-ratelimit fields will be treated
        as a single request. This behavior is to error on the safe-side as such
        responses should trigger exceptions that indicate invalid behavior.

        """
        if 'x-ratelimit-remaining' not in response_headers:
            if self.remaining is not None:
                self.remaining -= 1
                self.used += 1
            return

        self.remaining = float(response_headers['x-ratelimit-remaining'])
        self.reset_timestamp = (time.time() +
                                int(response_headers['x-ratelimit-reset']))
        self.used = int(response_headers['x-ratelimit-used'])
