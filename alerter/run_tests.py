import unittest

loader = unittest.TestLoader()
suite = loader.discover('.')

# TODO: For production set buffer=True in TextTestRunner to avoid the components
#     : from printing output. Also, set verbosity=2 to get the result of each
#     : test
runner = unittest.TextTestRunner(buffer=True, verbosity=2)
runner.run(suite)
