
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


def blobList(prefix, boolean):
    storage_client = storage.Client(project=local_constants.PROJECT_NAME)
    delimiter=None

    if boolean==True:
        delimiter='/'
        

    return storage_client.list_blobs(local_constants.PROJECT_STORAGE_BUCKET, prefix=prefix, delimiter=delimiter)

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

@app.route('/addDirectory/<path:name>', methods=['POST', 'GET'])
def addDirectoryPageHandler(name):
    
    return render_template('addDirectory.html', path=name)

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

            blob_list = blobList(None, False) 
            for i in blob_list:
                if i.name == session['email']+'/':
                    directory_list.append(i)
                 


            if len(directory_list)==0:
                addDirectory(session['email']+'/')
                blob_list = blobList(None, False) 
                for i in blob_list:
                    if i.name == session['email']+'/':
                        directory_list.append(i)
                        session['location']=i
                        

            
            
        except ValueError as exc: 
            error_message = str(exc)
        
        #print(error_message)

    return render_template('indexPage.html', user_data=claims, error_message=error_message, user_info=user_info, root=session['email']+'/', directory_list=directory_list)

@app.route('/add_directory/<path:name>/', methods=['POST']) 
def addDirectoryHandler(name):
    id_token = request.cookies.get("token") 
    error_message = None
    claims = None
    times = None
    user_info = None
    directory=[]
    count=0
    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)

            directory_name = request.form['Fname']
            if directory_name == '' or directory_name[len(directory_name) - 1] != '/':
                flash('A directory should have a directory name followed by a /')
                return render_template('addDirectory.html')
            name=name+'/'

            directory_name = name+directory_name
            print(directory_name)
            user_info = retrieveUserInfo(claims)
            directory=user_info['directory_list_keys']

            for d in directory:
                if d == directory_name:
                    flash('You should not have two directories with the same name')
                    return render_template('addDirectory.html')

            addDirectory(directory_name)
            directory.append(directory_name)
            print(directory)
            user_info.update({
                'directory_list_keys': directory
            })
            datastore_client.put(user_info)
            count = directory_name.count('/')
            createDirectory(claims, directory_name)
            flash('You have successfully created a new directory')
            session['location']=directory_name
            directory.remove(directory_name)
            print('this is addDi',session['location'])
       
        except ValueError as exc: 
            error_message = str(exc)

    return render_template('directoryPage.html', directory_list=directory, user_info=user_info, count=count)

@app.route('/show/<path:name>/', methods=['POST', 'GET'])
def showDirectory(name):
    id_token = request.cookies.get("token") 
    error_message = None
    claims = None
    name = name+'/'
    user_info = None
    directory_list=[]
    count=0
    prefix=None

    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
            user_info = retrieveUserInfo(claims)
           
            blob_list = blobList(name, True)
            for i in blob_list:
                if i.name[len(i.name)-1]=='/':
                    session['location']=name
            for prefix in blob_list.prefixes:
                directory_list.append(prefix)
                count = prefix.count('/')
                print(session['location'])     

        except ValueError as exc: 
            error_message = str(exc)
    
    return render_template('directoryPage.html', directory_list=directory_list, user_info=user_info, count=count, path=session['location'])

@app.route('/way/<path:vn>', methods=['POST', 'GET'])
def changeDirectory(vn):
    id_token = request.cookies.get("token") 
    error_message = None
    claims = None
    name = session['location']
    user_info = None
    directory_list=[]
    count=0
    prefix=None

    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
            user_info = retrieveUserInfo(claims)
            myList=''
            count = vn.count('/')
            temp=vn.split('/')
            
            for i in range(count-1):
                myList=myList+temp[i]+"/"

            blob_list = blobList(myList, True)
            for i in blob_list:
                if i.name[len(i.name)-1]=='/':
                    sc=0
            for prefix in blob_list.prefixes:
                directory_list.append(prefix) 
            count=count-1
        except ValueError as exc: 
            error_message = str(exc)
    
    return render_template('directoryPage.html', directory_list=directory_list, user_info=user_info, count=count, path=myList)


@app.route('/delete/<path:name>', methods=['POST', 'GET'])
def deleteDirectory(name):

    id_token = request.cookies.get("token") 
    error_message = None
    claims = None
    name = name
    user_info = None
    directory_list=[]
    temp=[]

    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
            user_info = retrieveUserInfo(claims)
            print('this is'+name)
            blob_list = blobList(name, None)
            for i in blob_list:
                if i.name[len(i.name)-1]=='/' and i.name != name:
                        print(i.name)
                        directory_list.append(i)
                        #session['location']=name
            
            if len(directory_list)!=0:
                flash('This directory has contain so cannot delete it ')
                return render_template('directoryPage.html', directory_list=directory_list)

            mylist = user_info['directory_list_keys']
            
            for n in range(len(mylist)):
                if not name.find(mylist[n])>=0:
                    temp.append(mylist[n])
            
            print(temp)
            delete_blob(name)

            user_info.update({
                'directory_list_keys':temp
            })

            datastore_client.put(user_info) 
            
            directory_list=[]
            blob_list = blobList(session['location'], None)
            for i in blob_list:
                if i.name[len(i.name)-1]=='/' and i.name != name:
                    print(i.name)
                    directory_list.append(i)
                    session['location']=name
        
        except ValueError as exc: 
            error_message = str(exc)
    
    return redirect('/')


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
