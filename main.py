import datetime
import local_constants
from flask import Flask, render_template, request, redirect, Response, session, flash
from google.cloud import datastore
import google.oauth2.id_token
from google.auth.transport import requests
from google.cloud import storage
from google.cloud.storage.blob import Blob

app = Flask(__name__)
app.secret_key = '12345'

# get access to the datastore client so we can add and store data in the datastore
datastore_client = datastore.Client()



# get access to a request adapter for firebase as we will need this to authenticate users
firebase_request_adapter = requests.Request()

def createUserInfo(claims):
    entity_key = datastore_client.key('user_info', claims['email']) 
    entity = datastore.Entity(key = entity_key)
    entity.update({
        'email': claims['email'],
        'directory_list_keys':[] 
    })

    datastore_client.put(entity)

def retrieveUserInfo(claims):
    entity_key = datastore_client.key('user_info', claims['email']) 
    entity = datastore_client.get(entity_key)
   
    return entity

def createDirectory(claims, name):
    entity_key = datastore_client.key('user_info', claims['email'], 'Directory', name)
    entity = datastore.Entity(key=entity_key)
    
    entity.update({
        'name': name,
        'subdirectories':[],
    })
    datastore_client.put(entity)  

def retrieveCurrentDirectory(claims, name):
    entity_key = datastore_client.key('user_info', claims['email'], 'Directory', name)
    entity = datastore_client.get(entity_key)

    return entity


def retrieveDirectory(claims):
    user_info=retrieveUserInfo(claims)
    directory_names=user_info['directory_list_keys']

    return directory_names


def blobList(prefix):
    storage_client = storage.Client(project=local_constants.PROJECT_NAME)

    return storage_client.list_blobs(local_constants.PROJECT_STORAGE_BUCKET, prefix=prefix)

def delete_blob(blob_name):
   
    storage_client = storage.Client(project=local_constants.PROJECT_NAME)
    bucket = storage_client.bucket(local_constants.PROJECT_STORAGE_BUCKET)

    blob = bucket.blob(blob_name)
    blob.delete()


def addDirectory(directory_name):  
    storage_client = storage.Client(project=local_constants.PROJECT_NAME) 
    bucket = storage_client.bucket(local_constants.PROJECT_STORAGE_BUCKET)

    blob = bucket.blob(directory_name)
    blob.upload_from_string('', content_type='application/x-www-form- urlencoded;charset=UTF-8')

def addFile(file):
    storage_client = storage.Client(project=local_constants.PROJECT_NAME) 
    bucket = storage_client.bucket(local_constants.PROJECT_STORAGE_BUCKET)
    

    blob = bucket.blob("Tobi/Home/"+file.filename) 
    blob.upload_from_file(file)

def downloadBlob(filename):
    storage_client = storage.Client(project=local_constants.PROJECT_NAME) 
    bucket = storage_client.bucket(local_constants.PROJECT_STORAGE_BUCKET)
    
    blob = storage.Blob(filename, bucket)
    return blob.download_as_bytes() 

@app.route('/addDirectory', methods=['POST', 'GET'])
def addDirectoryPageHandler():
    
    return render_template('addDirectory.html')

@app.route('/booking/<int:id>', methods=['POST', 'GET'])
def bookingPageHandler(id):
    return render_template('booking.html', id=id)

@app.route('/')
def root():
    id_token = request.cookies.get("token") 
    error_message = None
    claims = None
    times = None
    user_info = None 
    root = True
    directory_list = []


    if id_token:

        try:

            claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
            user_info = retrieveUserInfo(claims) 
            if user_info == None:
                createUserInfo(claims)
            user_info = retrieveUserInfo(claims)
            session['email']=user_info['email']
            session['location']=session['email']+'/'
            mylist=user_info['directory_list_keys']

            blob_list = blobList(None) 
            for i in blob_list:
                if i.name == session['email']+'/':
                    directory_list.append(i)
                 


            if len(directory_list)==0:
                addDirectory(session['email']+'/')
                blob_list = blobList(None) 
                for i in blob_list:
                    if i.name == session['email']+'/':
                        directory_list.append(i)
                        session['location']=i
                        

            print(directory_list)
            
        except ValueError as exc: 
            error_message = str(exc)
        
        #print(error_message)

    return render_template('indexPage.html', user_data=claims, error_message=error_message, user_info=user_info, root=session['email']+'/', directory_list=directory_list)

@app.route('/add_directory', methods=['POST']) 
def addDirectoryHandler():
    id_token = request.cookies.get("token") 
    error_message = None
    claims = None
    times = None
    user_info = None
    directory=[]
    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)

            directory_name = request.form['Fname']
            if directory_name == '' or directory_name[len(directory_name) - 1] != '/':
                flash('A directory should have a directory name followed by a /')
                return render_template('addDirectory.html')
            
            directory_name = session['location']+directory_name
            user_info = retrieveUserInfo(claims)
            directory=user_info['directory_list_keys']

            for d in directory:
                if d == directory_name:
                    flash('You should not have two directories with the same name')
                    return render_template('addDirectory.html')

            addDirectory(directory_name)
            directory.append(directory_name)
            
            user_info.update({
                'directory_list_keys': directory
            })
            datastore_client.put(user_info)

            createDirectory(claims, directory_name)
            flash('You have successfully created a new directory')
            session['location']=directory_name

        except ValueError as exc: 
            error_message = str(exc)

    return render_template('directoryPage.html', directory_list=directory, user_info=user_info)

@app.route('/show/<string:name>/', methods=['POST', 'GET'])
def showDirectory(name):
    id_token = request.cookies.get("token") 
    error_message = None
    claims = None
    name = name+'/'
    user_info = None
    directory_list=[]

    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
            user_info = retrieveUserInfo(claims)
           
            blob_list = blobList(name)
            for i in blob_list:
                if i.name[len(i.name)-1]=='/' and i.name != name:
                    print(i.name)
                    directory_list.append(i)
                    session['location']=name
                

        except ValueError as exc: 
            error_message = str(exc)
    
    return render_template('directoryPage.html', directory_list=directory_list, user_info=user_info)

@app.route('/delete/<path:name>', methods=['POST', 'GET'])
def deleteDirectory(name):

    id_token = request.cookies.get("token") 
    error_message = None
    claims = None
    name = name
    user_info = None
    directory_list=[]

    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
            user_info = retrieveUserInfo(claims)
            print('this is'+name)
            blob_list = blobList(name)
            for i in blob_list:
                if i.name[len(i.name)-1]=='/' and i.name != name:
                        print(i.name)
                        directory_list.append(i)
                        #session['location']=name
            
            print(directory_list)
            print(session['location'])

        except ValueError as exc: 
            error_message = str(exc)
    
    return render_template('directoryPage.html')


@app.route('/upload_file', methods=['post']) 
def uploadFileHandler():
    id_token = request.cookies.get("token") 
    error_message = None
    claims = None
    times = None
    user_info = None
    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)

            file = request.files['file_name'] 
            if file.filename == '':
                return redirect('/')
            user_info = retrieveUserInfo(claims) 
            addFile(file)

        except ValueError as exc: error_message = str(exc)
    return redirect('/')

@app.route('/download_file/<string:filename>', methods=['POST']) 
def downloadFile(filename):
    id_token = request.cookies.get("token") 
    error_message = None
    claims = None
    times = None
    user_info = None 
    file_bytes = None

    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)

        except ValueError as exc: 
            error_message = str(exc)

    return Response(downloadBlob(filename), mimetype='application/pdf')



if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
