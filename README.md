# Smart Movie Recommendation System 🎬

## 📌 Project Overview
This project was developed as a collaborative effort by a **team of 5 students** for the Software Engineering course. It represents a distributed platform for movie suggestions, combining a Django-based web interface with advanced formal verification methods.

## 🛠️ My Specific Contributions
In this team environment, I was responsible for the high-level architecture verification and the user-facing components:

* **Design Pattern Implementation (Visitor):** I designed and implemented the **Visitor Pattern** within the `helloapp/patterns.py` file. This was used to create a decoupled verification bridge, allowing us to add new validation rules (like content filters or user permissions) without altering the existing movie or user models.
* **Formal Verification & Runtime Monitoring (Linux):** I led the academic verification side of the project. I developed formal semantics using the **K Framework** on a **Linux environment** to monitor the system's execution. This ensured that the recommendation logic strictly followed predefined safety properties, preventing runtime errors.
* **Frontend Development:** I built the responsive user interface using **Django Templates**. This involved creating the HTML/CSS structure that connects the backend logic to the end-user, ensuring a seamless experience when browsing movie recommendations.

## 🐧 Technical Focus: Verification & UI
While the team handled the database and recommendation algorithms, my focus remained on ensuring system correctness and usability:
* **K Framework:** Specialized runtime monitors for Linux.
* **Architecture:** Ensuring clean code through design patterns.
* **Interface:** Real-time data visualization via Django.

## 📂 Project Structure (My Areas)
* `helloapp/` - Contains my Visitor Pattern logic and view controllers.
* `templates/` - HTML components I developed for the UI.
* `manage.py` - The entry point we used to run the collaborative server.
* **Linux Branch** - Contains the K Framework semantics I authored for formal verification.

## 🚀 How to Run
1. Install Django: `pip install django`.
2. Initialize: `python manage.py migrate`.
3. Run Server: `python manage.py runserver`.
