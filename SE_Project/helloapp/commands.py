import numpy as np
from .models import Review
from .models import Recommendation
#the command object (Encapsulates the request)
class RecalculateRecommendationsCommand:
    def __init__(self, user_ids=None, hyper_parameters=None):
        #store all necessary parameters for the calculation
        self.user_ids = user_ids or "All users"
        self.hyper_parameters = hyper_parameters or {'epochs': 20, 'learning_rate': 0.01}

    def execute(self):
        user_ids = list(Review.objects.values_list('user_id', flat=True).distinct())
        movie_ids = list(Review.objects.values_list('movie_id', flat=True).distinct())

        # Create a lookup dictionary: {DatabaseID: MatrixIndex}
        # Result looks like: {105: 0, 106: 1, ...}
        # This helps because a) user IDs might not start from 0
        #                    b) some users might have no reviews, so they'd be missing from the data set here
        user_map = {id: i for i, id in enumerate(user_ids)}
        movie_map = {id: i for i, id in enumerate(movie_ids)}

        num_users = len(user_ids)
        num_items = len(movie_ids)

        # Declare a matrix of size (users x movies) filled with zeros
        R = np.zeros((num_users, num_items))

        for review in Review.objects.all():
            u_idx = user_map[review.user_id]
            m_idx = movie_map[review.movie_id]
            R[u_idx, m_idx] = float(review.rating)

        K = 5  # Number of latent features (e.g., Genre, Mood, Pace)
        # The latent features don't actually have to be specified, they're kind of just "implied"
        # by the algorithm
        lr = 0.05  # Learning rate (how big of a 'step' the math takes)
        num_epochs = 500  # How many times we loop over the data

        # This represents random guesses before the computer starts learning
        U = np.random.rand(num_users, K)
        V = np.random.rand(num_items, K)

        # This basically keep track of the positions where the users already rated the movies
        # It's needed to differentiate between an actual review and a prediction from the alg.
        mask = (R > 0).astype(float)

        N = np.sum(mask)



        for curr_epoch in range(num_epochs):
            # Reconstruct the full predicted matrix (Linear dot product)
            R_hat = U @ V.T #.T is transposed matrix

            # Calculate the difference (Error)
            # We only care about the cells where we actually have ratings
            raw_error = R - R_hat
            error_matrix = raw_error * mask

            # Calculate Gradients (The direction to move in)
            U_grad = -2. / N * (error_matrix) @ V
            V_grad = -2. / N * (error_matrix).T @ U

            # 4. Update the matrices
            U -= lr * U_grad
            V -= lr * V_grad
        final_predictions = U @ V.T

        print("\n" + "=" * 50)
        print("FINAL PREDICTED RATING MATRIX (R_hat)")
        print("Rows = Users, Columns = Movies")
        print("=" * 50)

        import sys
        np.set_printoptions(threshold=sys.maxsize, precision=2, suppress=True)

        print(final_predictions)
        print("=" * 50 + "\n")

        # Clear previous recommendations to keep the data fresh
        Recommendation.objects.all().delete()

        # Create a reverse map so we can find the movie id from the matrix index
        reverse_movie_map = {i: m_id for m_id, i in movie_map.items()}

        for u_id, u_idx in user_map.items():
            # Get the user's predicted ratings row
            user_preds = final_predictions[u_idx]

            # Start an empty list to hold movies the user hasn't rated yet
            unrated_movies_with_scores = []

            # Loop through every movie in the matrix by its index (0, 1, 2...)
            for movie_index in range(len(R[u_idx])):

                # Check the original rating in matrix R
                actual_rating = R[u_idx][movie_index]

                # If the rating is 0, it means the user hasn't seen this movie
                if actual_rating == 0:
                    predicted_score = user_preds[movie_index]
                    unrated_movies_with_scores.append((movie_index, predicted_score))

            # Short helper function to help with the sorting
            def get_score(pair):
                return pair[1]

            unrated_movies_with_scores.sort(key=get_score, reverse=True)

            # Take only the first 3 movies (3 is an arbitrary number, can be changed to recommend however many)
            top_3_pairs = unrated_movies_with_scores[:3]

            # Extract just the movie indices so we can save them
            recommendations = []
            for pair in top_3_pairs:
                movie_index = pair[0]
                recommendations.append(movie_index)

            # Save each recommendation

            for m_idx in recommendations:
                print(f"\nUser ID: {u_id}, movie ID: {reverse_movie_map[m_idx]}")
                Recommendation.objects.create(
                    user_id=u_id,
                    movie_id=reverse_movie_map[m_idx],
                    predicted_rating=float(user_preds[m_idx])
                )

        print(f"Successfully updated Top 3 picks for {num_users} users.")