# Smart Movie Recommendation System 🎬

## 📌 Project Overview
A distributed movie recommendation platform that integrates modern web development with formal verification methods. This project demonstrates a robust approach to software reliability, focusing on structural design patterns and runtime monitoring.

## 🛠️ My Technical Contributions
I was responsible for the core verification logic and the user interface, specifically:

* **Design Pattern Verification (Visitor):** Implemented a decoupled verification bridge using the **Visitor Pattern** in `helloapp/patterns.py`. This ensures that validation rules (such as age restrictions or permission checks) are independent of the movie and user entities, making the system highly extensible.
* **Formal Verification (K Framework):** Developed the formal semantics and runtime verification logic specifically for **Linux**. Using the **K Framework**, I implemented monitors that ensure the recommendation logic adheres to predefined safety properties during execution.
* **Frontend Development:** Designed and implemented the responsive web interface. Using Django's template engine, I built the frontend components that allow users to interact with the recommendation engine and view personalized movie data.

## 🐧 Linux Environment & K Framework
The project features a specialized verification layer designed to run on Linux:
* **Runtime Monitoring:** The K Framework integration intercepts system events to verify correctness in real-time.
* **Formal Semantics:** I defined the operational semantics for the core recommendation components to prevent logic errors before they reach the production environment.

## 📂 Project Structure
* `helloapp/` - Contains the logic for the Visitor Pattern and frontend views.
* `templates/` - HTML/CSS components for the user interface.
* `k-framework/` - (Available on the linux branch) Formal verification scripts and semantics definitions.
* `manage.py` - Main entry point for the Django application.

## 🚀 How to Run
1. **Frontend & Logic:** Install Django (`pip install django`) and run `python manage.py runserver`.
2. **Verification (Linux):** Switch to the `linux-k-framework` branch and follow the instructions in the `k-framework` directory to start the runtime monitors.
