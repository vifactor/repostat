import time
from datetime import timedelta


class Timeit(object):

    def __init__(self, before_msg=None):
        self.before_message = before_msg

    def __call__(self, method):
        def wrapper(*args):
            if self.before_message is None:
                self.before_message = method.__name__
            print(self.before_message + "...")
            ts = time.time()
            result = method(*args)
            te = time.time()

            elapsed = (te - ts)
            if elapsed < 1:
                print('Elapsed time: %2.2f ms' % (elapsed * 1000))
            else:
                formatted = str(timedelta(seconds=elapsed))
                print('Elapsed time: %s' % formatted)

            return result
        return wrapper
