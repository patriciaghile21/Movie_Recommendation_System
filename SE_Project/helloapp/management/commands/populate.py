import random
from datetime import date
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
# === CHANGE 'api' TO YOUR ACTUAL APP NAME ===
from helloapp.models import Movie, Review, Genre


class Command(BaseCommand):
    help = 'Populate database with Movies and Reviews'

    def handle(self, *args, **kwargs):
        User = get_user_model()
        users = list(User.objects.all())

        if not users:
            self.stdout.write(self.style.ERROR("❌ No users found! Create users in admin first."))
            return

        # DATA LIST
        movies_data = [
            ("The Shawshank Redemption", "1994-09-22", 142, "Frank Darabont", "Columbia Pictures", ["Drama", "Crime"]),
            ("The Dark Knight", "2008-07-18", 152, "Christopher Nolan", "Warner Bros.", ["Action", "Crime", "Drama"]),
            ("Pulp Fiction", "1994-10-14", 154, "Quentin Tarantino", "Miramax", ["Crime", "Drama"]),
            ("Forrest Gump", "1994-07-06", 142, "Robert Zemeckis", "Paramount", ["Drama", "Romance"]),
            ("Inception", "2010-07-16", 148, "Christopher Nolan", "Warner Bros.", ["Action", "Sci-Fi", "Thriller"]),
            ("The Matrix", "1999-03-31", 136, "Lana Wachowski", "Warner Bros.", ["Action", "Sci-Fi"]),
            ("Interstellar", "2014-11-07", 169, "Christopher Nolan", "Paramount", ["Adventure", "Drama", "Sci-Fi"]),
            ("Parasite", "2019-05-30", 132, "Bong Joon Ho", "CJ Entertainment", ["Thriller", "Drama"]),
            ("Gladiator", "2000-05-05", 155, "Ridley Scott", "DreamWorks", ["Action", "Adventure", "Drama"]),
            ("The Lion King", "1994-06-15", 88, "Roger Allers", "Disney", ["Animation", "Adventure", "Drama"]),
            ("Titanic", "1997-12-19", 195, "James Cameron", "Paramount", ["Romance", "Drama"]),
            ("Avatar", "2009-12-18", 162, "James Cameron", "20th Century Fox", ["Action", "Adventure", "Fantasy"]),
            ("Joker", "2019-10-04", 122, "Todd Phillips", "Warner Bros.", ["Crime", "Drama", "Thriller"]),
            ("Avengers: Endgame", "2019-04-26", 181, "Anthony Russo", "Marvel Studios",
             ["Action", "Adventure", "Sci-Fi"]),
            ("Coco", "2017-11-22", 105, "Lee Unkrich", "Disney", ["Animation", "Adventure", "Family"])
        ]

        review_comments = [
            "Absolute masterpiece!", "A bit overrated.", "Loved the cinematography.",
            "Great acting but slow pace.", "Would watch again!", "Terrible ending.",
            "Best movie I've seen this year.", "Solid 10/10.", "Not my cup of tea."
        ]

        self.stdout.write("Starting population...")

        for m_name, m_date_str, m_dur, m_dir, m_studio, m_genre_names in movies_data:
            y, m, d = map(int, m_date_str.split('-'))
            release_date_obj = date(y, m, d)

            # Create Movie
            movie, created = Movie.objects.get_or_create(
                name=m_name,
                defaults={
                    'releaseDate': release_date_obj,
                    'duration_minutes': m_dur,
                    'director': m_dir,
                    'studio': m_studio
                }
            )

            if created:
                self.stdout.write(f"✅ Created Movie: {m_name}")

                # Link Genres
                found_genres = []
                for g_name in m_genre_names:
                    g_obj = Genre.objects.filter(name__iexact=g_name).first()
                    if g_obj:
                        found_genres.append(g_obj)
                if found_genres:
                    movie.genres.set(found_genres)

                # Reviews
                number_of_reviews = random.randint(3, 6)
                for _ in range(number_of_reviews):
                    selected_user = random.choice(users)

                    # USE get_or_create TO AVOID CRASHING ON DUPLICATES
                    review, review_created = Review.objects.get_or_create(
                        user=selected_user,
                        movie=movie,
                        defaults={
                            'rating': round(random.uniform(4.0, 10.0), 1),
                            'text': random.choice(review_comments)
                        }
                    )

                    if review_created:
                        self.stdout.write(f"   -> Added review by {selected_user.username}")
                    else:
                        self.stdout.write(f"   -> Skipped review (User {selected_user.username} already reviewed this)")
            else:
                self.stdout.write(f"   -> Skipped {m_name} (already exists)")

        self.stdout.write(self.style.SUCCESS("DONE! Data population complete."))