```
├── avr - the main application module
│   ├── forms.py - conatains all the different forms the site uses
│   ├── __init__.py - contains initialization code for the package
│   ├── models.py - contains all the database models used by the site
│   ├── routes.py - contains all the different URLs that the application implements
│   ├── static - contains all the static files of the site  
│   │   ├── css - contains style sheets the site uses 
│   │   ├── fonts - contains additional fonts the site uses 
│   │   ├── images
│   │   │   └── profile - contains all the students profile pictures (make sure default.png is there which is the default profile picture )  
│   │   │   └── projects - contains all the project images 
│   │   │   └── proposed_projects - contains all the proposed project images
│   │   └── js - contains javascript files/libraries the site uses  
│   └── templates - contains all the HTML templates of the site (these templates are rendered using the Jinja template library that flask uses) 
└── run.py

```
