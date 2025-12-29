import os
import sys
import django
from datetime import date

# --- Django Environment Setup ---
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SE_Project.settings')
django.setup()

from helloapp.models import Profile, Movie, Review
from django.contrib.auth.models import User


def calculate_age(birthdate):
    today = date.today()
    return today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))


def generate_k_trace(user_id, movie_id):
    print(f"\n--- Generating K-Trace (User ID: {user_id}, Movie ID: {movie_id}) ---")

    try:
        user = User.objects.get(id=user_id)
        profile = Profile.objects.get(user=user)
        movie = Movie.objects.get(id=movie_id)
    except Exception as e:
        print(f"Error fetching data: {e}")
        return

    # Data Extraction
    age = calculate_age(profile.birthdate)

    genres_list = [g.name for g in movie.genres.all()]
    k_genre = "Other"
    if "Horror" in genres_list or "Thriller" in genres_list:
        k_genre = "Horror"

    is_watched = Review.objects.filter(user=user, movie=movie).exists()
    k_watched_str = "true" if is_watched else "false"

    print(f"Details -> Age: {age}, Genre: {k_genre}, Watched: {k_watched_str}")

    # Trace Generation
    k_command = f'check({movie.id}, {age}, "{k_genre}", {k_watched_str})'
    k_path = "/home/patri/Documents/k_files/trace.txt"

    try:
        with open(k_path, "w") as f:
            f.write(k_command)
        print(f"SUCCESS! Command written: {k_command}")
    except Exception as e:
        print(f"Error writing file: {e}")


if __name__ == "__main__":
    # Test execution logic
    print("Automated test: Searching for user 'chris1706' and a Horror movie...")

    try:
        u = User.objects.get(username='chris1706')

        # Force update age for testing purposes (Set to 2015 -> ~9 years old)
        p = Profile.objects.get(user=u)
        p.birthdate = date(2015, 1, 1)
        p.save()
        print(f"User found: {u.username} (Age set to ~9 years)")

        m = Movie.objects.filter(genres__name='Horror').first()

        if m:
            print(f"Horror movie found: {m.name}")
            generate_k_trace(user_id=u.id, movie_id=m.id)
        else:
            print("Error: No Horror movie found in database.")

    except User.DoesNotExist:
        print("Error: User 'chris1706' not found.")