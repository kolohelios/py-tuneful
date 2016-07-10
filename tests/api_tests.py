import unittest
import os
import shutil
import json
try: from urllib.parse import urlparse
except ImportError: from urlparse import urlparse # Py2 compatibility
from io import StringIO, BytesIO

import sys; print(list(sys.modules.keys()))
# Configure our app to use the testing databse
os.environ["CONFIG_PATH"] = "tuneful.config.TestingConfig"

from tuneful import app
from tuneful import models
from tuneful.utils import upload_path
from tuneful.database import Base, engine, session

class TestAPI(unittest.TestCase):
    """ Tests for the tuneful API """

    def setUp(self):
        """ Test setup """
        self.client = app.test_client()

        # Set up the tables in the database
        Base.metadata.create_all(engine)

        # Create folder for test uploads
        os.mkdir(upload_path())

    def tearDown(self):
        """ Test teardown """
        session.close()
        # Remove the tables and their data from the database
        Base.metadata.drop_all(engine)

        # Delete test upload folder
        shutil.rmtree(upload_path())
        
    def test_get_with_unsupported_accept_header(self):
        response = self.client.get('/api/songs',
            headers = [('Accept', 'application/xml')]
        )
        
        self.assertEqual(response.status_code, 406)
        self.assertEqual(response.mimetype, 'application/json')
        
        data = json.loads(response.data.decode('ascii'))
        self.assertEqual(data['message'],
            'Request must accept application/json data')

    def test_get_empty_songs(self):
        ''' getting songs from an empty database '''
        response = self.client.get('/api/songs',
            headers = [('Accept', 'application/json')]
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, 'application/json')
        
        data = json.loads(response.data.decode('ascii'))
        self.assertEqual(data, [])
        
    def test_get_songs(self):
        fileA = models.File(filename = 'Test Song A.mp3')
        fileB = models.File(filename = 'Test Song B.mp3')
        songA = models.Song(file = fileA)
        songB = models.Song(file = fileB)
        session.add_all([fileA, fileB, songA, songB])
        session.commit()
        
        response = self.client.get('/api/songs',
            headers = [('Accept', 'application/json')]
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, 'application/json')

        data = json.loads(response.data.decode('ascii'))
        self.assertEqual(len(data), 2)
        
        songA = data[0]
        self.assertEqual(songA['id'], 1)
        self.assertEqual(songA['file']['id'], 1)
        self.assertEqual(songA['file']['name'], 'Test Song A.mp3')
        
        songB = data[1]
        self.assertEqual(songB['id'], 2)
        self.assertEqual(songB['file']['id'], 2)
        self.assertEqual(songB['file']['name'], 'Test Song B.mp3')
    
    def test_get_song(self):
        ''' get a single song from the API and make sure it is
        the one that we requested and not a different one 
        from the DB '''
        
        fileA = models.File(filename = 'Test Song A.mp3')
        fileB = models.File(filename = 'Test Song B.mp3')
        songA = models.Song(file = fileA)
        songB = models.Song(file = fileB)
        session.add_all([fileA, fileB, songA, songB])
        session.commit()
        
        response = self.client.get('/api/songs/1',
            headers = [('Accept', 'application/json')]
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, 'application/json')

        data = json.loads(response.data.decode('ascii'))
        self.assertEqual(len(data), 2)
        
        self.assertEqual(data['id'], 1)
        self.assertEqual(data['file']['id'], 1)
        self.assertEqual(data['file']['name'], 'Test Song A.mp3')
    
        self.assertNotEqual(data['id'], 2)
        self.assertNotEqual(data['file']['id'], 2)
        self.assertNotEqual(data['file']['name'], 'Test Song B.mp3')
        
    def test_post_song(self):
        ''' posting a new song '''
        file = models.File(filename = 'Test Song.mp3')
        session.add(file)
        session.commit()
        
        data = {
            "file": {
                "id": 1
            }
        }
        
        response = self.client.post('/api/songs',
            data = json.dumps(data),
            content_type = 'application/json',
            headers = [('Accept', 'application/json')]
        )
        
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.mimetype, 'application/json')
        self.assertEqual(urlparse(response.headers.get('Location')).path,
            '/api/songs/1')
        
        data = json.loads(response.data.decode('ascii'))
        self.assertEqual(data['id'], 1)
        self.assertEqual(data['file']['id'], file.id)
        self.assertEqual(data['file']['name'], 'Test Song.mp3')
        
        songs = session.query(models.Song).all()
        self.assertEqual(len(songs), 1)
        
        song = songs[0]
        
        self.assertEqual(song.id, 1)
        self.assertEqual(song.file.id, 1)
        self.assertEqual(song.file.filename, 'Test Song.mp3')
        
    def test_post_with_unsupported_accept_header(self):
        response = self.client.post('/api/songs',
            headers = [('Accept', 'application/xml')]
        )
        
        self.assertEqual(response.status_code, 406)
        self.assertEqual(response.mimetype, 'application/json')
        
        data = json.loads(response.data.decode('ascii'))
        self.assertEqual(data['message'],
            'Request must accept application/json data')
        
    def test_post_song_with_nonexistent_file(self):
        ''' try posting a new song with bad file id '''
        
        data = {
            "file": {
                "id": 8
            }
        }
        
        response = self.client.post('/api/songs',
            data = json.dumps(data),
            content_type = 'application/json',
            headers = [('Accept', 'application/json')]
        )
        
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.mimetype, 'application/json')
       
        data = json.loads(response.data.decode('ascii'))
        self.assertEqual(data['message'],
            'Could not find file with id 8')
            
    def test_post_song_with_invalid_file_id_type(self):
        ''' try posting a new song with a file that 
        has an id of the wrong type '''
        
        data = {
            "file": {
                "id": 'whatsup'
            }
        }
        
        response = self.client.post('/api/songs',
            data = json.dumps(data),
            content_type = 'application/json',
            headers = [('Accept', 'application/json')]
        )
        
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.mimetype, 'application/json')
       
        data = json.loads(response.data.decode('ascii'))
        self.assertEqual(data['message'],
            '\'whatsup\' is not of type \'number\'')
    
    def test_post_song_with_invalid_json_structure(self):
        ''' try posting a new song with a file that 
        has only a key:value pair insted of a file object '''
        
        data = {
            "file": 8
        }
        
        response = self.client.post('/api/songs',
            data = json.dumps(data),
            content_type = 'application/json',
            headers = [('Accept', 'application/json')]
        )
        
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.mimetype, 'application/json')
       
        data = json.loads(response.data.decode('ascii'))
        self.assertEqual(data['message'],
            '8 is not of type \'object\'')
    
    def test_post_song_with_unsupported_mimetype(self):
        data = '<xml></xml>'
        response = self.client.post('/api/songs',
            data = json.dumps(data),
            content_type = 'application/xml',
            headers = [('Accept', 'application/json')]
        )
        
        self.assertEqual(response.status_code, 415)
        self.assertEqual(response.mimetype, 'application/json')
        
        data = json.loads(response.data.decode('ascii'))
        self.assertEqual(data['message'],
            'Request must contain application/json data')
       
    def test_put_song(self):
        ''' updating a song '''
        
        fileA = models.File(filename = 'Test Song A.mp3')
        fileB = models.File(filename = 'Test Song B.mp3')
        song = models.Song(file = fileA)
        session.add_all([fileA, fileB, song])
        session.commit()
        
        data = {
            "file": {
                "id": 2
            }
        }
        
        response = self.client.put('/api/songs/1',
            data = json.dumps(data),
            content_type = 'application/json',
            headers = [('Accept', 'application/json')]
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, 'application/json')
        self.assertEqual(urlparse(response.headers.get('Location')).path,
            '/api/songs/1')
        
        data = json.loads(response.data.decode('ascii'))
        self.assertEqual(data['id'], 1)
        self.assertEqual(data['file']['id'], 2)
        self.assertEqual(data['file']['name'], 'Test Song B.mp3')
        
        songs = session.query(models.Song).all()
        self.assertEqual(len(songs), 1)
        
        song = songs[0]
        
        self.assertEqual(song.id, 1)
        self.assertEqual(song.file.id, 2)
        self.assertEqual(song.file.filename, 'Test Song B.mp3')
        
    def test_put_song_with_nonexistent_id(self):
        ''' updating a song '''
        
        fileA = models.File(filename = 'Test Song A.mp3')
        fileB = models.File(filename = 'Test Song B.mp3')
        song = models.Song(file = fileA)
        session.add_all([fileA, fileB, song])
        session.commit()
        
        data = {
            "file": {
                "id": 2
            }
        }
        
        response = self.client.put('/api/songs/8',
            data = json.dumps(data),
            content_type = 'application/json',
            headers = [('Accept', 'application/json')]
        )
        
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.mimetype, 'application/json')
       
        data = json.loads(response.data.decode('ascii'))
        self.assertEqual(data['message'],
            'Could not find song with id 8')
            
    def test_put_with_unsupported_accept_header(self):
        response = self.client.put('/api/songs/1',
            headers = [('Accept', 'application/xml')]
        )
        
        self.assertEqual(response.status_code, 406)
        self.assertEqual(response.mimetype, 'application/json')
        
        data = json.loads(response.data.decode('ascii'))
        self.assertEqual(data['message'],
            'Request must accept application/json data')
    
    def test_put_song_with_nonexistent_file(self):
        ''' updating a song '''
        
        file = models.File(filename = 'Test Song A.mp3')
        song = models.Song(file = file)
        session.add_all([file, song])
        session.commit()
        
        data = {
            "file": {
                "id": 19
            }
        }
        
        response = self.client.put('/api/songs/1',
            data = json.dumps(data),
            content_type = 'application/json',
            headers = [('Accept', 'application/json')]
        )
        
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.mimetype, 'application/json')
       
        data = json.loads(response.data.decode('ascii'))
        self.assertEqual(data['message'],
            'Could not find file with id 19')
    
    def test_put_song_with_unsupported_mimetype(self):
        data = '<xml></xml>'
        response = self.client.put('/api/songs/1',
            data = json.dumps(data),
            content_type = 'application/xml',
            headers = [('Accept', 'application/json')]
        )
        
        self.assertEqual(response.status_code, 415)
        self.assertEqual(response.mimetype, 'application/json')
        
        data = json.loads(response.data.decode('ascii'))
        self.assertEqual(data['message'],
            'Request must contain application/json data')
            
    def test_put_song_with_invalid_file_id_type(self):
        ''' try putting a song with a file that 
        has an id of the wrong type '''
        
        file = models.File(filename = 'Test Song A.mp3')
        song = models.Song(file = file)
        session.add_all([file, song])
        session.commit()
        
        data = {
            "file": {
                "id": 'whatsup'
            }
        }
        
        response = self.client.put('/api/songs/1',
            data = json.dumps(data),
            content_type = 'application/json',
            headers = [('Accept', 'application/json')]
        )
        
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.mimetype, 'application/json')
       
        data = json.loads(response.data.decode('ascii'))
        self.assertEqual(data['message'],
            '\'whatsup\' is not of type \'number\'')
            
    def test_put_song_with_invalid_json_structure(self):
        ''' try putting a song with a file that 
        has only a key:value pair insted of a file object '''
        
        file = models.File(filename = 'Test Song A.mp3')
        song = models.Song(file = file)
        session.add_all([file, song])
        session.commit()
        
        data = {
            "file": 8
        }
        
        response = self.client.put('/api/songs/1',
            data = json.dumps(data),
            content_type = 'application/json',
            headers = [('Accept', 'application/json')]
        )
        
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.mimetype, 'application/json')
       
        data = json.loads(response.data.decode('ascii'))
        self.assertEqual(data['message'],
            '8 is not of type \'object\'')
            
    def test_delete_song(self):
        ''' delete a song '''
        
        file = models.File(filename = 'Test Song A.mp3')
        song = models.Song(file = file)
        session.add_all([file, song])
        session.commit()
        
        response = self.client.delete('/api/songs/1',
            headers = [('Accept', 'application/json')]
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, 'application/json')
       
        data = json.loads(response.data.decode('ascii'))
        self.assertEqual(data['message'],
            'Successfully deleted song with id 1')
            
    def test_delete_song_with_nonexistent_id(self):
        ''' attempt to delete a song with an ID that does not exist '''
        
        response = self.client.delete('/api/songs/8',
            headers = [('Accept', 'application/json')]
        )
        
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.mimetype, 'application/json')
       
        data = json.loads(response.data.decode('ascii'))
        self.assertEqual(data['message'],
            'Could not find song with id 8')
            
    def test_delete_with_unsupported_accept_header(self):
        response = self.client.delete('/api/songs/1',
            headers = [('Accept', 'application/xml')]
        )
        
        self.assertEqual(response.status_code, 406)
        self.assertEqual(response.mimetype, 'application/json')
        
        data = json.loads(response.data.decode('ascii'))
        self.assertEqual(data['message'],
            'Request must accept application/json data')
            
    def test_get_uploaded_file(self):
        path = upload_path('test.txt')
        with open(path, 'wb') as f:
            f.write(b'File contents')
        
        response = self.client.get('/uploads/test.txt')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, 'text/plain')
        self.assertEqual(response.data, b'File contents')
        
    def test_file_upload(self):
        data = {
            'file': (BytesIO(b'File contents'), 'test.txt')
        }
        
        response = self.client.post('/api/files',
            data = data,
            content_type = 'multipart/form-data',
            headers = [('Accept', 'application/json')]
        )
        
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.mimetype, 'application/json')
        
        data = json.loads(response.data.decode('ascii'))
        self.assertEqual(urlparse(data['path']).path, '/uploads/test.txt')

        path = upload_path('test.txt')
        self.assertTrue(os.path.isfile(path))
        with open(path, 'rb') as f:
            contents = f.read()
        self.assertEqual(contents, b'File contents')