import os.path
import json

from flask import request, Response, url_for, send_from_directory
from werkzeug.utils import secure_filename
from jsonschema import validate, ValidationError

from . import models
from . import decorators
from tuneful import app
from .database import session
from .utils import upload_path

song_schema = {
    "properties": {
        "file": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "number"
                }
            },
            "required": ["id"]
        }
    },
    "required": ["file"]
}

@app.route('/api/songs', methods = ['GET'])
@decorators.accept('application/json')
def songs_get():
    ''' get a list of songs '''
    
    songs = session.query(models.Song)
    songs = songs.order_by(models.Song.id)

    data = json.dumps([song.as_dictionary() for song in songs])
    return Response(data, 200, mimetype = 'application/json')

@app.route('/api/songs/<int:id>', methods = ['GET'])
@decorators.accept('application/json')
def song_get(id):
    ''' get a single song '''
    
    song = session.query(models.Song).get(id)
    
    data = json.dumps(song.as_dictionary())
    return Response(data, 200, mimetype = 'application/json')

@app.route('/api/songs', methods = ['POST'])
@decorators.accept('application/json')
@decorators.require('application/json')
def songs_post():
    ''' add a new song '''
    data = request.json
        
    # check that the JSON supplied is valid
    # if not you return a 422 Unprocessable Entity
    try:
        validate(data, song_schema)
    except ValidationError as error:
        data = {'message': error.message}
        return Response(json.dumps(data), 422, mimetype = 'application/json')
    
    file = session.query(models.File).get(data['file']['id'])
    
    # if the file does not exist we will return a 404 error
    if not file:
        message = 'Could not find file with id {}'.format(data['file']['id'])
        data = json.dumps({'message': message})
        return Response(data, 404, mimetype = 'application/json')
    
    song = models.Song(file = file)
    session.add(song)
    session.commit()
    
    # return a 201 Created, containing the post as JSON and with the
    # Location header set to the location of the post
    print(song.as_dictionary())
    data = json.dumps(song.as_dictionary())
    headers = {'Location': url_for('song_get', id = song.id)}
    return Response(data, 201, headers = headers, mimetype = 'application/json')
    
    