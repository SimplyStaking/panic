import unittest

loader = unittest.TestLoader()
suite = loader.discover('./test/monitors/node', 'test_cosmos.py')

runner = unittest.TextTestRunner(buffer=True, verbosity=2)
runner.run(suite)
