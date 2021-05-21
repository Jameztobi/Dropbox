from flask import Flask, render_template, request, redirect, session, flash, Response
from google.cloud import datastore, storage
import google.oauth2.id_token
from google.auth.transport import requests
import json
import local_constants
import collections


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
        'directory_list_keys':[],
        'files_list_keys':[] 
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

def blob_metadata(blob_name):
    """Prints out a blob's metadata."""
    # bucket_name = 'your-bucket-name'
    # blob_name = 'your-object-name'

    storage_client = storage.Client(project=local_constants.PROJECT_NAME)
    bucket = storage_client.bucket(local_constants.PROJECT_STORAGE_BUCKET)

    # Retrieve a blob, and its metadata, from Google Cloud Storage.
    # Note that `get_blob` differs from `Bucket.blob`, which does not
    # make an HTTP request.
    blob = bucket.get_blob(blob_name)
    return blob.md5_hash
    


def addDirectory(directory_name):  
    storage_client = storage.Client(project=local_constants.PROJECT_NAME) 
    bucket = storage_client.bucket(local_constants.PROJECT_STORAGE_BUCKET)
    

    blob = bucket.blob(directory_name)
    blob.upload_from_string('', content_type='application/x-www-form- urlencoded;charset=UTF-8')

def addFile(path, file):
    storage_client = storage.Client(project=local_constants.PROJECT_NAME) 
    bucket = storage_client.bucket(local_constants.PROJECT_STORAGE_BUCKET)
    blob = bucket.blob(path+file.filename) 
    blob.upload_from_file(file)


def downloadBlob(filename):
    storage_client = storage.Client(project=local_constants.PROJECT_NAME) 
    bucket = storage_client.bucket(local_constants.PROJECT_STORAGE_BUCKET)
    
    blob = bucket.blob(filename)
    return blob.download_to_filename(filename)
 

@app.route('/addDirectory/<path:name>', methods=['POST', 'GET'])
def addDirectoryPageHandler(name):
    return render_template('addDirectory.html', path=name)

@app.route('/showDublicates', methods=['POST', 'GET'])
def dublicatesPageHandler():
    return render_template('showDublicates.html')

@app.route('/addFiles/<path:name>', methods=['POST', 'GET'])
def addFilePageHandler(name):
    id_token = request.cookies.get("token") 
    error_message = None
    claims = None
    user_info = None 
    data=[]
    file_list=[]

    if id_token:
        try: 
            claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
            user_info = retrieveUserInfo(claims)
            file_list=user_info['files_list_keys']
            blob_list = blobList(name, True)
            for i in blob_list:
                if i.name[len(i.name)-1]=='/':
                    session['location']=name
                if i.name[len(i.name)-1]!='/':
                    file_list.append(i.name)

        except ValueError as exc: 
            error_message = str(exc)
     
    return render_template('addFiles.html', path=name, data=json.dumps(file_list))

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
    files=[]
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
            #print(directory_name)
            user_info = retrieveUserInfo(claims)
            directory=user_info['directory_list_keys']
            files=user_info['files_list_keys']

            for d in directory:
                if d == directory_name:
                    flash('You should not have two directories with the same name')
                    return render_template('addDirectory.html')

            addDirectory(directory_name)
            directory.append(directory_name)
            #print(directory)
            user_info.update({
                'directory_list_keys': directory
            })
            datastore_client.put(user_info)
            count = directory_name.count('/')
            createDirectory(claims, directory_name)
            flash('You have successfully created a new directory')
            session['location']=directory_name
            directory.remove(directory_name)

       
        except ValueError as exc: 
            error_message = str(exc)

    return render_template('directoryPage.html', directory_list=directory, files=files, user_info=user_info, count=count)

@app.route('/show/<path:name>/', methods=['POST', 'GET'])
def showDirectory(name):
    id_token = request.cookies.get("token") 
    error_message = None
    claims = None
    name = name+'/'
    user_info = None
    directory_list=[]
    files=[]
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
                if i.name[len(i.name)-1]!='/':
                    files.append(i.name)
            for prefix in blob_list.prefixes:
                directory_list.append(prefix)
                count = prefix.count('/')
            if count ==0:
                count=name.count('/')       

        except ValueError as exc: 
            error_message = str(exc)
    
    return render_template('directoryPage.html', directory_list=directory_list, files=files, user_info=user_info, count=count, path=session['location'])

@app.route('/way/<path:vn>', methods=['POST', 'GET'])
def changeDirectory(vn):
    id_token = request.cookies.get("token") 
    error_message = None
    claims = None
    name = session['location']
    user_info = None
    directory_list=[]
    files=[]
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
                if i.name[len(i.name)-1]!='/':
                    files.append(i.name)
            for prefix in blob_list.prefixes:
                directory_list.append(prefix) 
            count=count-1
        except ValueError as exc: 
            error_message = str(exc)
    
    return render_template('directoryPage.html', directory_list=directory_list, files=files, user_info=user_info, count=count, path=myList)


@app.route('/delete/<path:name>', methods=['POST', 'GET'])
def deleteDirectory(name):

    id_token = request.cookies.get("token") 
    error_message = None
    claims = None
    name = name
    user_info = None
    directory_list=[]
    files=[]
    temp1=[]
    temp2=[]

    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
            user_info = retrieveUserInfo(claims)
           
          
            temp_list=user_info['files_list_keys']
            for i in range(len(temp_list)):
                if name.find(temp_list[i])>=0:
                    name=temp_list[i]

            blob_list = blobList(name, True)
            for i in blob_list:
                if i.name[len(i.name)-1]=='/' and i.name != name:
                    #print(i.name)
                    directory_list.append(i)
                    #session['location']=name
                else:
                    files.append(i)
            
            if len(directory_list) and len(files)!=0:
                flash('This directory has content so cannot be deleted ')
                return render_template('directoryPage.html', directory_list=directory_list)
            
            mylist = user_info['directory_list_keys']
            
            for n in range(len(mylist)):
                if not name.find(mylist[n])>=0:
                    temp1.append(mylist[n])
            
            mylist=user_info['files_list_keys']
            #print(name)
            for n in range(len(mylist)):
                if not name.find(mylist[n])>=0:
                    temp2.append(mylist[n])

            if not name.find(session['location'])>=0:
                name=session['location']+name

            delete_blob(name)

            user_info.update({
                'directory_list_keys':temp1,
                'files_list_keys':temp2
            })

            datastore_client.put(user_info) 
            
            directory_list=[]
            blob_list = blobList(session['location'], None)
            for i in blob_list:
                if i.name[len(i.name)-1]=='/' and i.name != name:
                    directory_list.append(i)
                    session['location']=name
        
        except ValueError as exc: 
            error_message = str(exc)
    
    return redirect('/')



@app.route('/upload_file/<path:name>', methods=['post']) 
def uploadFileHandler(name):
    id_token = request.cookies.get("token") 
    error_message = None
    claims = None
    times = None
    user_info = None
    myList=[]
    directory=[]
    directory_list=[]
    path=None
    count=0
    files=[]
    my_list=None
    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
            temp=request.form.get('mode')
            file = request.files['file_name'] 
            if file.filename == '':
                flash('This not allowed')
                return redirect('/')
            if temp == "change":
                temp1=file.filename
                temp3=temp1.split('.').pop()
                temp2=temp1[0 : temp1.rfind('.')]
                file.filename= temp2 + "new" + "."+temp3
            
            user_info = retrieveUserInfo(claims)
            myList=user_info['files_list_keys']
            # directory=user_info['directory_list_keys']
            # temp=directory[len(directory)-1]
            # count = temp.count('/')
            myList.append(file.filename)
            user_info.update({
                'files_list_keys':myList 
            })
            datastore_client.put(user_info)
            addFile(name, file)
            blob_metadata(name)
            flash("You have successfully added a file")
            blob_list = blobList(name, True)
            for i in blob_list:
                if i.name[len(i.name)-1]=='/':
                    session['location']=name
                if i.name[len(i.name)-1]!='/':
                    files.append(i.name)
            for prefix in blob_list.prefixes:
                directory_list.append(prefix)
                count = prefix.count('/')
            if count ==0:
                count=name.count('/')
        
        
        except ValueError as exc: 
            error_message = str(exc)

    return render_template('directoryPage.html', directory_list=directory_list, files=myList, user_info=user_info, count=count, path=session['location'])

@app.route('/download_file/<path:filename>', methods=['POST', 'GET']) 
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
            print('we are here')
            print(filename)
        except ValueError as exc: 
            error_message = str(exc)
    return Response(downloadBlob(filename), mimetype='application/octet-stream')

@app.route('/show_dublicates', methods=['POST', 'GET'])
def show_dublicate():
    files={}
    temp_list=[]
    unique_list = []
    myList=[]
    temp=[]
    location=session['location']

    blob_list = blobList(location, True)
    for i in blob_list:
        if i.name[len(i.name)-1]!='/':
            files.update({
                i.name:blob_metadata(i.name)
            })
            temp_list.append(blob_metadata(i.name))
   
    myList.append([item for item, count in collections.Counter(temp_list).items() if count > 1])
    #s = set( val for dic in lis for val in dic.values())

    # traverse for all elements
    for x in myList:
        if x not in unique_list:
            unique_list.append(x)
   
    for name, dict_ in files.items():
        for i in range(len(unique_list)):
            if dict_ == unique_list[i]:
                print(dict_)
                temp.append(name)
    
    print(temp)


    return redirect('/')


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
