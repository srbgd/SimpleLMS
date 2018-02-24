## SLMS
Simple Library Managment System. 

## Usage
To use this program you need to have ```python3``` installed on your PC.
### Start
Create python file ```config.py``` with following code:
```
import os
class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'YOUR_SECRET_KEY'

mongodb_link = "YOUR_MONGODB_LINK"
```

Type: ```pip install -r requirements.txt```
Then ```python interface.py```


Now it runs on your localhost: ```http://localhost:5000/```

Librarian may add new books and change any users data. Student and Faculty may check_out available books and change thier own data.
