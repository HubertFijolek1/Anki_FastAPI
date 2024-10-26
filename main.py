from fastapi import FastAPI, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import List, Optional
import datetime
from sqlalchemy import Column, Integer, String, Date, ForeignKey, Float, create_engine
from sqlalchemy.orm import relationship, sessionmaker, Session, declarative_base
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from fastapi.templating import Jinja2Templates
import json

# SQLAlchemy setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# JWT Config
SECRET_KEY = "123"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Setup Jinja2 templates directory
templates = Jinja2Templates(directory="templates")


# Database Models
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)


class CardDB(Base):
    __tablename__ = 'cards'
    id = Column(Integer, primary_key=True, index=True)
    question = Column(String, index=True)
    answer = Column(String)
    box = Column(Integer, default=1)
    interval = Column(Integer, default=1)
    ease_factor = Column(Float, default=2.5)
    repetitions = Column(Integer, default=0)
    last_reviewed = Column(Date)
    next_review = Column(Date)
    deck_id = Column(Integer, ForeignKey('decks.id'))


class DeckDB(Base):
    __tablename__ = 'decks'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    cards = relationship("CardDB", back_populates="deck")


class CardReviewHistory(Base):
    __tablename__ = 'review_history'
    id = Column(Integer, primary_key=True, index=True)
    card_id = Column(Integer, ForeignKey('cards.id'))
    user_id = Column(Integer, ForeignKey('users.id'))
    correct = Column(Integer)
    review_date = Column(Date, default=datetime.date.today)


Base.metadata.create_all(bind=engine)


# Dependency for getting DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Pydantic Models
class Card(BaseModel):
    question: str
    answer: str
    box: int = 1
    last_reviewed: Optional[datetime.date] = None
    next_review: datetime.date = datetime.date.today()


class Deck(BaseModel):
    name: str
    cards: List[Card] = []


# FastAPI app instance
app = FastAPI()


# Helper function to get the current user from JWT token
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid authentication")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid user")
    return user


# Routes for User Registration and Login
@app.post("/register/")
def register_user(username: str, password: str, db: Session = Depends(get_db)):
    hashed_password = pwd_context.hash(password)
    user = User(username=username, hashed_password=hashed_password)
    db.add(user)
    db.commit()
    return {"message": "User created successfully"}


@app.post("/token/")
def login(username: str, password: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user or not pwd_context.verify(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = jwt.encode({"sub": username}, SECRET_KEY, algorithm=ALGORITHM)
    return {"access_token": token, "token_type": "bearer"}


# Routes for Deck Management
@app.post("/decks/")
def create_deck(deck: Deck, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_deck = DeckDB(name=deck.name, user_id=current_user.id)
    db.add(db_deck)
    db.commit()
    db.refresh(db_deck)
    return db_deck


@app.get("/decks/{deck_id}/")
def get_deck(deck_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    deck = db.query(DeckDB).filter(DeckDB.id == deck_id, DeckDB.user_id == current_user.id).first()
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")
    return deck


@app.get("/decks/")
def get_decks(request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    decks = db.query(DeckDB).filter(DeckDB.user_id == current_user.id).all()
    return templates.TemplateResponse("decks.html", {"request": request, "decks": decks, "user": current_user})


@app.get("/decks/{deck_id}/export/")
def export_deck(deck_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    deck = db.query(DeckDB).filter(DeckDB.id == deck_id, DeckDB.user_id == current_user.id).first()
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")

    deck_data = {
        "name": deck.name,
        "cards": [{"question": card.question, "answer": card.answer, "box": card.box} for card in deck.cards]
    }
    return deck_data


@app.post("/decks/import/")
def import_deck(deck_data: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_deck = DeckDB(name=deck_data['name'], user_id=current_user.id)
    db.add(db_deck)
    db.commit()
    db.refresh(db_deck)
    for card_data in deck_data['cards']:
        db_card = CardDB(
            question=card_data['question'],
            answer=card_data['answer'],
            box=card_data.get('box', 1),
            deck_id=db_deck.id
        )
        db.add(db_card)
    db.commit()
    return {"message": "Deck imported successfully"}


@app.get("/decks/{deck_id}/progress/")
def show_progress(deck_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    total_cards = db.query(CardDB).filter(CardDB.deck_id == deck_id, DeckDB.user_id == current_user.id).count()
    reviewed_cards = db.query(CardReviewHistory).filter(CardReviewHistory.user_id == current_user.id,
                                                        CardReviewHistory.card_id == CardDB.id).count()
    correct_reviews = db.query(CardReviewHistory).filter(CardReviewHistory.user_id == current_user.id,
                                                         CardReviewHistory.correct == True).count()

    # Example streak logic: How many consecutive days the user has reviewed cards
    review_dates = db.query(CardReviewHistory.review_date).filter(
        CardReviewHistory.user_id == current_user.id).distinct().all()
    streak = calculate_streak(review_dates)

    return {
        "total_cards": total_cards,
        "reviewed_cards": reviewed_cards,
        "correct_reviews": correct_reviews,
        "streak": streak,
        "accuracy": (correct_reviews / reviewed_cards) * 100 if reviewed_cards > 0 else 0
    }


def calculate_streak(review_dates):
    streak = 0
    today = datetime.date.today()
    for i, date in enumerate(sorted(review_dates, reverse=True)):
        if date != today - datetime.timedelta(days=i):
            break
        streak += 1
    return streak


# Review a Card with SM2 Algorithm
def update_review_sm2(card, quality):
    if quality >= 3:
        if card.repetitions == 0:
            card.interval = 1
        elif card.repetitions == 1:
            card.interval = 6
        else:
            card.interval = round(card.interval * card.ease_factor)

        card.repetitions += 1
        card.ease_factor += (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
        if card.ease_factor < 1.3:
            card.ease_factor = 1.3
    else:
        card.interval = 1
        card.repetitions = 0

    card.next_review = datetime.date.today() + datetime.timedelta(days=card.interval)
    card.last_reviewed = datetime.date.today()


@app.put("/decks/{deck_id}/cards/{card_id}/review/")
def review_card(deck_id: int, card_id: int, quality: int, db: Session = Depends(get_db),
                current_user: User = Depends(get_current_user)):
    card = db.query(CardDB).join(DeckDB).filter(CardDB.id == card_id, DeckDB.id == deck_id,
                                                DeckDB.user_id == current_user.id).first()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    update_review_sm2(card, quality)
    db.commit()
    return {"message": "Card reviewed successfully."}
