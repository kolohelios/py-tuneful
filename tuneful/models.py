import os.path

from flask import url_for
from sqlalchemy import Column, Integer, String, Sequence, ForeignKey
from sqlalchemy.orm import relationship

from tuneful import app
from .database import Base, engine

class Song(Base):
    __tablename__ = 'songs'
    
    def as_dictionary(self):
        return {
            "id": self.id,
            "file": self.file.as_dictionary()
        }
    
    id = Column(Integer, primary_key = True)
    file = relationship('File', uselist = False, backref = 'song')
    
class File(Base):
    __tablename__ = 'files'
    
    def as_dictionary(self):
        return {
            "id": self.id,
            "name": self.filename,
            "path": url_for('uploaded_file', filename = self.filename)
        }
    
    id = Column(Integer, primary_key = True)
    filename = Column(String(1024), nullable = False)
    song_id = Column(Integer, ForeignKey('songs.id'))