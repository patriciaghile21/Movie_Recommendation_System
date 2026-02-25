# Smart Movie Recommendation System 🎬

## 📌 Project Overview
An intelligent, distributed platform designed to provide personalized movie suggestions through collaborative filtering and microservices. The project bridges modern web development (Django) with academic rigor, incorporating formal verification methods and advanced architectural design patterns.

## 🛠️ Key Technical Contributions
I focused on the core logic and reliability of the system, implementing the following:

* **Advanced Design Patterns:** Implemented the **Visitor Pattern** within `helloapp/patterns.py` to create a modular verification bridge. This allows for extending the system's validation rules (e.g., checking user age vs. movie rating) without modifying the core entity classes.
* **Distributed Recommendation Engine:** Developed the `recommendation_service.py` as a standalone microservice that uses collaborative filtering algorithms to analyze user behavior and suggest relevant content.
* **Microservices Communication:** Integrated **RPyC (Remote Python Call)** for high-performance communication between the Django web server and the AI backend.
* **Backend Architecture:** Structured the core Django application (`SE_Project`) and the specific app logic (`helloapp`) to ensure scalability and clean separation of concerns.

## 🐧 Linux & Formal Verification (K Framework)
Beyond the standard implementation, this project explores **Runtime Verification** to ensure system correctness:

* **K Framework Integration:** A specialized version of this system (available in the `linux-k-framework` branch) includes formal semantics defined using the K Framework. 
* **Runtime Monitors:** Specifically designed for a **Linux environment**, these monitors intercept system events to verify that the recommendation logic adheres to predefined safety and security properties.
* **Platform Specifics:** While the core Django UI is platform-independent, the formal verification layer leverages Linux-specific tools to perform real-time analysis of the software's execution trace.

## 🗄️ Project Structure
* `helloapp/` - Application logic, including models and the Visitor pattern implementation.
* `SE_Project/` - Core settings and configuration for the Django framework.
* `recommendation_service.py` - Standalone AI service for movie filtering.
* `manage.py` - Entry point for administrative tasks and server management.
* `connector.py` / `test_rpyc.py` - Utilities for distributed service communication.

## 🚀 How to Run (Windows/Core Version)
1. **Environment:** Ensure Python 3.x is installed.
2. **Setup:** Install required libraries: `pip install django rpyc`.
3. **Database:** Initialize the schema: `python manage.py migrate`.
4. **Launch AI:** Start the recommendation engine: `python recommendation_service.py`.
5. **Start Web:** Run the server: `python manage.py runserver`.
