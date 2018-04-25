# SimpleLMS
Simple Library Managment System. 

## Usage
To use this program you need to have *python3*, *pymongo* and *flask* installed on your PC.
### How to start?
Type ```python3 main.py``` in the command line. Then you will be offered to log in. Enter ```admin``` as a login and ```p``` as a password to be logged in as the admin user. It will give you permissions to use all feature. Or you can type your own login and password if you are already registered. But remember that every user has a type which restricts the allowed features. For example, a librarian can insert, delete, modify documents and register new users but can't search for logs. Only admin can see the logs.
### How to interact with this LMS?
After you successfully log in you will see the list of all documents in the center of the page, the list of allowed features on the left side of this page and the search field on the top of this page.

### What features can I use as a user?
A user can use the search field on the main page to find a document on move to a document page. Then a user can see the information about the document and send a checkout or return request if it is possible. Also, a user can use "My notifications" and "Log out" button on the main page.
### What additional features can I use as a librarian?
A librarian can approve or decline requests. A librarian can confirm registration for a user. A librarian can see all notifications an all documents with overdue. Some librarians can add, delete and modify documents. It depends on the level of privileges of a librarian.
### What additional features can I use as an admin?
The admin can manage librarians. The admin can change the level of privileges of librarians. Also, the admin can see all logs which the system produces.

## Testing
This LMS has command line interface mode which is used for testing. File ```test.in``` contains the commands for testing. After executing these commands you should see the string like in file ```test.out```. To test these automatically you can run ```cat test.in | python3 main.py command_line_mode_on``` in terminal. You should compare output strings and correct answers (in file ```test.out```) manually because the order of pairs key-value in dictionaries can differ for different python interpretations.
Also, this feature is used to set the state of the LMS before execution a test case in web interface mode. For example, a file ```initial_state``` contains the list of commands that after execution undo all changes and return the current state of this LMS to the initial. It is useful for manually testing.

## Documentation
All documentation is stored in the ```documentation``` folder. Open ```annotated.html``` to see the documentation for source code. It is extracted from comments by *Doxygen*. It has documentation for all modules, classes, and functions. It describes the inheritance, the encapsulation and how they interact with each other.
The description of the internal structure of objects in the database and object templates can be found in ```slms_structure.pptx``` presentation. Also, it has screenshots with examples.

## Contribution 
This project has 2 contributes. Rishat Rizvanov who implemented the web interface (a module responsible for front-end) and database and Sergey Bogdanik who implemented the core (a module responsible for back-end) and command line interface.


