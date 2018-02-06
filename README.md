## SLMS
Simple Library Managment System. 

## Usage
To use this programm you need to have ```python3``` installed on your PC.
### How to start?
In order to run python file type on the command line following: ```python3 main.py```  Then you will be offered to log in. Leave login and password empty to log in as the admin user. It will give you permissions to run all command. Or you can type your own login and password if you are already registered. But remember that every user has a type which restricts accessible commands. For example, a librarian can insert, delete, modify documents and register new users but can't search for documents. 
### How to interact with this LMS?
After you successfully logged in you will see ```>>>``` symbols. It is an invitation to write commands. Every command has following structure: ```command_name target --attribute value``` where:
1. Command name: one word from the list of commands 
2. Target: one word which is necessary for some commands 
3. Attributes: dictionary where a key is attribute name following after symbols -- and value is the string following after attribute name. There can be more than one attributes 
### What command can I write?
1. Login:
    - no target and attributes
    - asks to write your login and password
    - if you leave these fields empty you will be logged in as an admin user
    - prints ```Success``` if you logged in successfully and ```Fail``` otherwise
2. Exit: 
    - no target and attributes
    - immediately halts the program
3. Register:
    - adds a new user
    - target is a type of the user which will be added
    - attributes are the attributes of the user which will be added
4. Insert:
    - adds a new document
    - target is a type of the document which will be added
    - attributes are the attributes of the document which will be added
5. Delete:
    - delete an item (user or document)
    - target is the id of the item which will be deleted
6. Modify:
    - modifies an item
    - target is the id of the item which will be modified
    - attributes are the attributes of the item which will be replaced
7. Find:
    - searches for items
    - target is a type of items which you are searching for. Leave it empty in order to search all types
    - attributes are the attributes of items which must match to count the item as found. Leave it empty to search for all items of current type
    - returns the list of found items
8. Checkout:
	- checks a document out
	- target is the id of the document which will be checked out
9. Return:
	- returns a document in library
	- may return the fine size when the document is overdue
10. Copy:
	- creates a opy of a document
	- target is the id of the document which will be copied
11. Check:
	- if target is not specified prints the list of all copies in the library and checked out
	- if target is the id of a document them it prints the list of all copies of the document
12. Drop:
	- deletes all records from datebase even current user
	- after executing this command you will become admin user

## Testing
File ```test.in``` contains the commands for testing. After executing these commands you should see the string like in file ```test.out```. To test these automatically you can run ```rm db.json; cat test.in | python3 main.py command_line_mode_on``` in terminal. You should compare output strings and correct answers (in file ```test.out```) manually because the order of pairs key-value in dictionaries can differ for different python interpretations. 
Tests from the fist delivery are in the ```tests``` directory. You can check them by executing ```cat tc<number of the test case>.in | python3 main.py command_line_mode_on``` in commad line. The correct answers are in ```*.out``` files.

## Documentation
You can see the documentation when you open source code and read docs below every function, class or variable declaration. 
