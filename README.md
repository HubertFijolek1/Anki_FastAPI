# AnkiApp-like Flashcard System in FastAPI

This project is a flashcard learning system inspired by Anki, built with FastAPI. It incorporates spaced repetition algorithms, user authentication, deck and card management, and a simple frontend interface using Jinja2 templates.

## Features

- **User Authentication**: JWT-based authentication with registration and login.
- **Deck Management**: Users can create, delete, and review decks.
- **Card Management**: Add, update, delete, and review flashcards within decks.
- **Spaced Repetition**: Uses the SM2 algorithm to calculate review intervals based on user feedback.
- **Progress Tracking**: Tracks total cards, reviewed cards, accuracy, and consecutive daily review streaks.
- **Deck Export/Import**: Allows users to export decks as JSON and import them back.
- **Frontend Interface**: Jinja2-based HTML pages provide a basic interface for deck and card management.

## Installation

1. **Clone the Repository**
    ```bash
    git clone <repository-url>
    cd anki-app-fastapi
    ```

2. **Set Up a Virtual Environment**
    ```bash
    python -m venv env
    source env/bin/activate  # On Windows use `env\\Scripts\\activate`
    ```

3. **Install Required Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4. **Run the FastAPI Application**
    ```bash
    uvicorn main:app --reload
    ```
    The application will be accessible at `http://127.0.0.1:8000`.

## API Endpoints

### User Authentication
- **POST** `/register/`: Register a new user by providing a `username` and `password`.
- **POST** `/token/`: Log in with `username` and `password` to receive a JWT token for authenticated requests.

### Deck Management
- **POST** `/decks/`: Create a new deck tied to the authenticated user.
- **GET** `/decks/{deck_id}/`: Retrieve details for a specific deck, accessible only to the deck owner.
- **GET** `/decks/{deck_id}/review/`: Review cards due today in the specified deck.
- **GET** `/decks/`: Display all decks owned by the authenticated user (HTML view).
- **GET** `/decks/{deck_id}/export/`: Export a deck to JSON format.
- **POST** `/decks/import/`: Import a deck from JSON format into the user's account.

### Card Management
- **POST** `/decks/{deck_id}/cards/`: Add a new card to the specified deck.
- **PUT** `/decks/{deck_id}/cards/{card_id}/review/`: Review a specific card, updating its next review date based on the SM2 algorithm.
- **DELETE** `/decks/{deck_id}/cards/{card_id}`: Delete a card from the specified deck.

### Progress Tracking
- **GET** `/decks/{deck_id}/progress/`: Displays the user’s progress within a specified deck, including:
  - Total cards in the deck
  - Number of reviewed cards
  - Accuracy (percentage of correct answers)
  - User streak (number of consecutive review days)

## Spaced Repetition: SM2 Algorithm

The SM2 algorithm dynamically schedules card review intervals based on user feedback to optimize learning. The steps:
1. Users rate their recall for each card (0-5).
2. The algorithm adjusts the card’s interval and ease factor based on the rating:
    - **High ratings** increase the review interval.
    - **Low ratings** reset the interval, reinforcing challenging cards more frequently.

## Frontend (HTML Templates with Jinja2)

Basic HTML templates provide a simple web interface for managing decks and cards:
- **Decks**: List all decks owned by the authenticated user.
- **Create Deck**: Simple form to add new decks.

## Next Steps

1. **Enhance Frontend**: Develop a more dynamic interface with JavaScript or a framework like React/Vue.
2. **Add Leaderboards**: Track and display learning streaks and accuracy-based rankings.
3. **Containerization**: Use Docker for easier deployment and scalability.