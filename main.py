from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import datetime
from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi import Depends
from sqlalchemy.orm import Session

# Create SQLite engine (or use PostgreSQL with the appropriate connection string)
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Card model for database
class CardDB(Base):
    __tablename__ = 'cards'
    id = Column(Integer, primary_key=True, index=True)
    question = Column(String, index=True)
    answer = Column(String)
    box = Column(Integer, default=1)
    last_reviewed = Column(Date)
    next_review = Column(Date)
    deck_id = Column(Integer, ForeignKey('decks.id'))

# Deck model for database
class DeckDB(Base):
    __tablename__ = 'decks'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    cards = relationship("CardDB", back_populates="deck")

# Make sure to create the tables
Base.metadata.create_all(bind=engine)

# Dependency for getting DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
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

# @app.post("/decks/")
# def create_deck(deck: Deck):
#     if deck.name in decks:
#         raise HTTPException(status_code=400, detail="Deck already exists")
#     decks[deck.name] = deck
#     return {"message": f"Deck '{deck.name}' created successfully."}
@app.post("/decks/", response_model=Deck)
def create_deck(deck: Deck, db: Session = Depends(get_db)):
    db_deck = DeckDB(name=deck.name)
    db.add(db_deck)
    db.commit()
    db.refresh(db_deck)
    return db_deck

# @app.post("/decks/{deck_name}/cards/")
# def add_card_to_deck(deck_name: str, card: Card):
#     if deck_name not in decks:
#         raise HTTPException(status_code=404, detail="Deck not found")
#     decks[deck_name].cards.append(card)
#     return {"message": f"Card added to deck '{deck_name}'."}

@app.post("/decks/{deck_id}/cards/", response_model=Card)
def add_card(deck_id: int, card: Card, db: Session = Depends(get_db)):
    db_card = CardDB(question=card.question, answer=card.answer, deck_id=deck_id)
    db.add(db_card)
    db.commit()
    db.refresh(db_card)
    return db_card

@app.put("/decks/{deck_id}/cards/{card_id}/review/")
def review_card(deck_id: int, card_id: int, correct: bool, db: Session = Depends(get_db)):
    card = db.query(CardDB).filter(CardDB.id == card_id, CardDB.deck_id == deck_id).first()

    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    if correct:
        card.box += 1
        card.last_reviewed = datetime.date.today()
    else:
        card.box = 1  # Reset if wrong

    if card.box == 1:
        card.next_review = datetime.date.today() + datetime.timedelta(days=1)
    elif card.box == 2:
        card.next_review = datetime.date.today() + datetime.timedelta(days=3)
    elif card.box == 3:
        card.next_review = datetime.date.today() + datetime.timedelta(days=7)

    db.commit()
    return {"message": "Card reviewed successfully."}

@app.delete("/decks/{deck_name}/cards/{question}")
def delete_card(deck_name: str, question: str):
    if deck_name not in decks:
        raise HTTPException(status_code=404, detail="Deck not found")

    card = next((c for c in decks[deck_name].cards if c.question == question), None)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    decks[deck_name].cards = [c for c in decks[deck_name].cards if c.question != question]
    return {"message": f"Card '{question}' deleted from deck '{deck_name}'."}

# @app.get("/decks/{deck_name}/progress/")
# def show_progress(deck_name: str):
#     if deck_name not in decks:
#         raise HTTPException(status_code=404, detail="Deck not found")
#
#     total_cards = len(decks[deck_name].cards)
#     reviewed_cards = len([card for card in decks[deck_name].cards if card.last_reviewed])
#     correct_cards = len([card for card in decks[deck_name].cards if card.box > 1])
#
#     return {
#         "total_cards": total_cards,
#         "reviewed_cards": reviewed_cards,
#         "correct_cards": correct_cards,
#         "accuracy": (correct_cards / reviewed_cards) * 100 if reviewed_cards else 0
#     }

@app.get("/decks/{deck_id}/progress/")
def show_progress(deck_id: int, db: Session = Depends(get_db)):
    total_cards = db.query(CardDB).filter(CardDB.deck_id == deck_id).count()
    reviewed_cards = db.query(CardDB).filter(CardDB.deck_id == deck_id, CardDB.last_reviewed != None).count()
    correct_cards = db.query(CardDB).filter(CardDB.deck_id == deck_id, CardDB.box > 1).count()

    return {
        "total_cards": total_cards,
        "reviewed_cards": reviewed_cards,
        "correct_cards": correct_cards,
        "accuracy": (correct_cards / reviewed_cards) * 100 if reviewed_cards > 0 else 0
    }

import json

@app.get("/decks/{deck_id}/export/")
def export_deck(deck_id: int, db: Session = Depends(get_db)):
    deck = db.query(DeckDB).filter(DeckDB.id == deck_id).first()

    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")

    deck_data = {
        "name": deck.name,
        "cards": [{"question": card.question, "answer": card.answer, "box": card.box} for card in deck.cards]
    }
    return json.dumps(deck_data)

@app.post("/decks/import/")
def import_deck(deck_data: dict, db: Session = Depends(get_db)):
    db_deck = DeckDB(name=deck_data['name'])
    db.add(db_deck)
    db.commit()
    db.refresh(db_deck)

    for card_data in deck_data['cards']:
        db_card = CardDB(question=card_data['question'], answer=card_data['answer'], box=card_data['box'], deck_id=db_deck.id)
        db.add(db_card)

    db.commit()
    return {"message": "Deck imported successfully"}
