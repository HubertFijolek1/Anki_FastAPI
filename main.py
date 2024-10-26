from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import datetime
app = FastAPI()

# Card model
class Card(BaseModel):
    question: str
    answer: str
    box: int = 1  # Default to box 1
    last_reviewed: Optional[datetime.date] = None
    next_review: datetime.date = datetime.date.today()
    categories: Optional[List[str]] = []

# Deck model
class Deck(BaseModel):
    name: str
    cards: List[Card] = []

# In-memory storage for decks
decks = {}

@app.get("/")
def read_root():
    return {"message": "Welcome to AnkiApp-like Flashcard System!"}

@app.post("/decks/")
def create_deck(deck: Deck):
    if deck.name in decks:
        raise HTTPException(status_code=400, detail="Deck already exists")
    decks[deck.name] = deck
    return {"message": f"Deck '{deck.name}' created successfully."}

@app.post("/decks/{deck_name}/cards/")
def add_card_to_deck(deck_name: str, card: Card):
    if deck_name not in decks:
        raise HTTPException(status_code=404, detail="Deck not found")
    decks[deck_name].cards.append(card)
    return {"message": f"Card added to deck '{deck_name}'."}

@app.put("/decks/{deck_name}/cards/{question}/review/")
def review_card(deck_name: str, question: str, correct: bool):
    if deck_name not in decks:
        raise HTTPException(status_code=404, detail="Deck not found")

    # Find the card by question
    card = next((c for c in decks[deck_name].cards if c.question == question), None)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    if correct:
        card.box += 1
        card.last_reviewed = datetime.date.today()
    else:
        card.box = 1  # Reset to box 1 if wrong
        card.last_reviewed = datetime.date.today()

    # Schedule next review based on the box
    if card.box == 1:
        card.next_review = datetime.date.today() + datetime.timedelta(days=1)
    elif card.box == 2:
        card.next_review = datetime.date.today() + datetime.timedelta(days=3)
    elif card.box == 3:
        card.next_review = datetime.date.today() + datetime.timedelta(days=7)

    return {"message": "Card reviewed and updated successfully."}

@app.delete("/decks/{deck_name}/cards/{question}")
def delete_card(deck_name: str, question: str):
    if deck_name not in decks:
        raise HTTPException(status_code=404, detail="Deck not found")

    card = next((c for c in decks[deck_name].cards if c.question == question), None)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    decks[deck_name].cards = [c for c in decks[deck_name].cards if c.question != question]
    return {"message": f"Card '{question}' deleted from deck '{deck_name}'."}

@app.get("/decks/{deck_name}/progress/")
def show_progress(deck_name: str):
    if deck_name not in decks:
        raise HTTPException(status_code=404, detail="Deck not found")

    total_cards = len(decks[deck_name].cards)
    reviewed_cards = len([card for card in decks[deck_name].cards if card.last_reviewed])
    correct_cards = len([card for card in decks[deck_name].cards if card.box > 1])

    return {
        "total_cards": total_cards,
        "reviewed_cards": reviewed_cards,
        "correct_cards": correct_cards,
        "accuracy": (correct_cards / reviewed_cards) * 100 if reviewed_cards else 0
    }

