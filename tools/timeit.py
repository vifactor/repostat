import time


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
            print('Finished in %2.2f ms' % ((te - ts) * 1000))
            return result
        return wrapper
