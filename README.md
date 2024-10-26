# AnkiApp-like Flashcard System in FastAPI

This project implements a flashcard learning system with a spaced repetition algorithm similar to Anki. Users can create decks of flashcards, review them, and track their learning progress.

## Features

- **User Authentication**: JWT-based authentication with registration and login.
- **Deck Management**: Create, delete, and review decks.
- **Card Management**: Add, update, and delete flashcards within decks.
- **Spaced Repetition**: Uses a Leitner system to schedule cards for review based on user performance.
- **Progress Tracking**: Shows progress such as total cards reviewed, accuracy, and more.
- **Export/Import Decks**: Export decks as JSON for backup or sharing and import them back.

## Installation

1. Clone the repository:
    ```bash
    git clone <repository-url>
    cd anki-app-fastapi
    ```

2. Create and activate a virtual environment:
    ```bash
    python -m venv env
    source env/bin/activate  # On Windows use `env\\Scripts\\activate`
    ```

3. Install the required dependencies:
    ```bash
    pip install -r requirements.txt
    ```

4. Run the FastAPI app:
    ```bash
    uvicorn main:app --reload
    ```

5. The application will be available at `http://127.0.0.1:8000`.

## API Endpoints

### User Authentication

- **POST** `/register/`: Register a new user.
- **POST** `/token/`: Log in and receive a JWT token.

### Deck Management

- **POST** `/decks/`: Create a new deck.
- **GET** `/decks/{deck_id}/review/`: Review all cards that are due today in the specified deck.
- **GET** `/decks/{deck_id}/export/`: Export a deck to JSON.
- **POST** `/decks/import/`: Import a deck from JSON.

### Card Management

- **POST** `/decks/{deck_id}/cards/`: Add a new card to the specified deck.
- **PUT** `/decks/{deck_id}/cards/{card_id}/review/`: Mark a card as reviewed and update its next review date based on whether the answer was correct or incorrect.
- **DELETE** `/decks/{deck_id}/cards/{card_id}`: Delete a card from the specified deck.

### Progress Tracking

- **GET** `/decks/{deck_id}/progress/`: Show progress for a specific deck, including total cards, reviewed cards, and accuracy.

## Spaced Repetition

The app uses the **Leitner system** for spaced repetition:
- **Box 1**: Cards answered incorrectly are moved here and reviewed the next day.
- **Box 2**: Cards answered correctly once are reviewed after 3 days.
- **Box 3**: Cards answered correctly multiple times are reviewed after 7 days.
- And so on...

## Next Steps

1. **User-specific Decks**: Tie decks to individual users so each user has their own private decks.
2. **Enhanced UI**: Implement a frontend using React or Vue, or create simple HTML templates using FastAPI's templating engine.
3. **Background Tasks**: Use background tasks for heavy operations like large deck imports or complex spaced repetition scheduling.

## Contributing

Feel free to contribute by submitting a pull request or opening an issue.

## License

This project is licensed under the MIT License.