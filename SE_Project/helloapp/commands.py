import numpy as np
from .models import Review
from .models import Recommendation

class RecalculateRecommendationsCommand:
    def __init__(self, user_ids=None, hyper_parameters=None):

        self.user_ids = user_ids or "All users"
        self.hyper_parameters = hyper_parameters or {'epochs': 20, 'learning_rate': 0.01}

    def execute(self):
        user_ids = list(Review.objects.values_list('user_id', flat=True).distinct())
        movie_ids = list(Review.objects.values_list('movie_id', flat=True).distinct())

        #Create a lookup dictionary: {DatabaseID: MatrixIndex}
        #This helps because user IDs might not start from 0 and because
        #some users might have no reviews, so they'd be missing from the data set here
        user_map = {id: i for i, id in enumerate(user_ids)}
        movie_map = {id: i for i, id in enumerate(movie_ids)}

        num_users = len(user_ids)
        num_items = len(movie_ids)

        #Declare a matrix of size users x movies filled with zeros
        R = np.zeros((num_users, num_items))

        for review in Review.objects.all():
            u_idx = user_map[review.user_id]
            m_idx = movie_map[review.movie_id]
            R[u_idx, m_idx] = float(review.rating)

        K = 5  #Number of latent features
        #The latent features don't actually have to be specified, they're kind of just "implied"
        #by the algorithm
        lr = 0.005  # Learning rate
        num_epochs = 5000

        #This represents random guesses before the computer starts learning
        U = np.random.rand(num_users, K)
        V = np.random.rand(num_items, K)

        #This basically keep track of the positions where the users already rated the movies
        #It's needed to differentiate between an actual review and a prediction from the algorithm
        mask = (R > 0).astype(float)

        N = np.sum(mask) #number of reviews



        for curr_epoch in range(num_epochs):
            R_hat = U @ V.T

            #Calculate the difference
            #We only care about the cells where we actually have ratings
            raw_error = R - R_hat
            error_matrix = raw_error * mask

            U_grad = -2. / N * (error_matrix) @ V
            V_grad = -2. / N * (error_matrix).T @ U

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

        Recommendation.objects.all().delete()

        #Create a reverse map so we can find the movie id from the matrix index
        reverse_movie_map = {i: m_id for m_id, i in movie_map.items()}

        for u_id, u_idx in user_map.items():
            #Get the user's predicted ratings row
            user_preds = final_predictions[u_idx]

            unrated_movies_with_scores = []

            for movie_index in range(len(R[u_idx])):

                #Check the original rating in matrix R
                actual_rating = R[u_idx][movie_index]

                #If the rating is 0, it means the user hasn't seen this movie
                if actual_rating == 0:
                    predicted_score = user_preds[movie_index]
                    unrated_movies_with_scores.append((movie_index, predicted_score))
            #Helper function for sorting. Returns the second element of a tuple,
            #in this case, the predicted rating
            def get_score(pair):
                return pair[1]

            unrated_movies_with_scores.sort(key=get_score, reverse=True)

            # Take only the first 3 movies
            top_3_pairs = unrated_movies_with_scores[:5]

            recommendations = []
            for pair in top_3_pairs:
                movie_index = pair[0]
                recommendations.append(movie_index)

            for m_idx in recommendations:
                print(f"\nUser ID: {u_id}, movie ID: {reverse_movie_map[m_idx]}")

                raw_score = float(user_preds[m_idx])

                if np.isnan(raw_score) or np.isinf(raw_score):
                    print(f"Warning: Math exploded for User {u_id}. setting score to 0.")
                    clean_score = 0.0
                else:
                    clean_score = raw_score

                Recommendation.objects.create(
                    user_id=u_id,
                    movie_id=reverse_movie_map[m_idx],
                    predicted_rating=clean_score
                )

        print(f"Successfully updated Top 3 picks for {num_users} users.")