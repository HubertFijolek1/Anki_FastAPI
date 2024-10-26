from fastapi import FastAPI
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

@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}
