from flask import Flask, render_template, request, redirect, session, flash, Response
from google.cloud import datastore, storage
import google.oauth2.id_token
from google.auth.transport import requests
import local_constants
import random


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


def createGeneralShares(email):
    entity_key = datastore_client.key('shared', email) 
    entity = datastore.Entity(key = entity_key)
    entity.update({
        'name':email, 
        'shared_files':[],
        'link': None
        
    })

    datastore_client.put(entity)

def retrieveGeneralShares(email):
    entity_key = datastore_client.key('shared', email) 
    entity = datastore_client.get(entity_key)

    return entity



def blobList(prefix, boolean):
    storage_client = storage.Client(project=local_constants.PROJECT_NAME)
    delimiter=None

    if boolean==True:
        delimiter='/'
        

    return storage_client.list_blobs(local_constants.PROJECT_STORAGE_BUCKET, prefix=prefix, delimiter=delimiter)

def add_blob_owner(blob_name, user_email):
    """Adds a user as an owner on the given blob."""
    # bucket_name = "your-bucket-name"
    # blob_name = "your-object-name"
    # user_email = "name@example.com"

    storage_client = storage.Client(project=local_constants.PROJECT_NAME)
    bucket = storage_client.bucket(local_constants.PROJECT_STORAGE_BUCKET)
    blob = bucket.blob(blob_name)

    # Reload fetches the current ACL from Cloud Storage.
    blob.acl.reload()

    # You can also use `group`, `domain`, `all_authenticated` and `all` to
    # grant access to different types of entities. You can also use
    # `grant_read` or `grant_write` to grant different roles.
    blob.acl.user(user_email).grant_read()
    blob.acl.save()

    print(
        "Added user {} as an owner on blob {} in bucket {}.".format(
            user_email, blob_name, bucket
        )
    )


def make_blob_public(blob_name):
    storage_client = storage.Client(project=local_constants.PROJECT_NAME)
    bucket = storage_client.bucket(local_constants.PROJECT_STORAGE_BUCKET)
    blob = bucket.blob(blob_name)

    blob.make_public()

    return blob.public_url
   

def delete_blob(blob_name):
    storage_client = storage.Client(project=local_constants.PROJECT_NAME)
    bucket = storage_client.bucket(local_constants.PROJECT_STORAGE_BUCKET)
    print(blob_name)
    blob = bucket.blob(blob_name)
    blob.delete()

def blob_metadata(blob_name):
    storage_client = storage.Client(project=local_constants.PROJECT_NAME)
    bucket = storage_client.bucket(local_constants.PROJECT_STORAGE_BUCKET)

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
    return blob.download_as_bytes()
 

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
    print(name)
    if id_token:
        try: 
            claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
            user_info = retrieveUserInfo(claims)
            blob_list = blobList(name, True)
            for i in blob_list:
                if i.name[len(i.name)-1]=='/':
                    session['location']=name
                if i.name[len(i.name)-1]!='/':
                    file_list.append(i.name)
            
        except ValueError as exc: 
            error_message = str(exc)
     
    return render_template('addFiles.html', path=name, data=file_list)

@app.route('/shareFile/<path:name>', methods=['POST', 'GET'])
def shareFileHandler(name):
    return render_template('shareFile.html', path=name)



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
        

    return render_template('indexPage.html', user_data=claims, error_message=error_message, user_info=user_info, root=session['email']+'/', directory_list=directory_list)

@app.route('/add_directory/<path:name>/', methods=['POST']) 
def addDirectoryHandler(name):
    id_token = request.cookies.get("token") 
    error_message = None
    claims = None
    times = None
    user_info = None
    directory=[]
    directory_list=[]
    files=[]
    count=0
    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)

            directory_name = request.form['Fname']
            if directory_name == '' or directory_name[len(directory_name) - 1] != '/':
                flash('A directory should have a directory name followed by a /')
                return render_template('addDirectory.html')
            blob_list = blobList(name, True) 
            for i in blob_list:
                if i.name[len(i.name)-1]=='/':
                    session['location']=name
                if i.name[len(i.name)-1]!='/':
                    files.append(i.name)

            name=name+'/'

            directory_name = name+directory_name
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
            count = directory_name.count('/')
           
            flash('You have successfully created a new directory')
            session['location']=directory_name

            blob_list = blobList(name, True)
            for i in blob_list:
                for prefix in blob_list.prefixes:
                    directory_list.append(prefix)
                    count = prefix.count('/')
                if count ==0:
                    count=2+name.count('/')
            

        except ValueError as exc: 
            error_message = str(exc)

    return render_template('directoryPage.html', directory_list=directory_list, files=files, user_info=user_info, count=count)

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
                count=1+name.count('/')   
             
           
        except ValueError as exc: 
            error_message = str(exc)
    
    return render_template('directoryPage.html', directory_list=directory_list, files=files, user_info=user_info, count=count, path=name)

@app.route('/way/<path:vn>', methods=['POST', 'GET'])
def changeDirectory(vn):
    id_token = request.cookies.get("token") 
    error_message = None
    claims = None
    name = session['location']
    user_info = None
    directory_list=[]
    files=[]
    myList=[]
    count=0
    prefix=None

    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
            user_info = retrieveUserInfo(claims)
            myList=''
            count = vn.count('/')
            temp=vn.split('/')
            if request.form.get('path')!='../':
                flash('You hava use a wrong Symbol')
                return redirect('/')
            for i in range(count-1):
                myList=myList+temp[i]+"/"

            blob_list = blobList(myList, True)
            for i in blob_list:
                if i.name[len(i.name)-1]!='/':
                    files.append(i.name)
            for prefix in blob_list.prefixes:
                directory_list.append(prefix) 
            count=count
           

        except ValueError as exc: 
            error_message = str(exc)

    
    return render_template('directoryPage.html', directory_list=directory_list, files=files, user_info=user_info, count=count, path=myList)


@app.route('/delete/<path:name>', methods=['POST', 'GET'])
def delete(name):

    id_token = request.cookies.get("token") 
    error_message = None
    claims = None
    name = name
    user_info = None
    directory_list=[]
    files=[]
    temp1=[]
    temp2=[]
    temp_name=None

    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
            user_info = retrieveUserInfo(claims)
           
            temp_name=name
            temp_list=user_info['files_list_keys']
            for i in range(len(temp_list)):
                if name.find(temp_list[i])>=0:
                    name=temp_list[i]
            
            if name[len(name)-1]=='/':
                name=name.rsplit('/', 1)[0]+'/'
                blob_list = blobList(name, None)
                for i in blob_list:
                    if i.name[len(i.name)-1]=='/' and i.name != name:
                        print(i.name)
                        directory_list.append(i.name)
                        session['location']=name
                
            blob_list = blobList(name, True)
            for i in blob_list:
                if i.name[len(i.name)-1]=='/' and i.name != name:
                    print(i.name)
                    directory_list.append(i.name)
                    session['location']=name
        
                if i.name[len(i.name)-1]!='/':
                    files.append(i.name)
                   
            
            if len(files)!=0:
                flash('This directory still has files so cannot be deleted')
                return render_template('directoryPage.html', directory_list=directory_list)
            
            if len(directory_list)!=0:
                flash('This directory has content so cannot be deleted')
                return render_template('directoryPage.html', directory_list=directory_list)
            
            mylist = user_info['directory_list_keys']
            
            for n in range(len(mylist)):
                if not name.find(mylist[n])>=0:
                    temp1.append(mylist[n])
            
            
            mylist=user_info['files_list_keys']
            for n in range(len(mylist)):
                if not name.find(mylist[n])>=0:
                    temp2.append(mylist[n])
                   
            user_info.update({
                'directory_list_keys':temp1,
                'files_list_keys':temp2
            })

            datastore_client.put(user_info)

            delete_blob(temp_name)
            
            directory_list=[]
            blob_list = blobList(session['location'], None)
            for i in blob_list:
                if i.name[len(i.name)-1]=='/' and i.name != name:
                    directory_list.append(i)
                    session['location']=name
            
            flash('Delete Successful')
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
            else:
                n = random.randint(0,22)
                temp1=file.filename
                temp3=temp1.split('.').pop()
                temp2=temp1[0 : temp1.rfind('.')]
                file.filename= temp2 + ""+str(n) + "."+temp3
            
            user_info = retrieveUserInfo(claims)
            myList=user_info['files_list_keys']
           
            myList.append(file.filename)
            user_info.update({
                'files_list_keys':myList 
            })
            datastore_client.put(user_info)
            addFile(name, file)
    
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
                count=2+name.count('/')
        
        except ValueError as exc: 
            error_message = str(exc)

    return render_template('directoryPage.html', directory_list=directory_list, files=files, user_info=user_info, count=count, path=session['location'])

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

        except ValueError as exc: 
            error_message = str(exc)
    return Response(downloadBlob(filename), mimetype='application/octet-stream')

@app.route('/show_dublicates', methods=['POST', 'GET'])
def show_dublicate():
    id_token = request.cookies.get("token") 
    files_list={}
    files=[]
    count=0
    temp_list=[]
    unique_list = []
    myList=[]
    temp=[]
    temp_list_final=[]
    location=session['location']
    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
            user_info = retrieveUserInfo(claims)
            blob_list = blobList(location, True)
            for i in blob_list:
                if i.name[len(i.name)-1]!='/':
                    files_list.update({
                        i.name:blob_metadata(i.name)
                    })
                    temp_list.append(blob_metadata(i.name))
            
            for i in range(0, len(temp_list)):
                for j in range(i+1, len(temp_list)):
                    if temp_list[i]== temp_list[j]:
                        count=count+1
                        temp_list_final.append(temp_list[i]) 
            if count==0:
                flash('There are no Dublicates')
                return render_template('showDublicates.html', user_info=user_info, path=session['location'])

            for name, dict_ in files_list.items():
                if dict_ in temp_list_final:
                    temp.append(name)
            
        except ValueError as exc: 
            error_message = str(exc)

    return render_template('showDublicates.html', files=temp, user_info=user_info, path=session['location'])

@app.route('/allDublicates', methods=['POST', 'GET'])
def show_all_dublicate():
    id_token = request.cookies.get("token") 
    files_list={}
    files=[]
    count=0
    temp_list=[]
    temp_list_final=[]
    unique_list = []
    mylist=[]
    temp=[]
    location=session['location']
    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
            user_info = retrieveUserInfo(claims)
            name=user_info['email']+'/'
            
            blob_list = blobList(name, False)
            for i in blob_list:
                if i.name[len(i.name)-1]!='/':
                    mylist.append(i.name)

            for i in range(len(mylist)):
                files_list.update({
                    mylist[i]:blob_metadata(mylist[i])
                })
                temp_list.append(blob_metadata(mylist[i]))

            for i in range(0, len(temp_list)):
                for j in range(i+1, len(temp_list)):
                    if temp_list[i]== temp_list[j]:
                        count=count+1
                        temp_list_final.append(temp_list[i])  
            if count==0:
                flash('There are no Dublicates')
                return render_template('showDublicates.html', user_info=user_info, path=session['location'])

            for name, dict_ in files_list.items():
                if dict_ in temp_list_final:
                    temp.append(name)
            
        except ValueError as exc: 
            error_message = str(exc)

    return render_template('showDublicates.html', files=temp, user_info=user_info, path=session['location'])

@app.route('/share_file/<path:name>', methods=['POST', 'GET'])
def share_file_handler(name):
    id_token = request.cookies.get("token") 
    temp=name
    mylist=[]
    email=request.form['file_name']
    name=name.split('/')[-1]
    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
            user_info = retrieveGeneralShares(email) 
            if user_info == None:
                createGeneralShares(email)
            user_info = retrieveGeneralShares(email)
            mylist=user_info['shared_files']
            mylist.append(name)
            
            temp_link=make_blob_public(temp)
            print(temp_link)
            user_info.update({
                'shared_files': mylist,
                'SharerName': claims['email'],
                'link':temp_link
            })

            datastore_client.put(user_info) 

            flash('You have successfully shared the file with {}'.format(claims['email']))
        except ValueError as exc: 
            error_message = str(exc)
    
        
    return redirect('/')

@app.route('/showSharedFiles', methods=['POST', 'GET'])
def show_shared_file_handler():
    mylist=[]
    user_info=None
    link=None
    id_token = request.cookies.get("token") 
    sharer=None
    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
            email=claims['email']
            user_info = retrieveGeneralShares(email)

            if user_info==None:
                flash('You have no shared files')
                return redirect('/')

            mylist=user_info['shared_files']
            link=user_info['link']
            if mylist ==None or len(mylist)==0:
                flash('You have no shared files')
                

        except ValueError as exc: 
            error_message = str(exc)

    return render_template('showSharedFiles.html', files=mylist, user_info=user_info, link=link)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
