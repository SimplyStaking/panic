import unittest

loader = unittest.TestLoader()
suite = loader.discover('./test')

runner = unittest.TextTestRunner(buffer=True, verbosity=2)
runner.run(suite)
