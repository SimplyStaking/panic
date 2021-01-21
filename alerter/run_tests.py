import unittest

loader = unittest.TestLoader()
suite = loader.discover('.', pattern='*.py')

runner = unittest.TextTestRunner()
runner.run(suite)
