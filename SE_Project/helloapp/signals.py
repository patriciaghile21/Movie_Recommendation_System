from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Review
from .commands import RecalculateRecommendationsCommand

@receiver(post_save, sender=Review)
def trigger_recommendation_update(sender, instance, created, **kwargs):

    if created:
        print("\n--- OBSERVER NOTIFIED: New review created. Executing Command. ---")
    else:
        print("\n--- OBSERVER NOTIFIED: Review updated. Executing Command. ---")

    # The observer triggers the command
    command = RecalculateRecommendationsCommand()
    command.execute()