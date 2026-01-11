import rpyc
import os
import django
from rpyc.utils.server import ThreadedServer

# Setup Django Environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SE_Project.settings')
django.setup()

from helloapp.models import Recommendation
from helloapp.commands import RecalculateRecommendationsCommand


class RecommendationService(rpyc.Service):
    def on_connect(self, conn):
        print(f"Connected to {conn}")

    def on_disconnect(self, conn):
        print(f"Disconnected from {conn}")

    def exposed_get_recommendations(self, user_id):
        """
        Retrieves recommendations from the database for the given user.
        """
        print(f"Fetching recommendations for user_id: {user_id}")

        recs = Recommendation.objects.filter(user_id=user_id).select_related('movie')

        results = []
        for rec in recs:
            results.append({
                "id": rec.movie.id,
                "name": rec.movie.name,
                "score": float(rec.predicted_rating)
            })

        print(f"Found {len(results)} recommendations.")
        return results

    def exposed_trigger_recalculation(self):
        """
        Triggers the Matrix Factorization algorithm to update recommendations.
        """
        print("Triggering recommendation recalculation...")
        cmd = RecalculateRecommendationsCommand()
        cmd.execute()
        print("Recalculation complete.")


if __name__ == "__main__":
    port = 18861
    print(f"Starting Recommendation RPyC Service on port {port}...")
    server = ThreadedServer(RecommendationService, port=port)
    server.start()
