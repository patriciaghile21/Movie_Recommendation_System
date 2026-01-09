from abc import ABC, abstractmethod
from datetime import date
import subprocess
import os
from .models import Review


class Visitor(ABC):

    @abstractmethod
    def visit(self, user, movie, profile):
        pass


class AgeSafetyVisitor(Visitor):
    def visit(self, user, movie, profile):
        today = date.today()
        age = today.year - profile.birthdate.year - (
                    (today.month, today.day) < (profile.birthdate.month, profile.birthdate.day))

        genres = [g.name for g in movie.genres.all()]
        is_horror = "Horror" in genres or "Thriller" in genres

        if is_horror and age < 18:
            return f"Blocked: Age Safety Violation! (User is {age}, needs 18 for Horror)"

        return "Safe"


class WatchHistoryVisitor(Visitor):
    def visit(self, user, movie, profile):
        already_watched = Review.objects.filter(user=user, movie=movie).exists()

        if already_watched:
            return f"Blocked: Watched Movie Violation! (You have already seen '{movie.name}')"

        return "Safe"


class RecommendationEngine:
    """
    Manager class that applies all visitors to a specific movie.
    """

    def __init__(self):
        self.visitors = [
            AgeSafetyVisitor(),
            WatchHistoryVisitor()
        ]

    def check_movie(self, user, movie, profile):
        errors = []
        for visitor in self.visitors:
            result = visitor.visit(user, movie, profile)

            if "Blocked" in result:
                errors.append(result)

        return errors


class KFrameworkBridge:
    """
    Handles Runtime Verification by invoking the K Framework externally.
    """

    def check_movie(self, user, movie, profile):
        today = date.today()
        age = today.year - profile.birthdate.year - (
                    (today.month, today.day) < (profile.birthdate.month, profile.birthdate.day))

        genres_list = [g.name for g in movie.genres.all()]
        k_genre = "Other"
        if "Horror" in genres_list or "Thriller" in genres_list:
            k_genre = "Horror"
        elif "Comedy" in genres_list:
            k_genre = "Comedy"

        is_watched = Review.objects.filter(user=user, movie=movie).exists()
        k_watched_str = "true" if is_watched else "false"

        # Construct K command
        k_command = f'check({movie.id}, {age}, "{k_genre}", {k_watched_str})'

        # Path configuration
        k_path = "/home/patri/Documents/k_files"
        trace_file = os.path.join(k_path, "trace.txt")

        try:
            with open(trace_file, "w") as f:
                f.write(k_command)

            # Execute KRUN
            result = subprocess.run(
                ['krun', 'trace.txt'],
                cwd=k_path,
                capture_output=True,
                text=True
            )
            output = result.stdout

            errors = []
            if "Success" in output:
                return []

            if "Age Safety Violation" in output:
                errors.append(f"K-VERDICT: Age restriction! (Verified by K Framework)")

            if "Watched Movie Violation" in output:
                errors.append(f"K-VERDICT: Redundant! (Verified by K Framework)")

            if not errors and "Error" in output:
                errors.append(f"K Error: {output[:50]}...")

            return errors

        except Exception as e:
            print(f"CRITICAL ERROR calling K: {e}")
            return [f"System Error: Could not contact K Framework."]