import rpyc
import time


def test_service():
    try:
        print("Connecting to RPyC Service...")
        conn = rpyc.connect("localhost", 18861)
        print("Connected.")

        print("Triggering recalculation...")
        conn.root.trigger_recalculation()
        print("Recalculation triggered.")

        print("Fetching recommendations for User ID 1...")
        recs = conn.root.get_recommendations(1)
        print(f"Recommendations for User 1: {recs}")

        conn.close()
        print("Test passed!")
    except Exception as e:
        print(f"Test failed: {e}")


if __name__ == "__main__":
    test_service()