import unittest
import rpyc
import threading
import time
import sys
import os

# Add the project root to sys.path to import modules
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.append(PROJECT_ROOT)

from recommendation_service import RecommendationService
from rpyc.utils.server import ThreadedServer


class TestRPyCIntegration(unittest.TestCase):
    SERVER_PORT = 18861
    server = None
    server_thread = None

    @classmethod
    def setUpClass(cls):
        """Start the RPyC server in a separate thread before tests."""
        print("\n[TEST] Starting RPyC Server for testing...")
        cls.server = ThreadedServer(RecommendationService, port=cls.SERVER_PORT)
        cls.server_thread = threading.Thread(target=cls.server.start)
        cls.server_thread.daemon = True
        cls.server_thread.start()
        time.sleep(1)  # Give it a second to start

    @classmethod
    def tearDownClass(cls):
        """Stop the RPyC server after tests."""
        if cls.server:
            print("[TEST] Stopping RPyC Server...")
            cls.server.close()

    def test_connection_and_data(self):
        """Test if we can connect and retrieve data."""
        print("[TEST] Connecting to RPyC Service...")
        conn = rpyc.connect("localhost", self.SERVER_PORT)

        # Test exposed method
        user_id = 999
        recommendations = conn.root.get_recommendations(user_id)

        print(f"[TEST] Received recommendations: {recommendations}")

        self.assertIsInstance(recommendations, list)
        self.assertGreater(len(recommendations), 0)
        self.assertIn('name', recommendations[0])
        self.assertIn('id', recommendations[0])

        conn.close()


if __name__ == '__main__':
    unittest.main()