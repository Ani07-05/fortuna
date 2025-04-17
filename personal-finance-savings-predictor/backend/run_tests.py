import unittest
import warnings
import logging
import test_api

if __name__ == "__main__":
    # Suppress all warnings
    warnings.filterwarnings("ignore")
    
    # Reduce logging level to suppress error logs
    logging.getLogger().setLevel(logging.CRITICAL)
    
    # Run tests
    suite = unittest.TestLoader().loadTestsFromModule(test_api)
    unittest.TextTestRunner(verbosity=2).run(suite)
