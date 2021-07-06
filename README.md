# Dropbox
Building a Room Scheduler
First before we can start with anything we will need to create a python virtual environment as we will need to install things into it without messing with the local python environment. The instructions you see here are taken from: 
https://cloud.google.com/appengine/docs/standard/python3/quickstart
There are a number of things that should be installed and setup before you attempt to run any of the programs here. 
Working Environment: 
1.	A decent syntax highlighting text editor with support for: 
•	Python
•	HTML 
•	CSS 
•	JS, 
•	Yaml,
•	 JSON  
•	Git integration. 

2.	An installation of python 3.8 that is accessible from anywhere on the command line. i.e. your PATH variable has been modified to find it.

3.	 An installation of google app engine with the app-engine-python and app-engine-python- extras installed that is also accessible from anywhere on the command line. i.e. your PATH variable has been modified to find it 
Once you have all of the above installed and setup then you are ready to go with building Google App Engine applications 

Specifically the Linux/OSX version. There are Windows versions of these as well on the same page. First open a command line and navigate to the directory where you will write the code for these examples. 
When you get there run the following command: 
python3 -m venv env 
This will create a directory called “env” that contains a python virtual environment that is separate from the regular python environment. 

After this we will need to run the following command 
source env/bin/activate
Application Development Steps:
1.	create a new directory for the application.

2.	inside that directory below is the directory and file structure 
app.yaml 
main.py 
local_constants.py
requirements.txt 
static/ 
◦ script.js 
◦ style.css 
templates/ 
◦ main.html 
3.	inside that directory create a file called requirements.txt and add the following text into it   
 Flask==1.1.2 
  google-cloud-datastore==1.15.0
  google-auth==1.21.2
  requests==2.24.0

The requirements.txt file is there to tell Google App Engine what additional libraries are needed in order to run your application. In this case we are stating that we need the Flask web framework and specifically version 1.1.2 in order to run our application. If we are developing the application locally we will need to install the requirements by hand which will be covered in a later step. Any additional libraries you will need must be specified in this file. 

Note that it is not possible to add any Python library of your choosing to this as Google App Engine runs a restricted version of Python3. Google App Engine may also have a deny-list of libraries that are not permitted to be installed as well and your chosen library(ies) may appear on that list. 




4.	In the file called ‘app.yaml’, you find the following code. 
   runtime: python38

 handlers:
- url : /static
  static_dir : static

- url : /.*
  script : auto


5.	In the file called ‘main.py’ and add the python code files 

6.	add a file called local_constants.py and add the following code to it 
PROJECT_NAME='<your project name goes here>’ 
PROJECT_STORAGE_BUCKET='<your storage bucket goes here>' 

These constants are refactored out to their own file to make them easy to reuse and also to prevent us from having to copy and paste them every time we need to use these constants. You can fill in the appropriate values here by finding the same values you have already defined in app-setup.js If you want to have a look at the storage bucket contents go to 
http://console.cloud.google.com/ 
and click on storage to see your buckets 


7.	open a console and navigate to the project directory. Make sure you have created your environment and sourced it as shown above and run the following command 
                pip install -r requirements.txt

8.	Before you go to run this project you will need the JSON file nearby to access the datastore. Before you run your application in your command line you will need to set the session variable GOOGLE_APPLICATION_CREDENTIALS with the location of this JSON file. In my case I have the JSON file above the directory this project runs in so in Linux I would run the following command to set that session variable 

export GOOGLE_APPLICATION_CREDENTIALS=”../app-engine-3-testing.json” 

where app-engine-3-testing.json is my JSON file. After this run the project as normal and every time you visit the root page now a new visit time will be added and the list will be dynamically updated. 

9.	run your application by executing the following command:
                 python main.py      

This will start your Flask application and if you navigate to localhost:8080 in your web browser you will see the message “Hello world” in plain text if everything is working correctly. 



Data Structure

-Description entity structures used and explain the data they hold
    (Datastore)
• User Info: This entity is created for every user that logs into the application. This holds two arrays, one for the directory and another for the files. In addition, it also holds the email address of the user. 
• Shared: This entity is created when a user what to send a file to another user. It holds the receiver's email and all the user's shared files. 

-Storage Structure:
  (Storage Bucket)
• When a user logs in for the first time, a default root directory is created for the user. Afterward, every other directory created by the user will be a subdirectory of the user's root directory. 

-General Data structures(ds) used:
•	list: This is a very common ds used within the application; it is mainly used to hold the file and directory entity. 
•	Dictionary: This is used within the application; it was used when file hashing within the show duplicate method.

Application Database/storage bucket Design 
  This application uses both the datastore and storage bucket—the storage bucket help to store all the files and directories for different users. A default directory is created for first-time users, and all other sub-directories and files are stored within that directory. On the other hand, the datastore helps store user entities with their respective directories and file names. A user entity is created uniquely using the user's email; this serves as the key in the datastore, while the shared entity is created uniquely using the receiver's email. Also, this is used as the key in the datastore. 











PROJECT DOCUMENTATION FOR DROPBOX APPLICATION

Helper Methods
1. To create a User: This method takes in claims to create an entity, using the user's email as a key in the datastore. This process returns an entity key, which is used to store the entity in the datastore.
2. To retrieve User Details: This method helps to return the user Entity. 
3. To create another entity for sharing: This method takes an email to create an entity, using the user's email as a key in the datastore. This process returns an entity key, which is used to store the entity in the datastore.
4. To retrieve the entity for sharing: This method helps to return the user Entity.
5. To create a Directory: This method takes in claims and the directory's name to be created, using the directory name as a key in the datastore. This process returns an entity key, which is used to store the entity in the datastore.
6. To retrieve a Directory: This method helps to return the Directory entity.
7. List of objects in the datastore: This method takes in a prefix with a boolean; the prefix is passed as one of the variables needed to retrieve all the objects in the storage. In addition to that, the Boolean is also among the parameters, as it serves as a delimiter. The Boolean value 'true' set the delimiter to the appropriate variable while false set the delimiter to none. It returns a list to the caller methods. 
8. To make a file sharable: This method takes in an object, retrieves the object from the datastore, and finally makes it accessible. 
9. To delete an Object: This method takes the object's name to be deleted, retrieves the object from the storage bucket using the object name, and then deletes the object.
10. To add a Directory to storage: This method takes in the directory's name to be added. Then using the blob and bucket classes, we add the directory to the storage.
11. To add a File to storage: This method takes in the name of the file to be added and its path. Then using the blob and bucket classes, we add the file to the storage.
12. To download a file: This method takes in the file name, using the filename, the file is fetched from the storage with the help of the blob and bucket classes, and it is returned to the caller in bytes for download. 

Page Return Handler methods
1. addDirectoryPageHandler: This method returns the addDirectory.html page 
2. dublicatePageHandler: This method returns the showDublicates.html page 
3. addFilePageHandler: This method takes in a path variable name and makes a call to the storage to retrieve all existing files. Then, it returns the addFile.html page along with the JSON object for all the retrieved files. 
4. ShareFileHandler: This method takes in a path variable name and returns the shareFiles.html page alongside the pathname. 




Main Methods
1. root: Firstly, we retrieve the user token and store it in a variable. Then, we check if the token is present; afterward, we get the claim and pass it into another method. This method will help retrieve the user's details if available or create it if it is not available.  We create two session variables for the user's email and path. Afterward, we check if the user already has a default directory created. If so, then we retrieve all the user's sub-directories and files, and If none exist, we create a default directory for the user. Finally, we return the indexPage.html along with other necessary variables. 

2. addDirectoryHandler: This method takes in the pathname variable. Then, it retrieves the user token and stores it in a variable. Then, we check if the token is present; if so, we retrieve the claims and pass them into another method. This method will help retrieve the user's details if available or create it if it is not available. Afterward, we get the name of the directory to be stored using the request method. Then, we check if the directory name is an empty string or does not end with a forward slash. We flash an error message to the user, and we return the addDirectory.html page. 
Using the path variable and the list object method, we get all the files that are in that directory. In addition, we perform another error check; we check if the directory name already exists with storage. If so, we flash an error message back to the user and return the addDirectory.html page. Finally, if we can reach this point, it means that the directory name is correct, and we store it in datastore and storage. We flash a success message to the user and return the directory.html page along with other necessary variables. 

3. show Directory: This method takes in the pathname variable. Then, it retrieves the user token and stores it in a variable. Then, we check if the token is present; if so, we retrieve the claims and pass them into another method. This method will help retrieve the user's details if available or create it if it is not available. Using the file path, we retrieve all the directories and files within the current directory. Also, we have a count variable to help determine if we are in the root directory or not.  We return the directory.html page along with other necessary variables. 

4. change Directory: This method helps us to move up a directory. It takes in the pathname variable. Then, it retrieves the user token and stores it in a variable. Then, we check if the token is present; if so, we retrieve the claims and pass them into another method. This method will help retrieve the user's details if available or create it if it is not available. We check to see if the path annotation entered by the user is correct. If it is not correct, then we flash an error message to the user. If it is correct, then we move up one directory, get all the files and sub-directory in that directory, and return to files, directory, path and count, and directoryPage.html.

5. Delete: This method handles deleting a directory or file; it takes in a pathname variable. Then, it retrieves the user token and stores it in a variable. Then, we check if the token is present; if so, we retrieve the claims and pass them into another method. This method will help retrieve the user's details if available or create it if it is not available. Using the path, we retrieve all the files and directories within the current directory. To delete a directory, we check if that directory contains sub-directories or files. If so, we flash a message to the user. If we get to this point, we delete it from both the datastore and storage bucket and return a success message.  

6. To upload File: This method takes in the pathname variable. Then, it retrieves the user token and stores it in a variable. Then, we check if the token is present; if so, we retrieve the claims and pass them into another method. This method will help retrieve the user's details if available or create it if it is not available. 
-Firstly, we get the name of the file using a request method. 
-Next, we check if the filename is an empty string, we flash an error message to the user and redirect the user to the root. 
-Afterwards, we check if this filename already exists with the datastore and storage. Hence, append a string 'new' to the filename, else we attach a random two-digit number to the filename. 
Finally, we save the filename in the datastore and file object into the storage bucket. We flash a success message to the user and return the directoryPage.html along with other variables. 

7. To download File: This method takes in a path containing the file to be download. In the Response method and another helper method, the file is downloaded.

8. show duplicate files within a directory: This method retrieves the path from the session variable, representing the current directory. Then we iterate through all the files in the current directory and retrieve their hashing. Finally, we return all files that have the same hash. 

9. show all duplicate files in the application:  In this method, we retrieve the list of all files within the application, then we iterate through to get all their hashes. We compare all the hashes received, and we return all the files that have similar hash numbers. 

10. share a file: This method in the file's name to be shared, then using the request method, and we retrieve the receiver's email. Using the helper method, we create an entity for the receiver with their shared file. In addition, we also make that file access to the receiver using one of the helper methods so that it is available read-only copy for download when the receiver logs in. 

11.show all shared files: This method returns all the files that have been shared with a user. 




