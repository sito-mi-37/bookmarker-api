from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import backref
from enum import unique
from datetime import datetime
import string
import random

db = SQLAlchemy()

# define User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(10), unique = True, nullable = False )
    email = db.Column(db.String(40), unique = True, nullable = False )
    password = db.Column(db.String(40), nullable = False)
    bookmark = db.relationship("Bookmark", backref="user" )
    created_at = db.Column(db.DateTime, default= datetime.now())
    updated_at = db.Column(db.DateTime, onupdate = datetime.now())

   

    def __repr__(self) -> str :
        return f"username>>>{self.username}"

    

class Bookmark(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text(200), nullable=True)
    url = db.Column(db.String, nullable = False)
    short_url = db.Column(db.String(3), nullable = False)
    visited = db.Column(db.Integer, default= 0)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    created_at = db.Column(db.DateTime, default= datetime.now())
    updated_at = db.Column(db.DateTime, onupdate = datetime.now())

    def generate_short_url(self):
        characters = string.digits + string.ascii_letters
        picked_letters = ''.join(random.choices(characters, k = 3))

        link = self.query.filter_by(short_url = picked_letters).first()
        if link:
            self.generate_short_url()
        else:
            return picked_letters

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.short_url = self.generate_short_url()



    def __repr__(self) -> str:
        return f"username>>>{self.url}"