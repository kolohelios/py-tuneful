import os.path

from flask import url_for
from sqlalchemy import Column, Integer, String, Sequence, ForeignKey
from sqlalchemy.orm import relationship

from tuneful import app
from .database import Base, engine

class Song(Base):
    __tablename__ = 'songs'
    
    def as_dictionary(self):
        song = {
            "id": self.id,
            "file": {
                "id": self.file.id,
                "name": self.file.name
            }
        }
        return song
    
    id = Column(Integer, primary_key = True)
    file = relationship('File', uselist = False, backref = 'song')
    
class File(Base):
    __tablename__ = 'files'
    
    def as_dictionary(self):
        file = {
            'id': self.id,
            'name': self.name
        }
    
    id = Column(Integer, primary_key = True)
    name = Column(String(1024), nullable = False)
    song_id = Column(Integer, ForeignKey('songs.id'))