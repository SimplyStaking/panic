import unittest

loader = unittest.TestLoader()
suite = loader.discover('.')

runner = unittest.TextTestRunner()
runner.run(suite)
