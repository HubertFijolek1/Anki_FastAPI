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

@app.get("/decks/{deck_name}/review/")
def review_cards(deck_name: str):
    if deck_name not in decks:
        raise HTTPException(status_code=404, detail="Deck not found")

    today = datetime.date.today()
    due_cards = [card for card in decks[deck_name].cards if card.next_review <= today]

    if not due_cards:
        return {"message": "No cards to review today."}

    return due_cards

