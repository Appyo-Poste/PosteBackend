Poste Backend Services
---

# Description

This repository contains the Poste backend server application / API as a Python + Django project.

---

# Installation & Usage - Docker

1. Clone this repository:

`git clone git@github.com:Appyo-Poste/PosteBackend.git`

2. Move into repository directory:

`cd PosteBackend`

3. Install and run Docker for your system: 

>https://www.docker.com/get-started/

4. Run the application via Docker using Docker Compose. Optional Make target provided for convenience.

`docker compose up --build -d` or `make up` 

5. The application will be running locally:
 
>http://localhost

6. A default superuser account will be created with the following credentials. Use this to login:

```
username: admin@email.com
password: admin1234
```

---

## Stopping the Application - Docker Containers

1. To stop the application, run the following command. Optional Make command provided for convenience.

`docker compose down --remove-orphans` or `make down`

2. OPTIONAL: To remove all data and start fresh, run the following command. Optional Make command provided for convenience.

`docker compose down --remove-orphans --volumes` or `make clean`

NOTE: This will delete all data, including the database, and will remove all folders, posts, and users. This is useful
for development, but be mindful of what this means for you.

# Installation & Usage -- Development Server (No Docker, not recommended)

You can also run this Project locally via Django's built-in development server. This is not recommended for production,
but is useful for development and testing. This will use an SQLite database rather than a Postgres database.

Please note that any changes made to one environment (Docker or local) will not be reflected in the other environment.

1. Clone this repository:
```
git clone git@github.com:Appyo-Poste/PosteBackend.git`
```

2. Move into repository directory:
```
cd PosteBackend
```

3. Create virtual environment
```
`python -m venv venv`   
```

4. Activate virtual environment

| OS | Command |
| --- | --- |
| Windows | `./venv/Scripts/activate` |
| Linux/Mac | `source venv/bin/activate` |

5. Install dependencies
```
pip install -r requirements.txt
```

6. Run the application via Django's built-in development server.

```
python manage.py runserver
```

7. The application will be running locally:
>http://localhost:8000

---

## Running tests

To run the tests, first ensure you have activated the virtual environment, as shown in #4 above. Then, run:

```
python manage.py test
```

Django automatically identifies and runs tests with this command. To ensure written tests are properly identified, 
name them accordingly (e.g. `test<name>.py`) and place them in the `PosteBackend/tests/` directory.

Alternatively, you may shell into the Docker container and run the tests from there. To do so:

1. Shell into the Docker container:
```
docker exec -it postebackend-poste-1 bash
```

2. Run the tests:
```
python manage.py test
```

---
# SSL and Certs

In order to use HTTPS, we need to generate a certificate and key. 

To generate a self-signed certificate and key, run the following command:
```
openssl req -x509 -newkey rsa:4096 -keyout poste.key -out poste.crt -days 365 -nodes
```

This will generate a certificate and key, which can be used to enable HTTPS. These files should not be committed to
version control, and should be kept secret. As a result, they are not included in this repository.
They will also need to be used in the frontend application, which is not included in this repository.

As a result, this repository should not be committed to the main branch until we are ready to solely use HTTPS.

---

# Models and Migrations

## Models

In Django, a **model** is a Python class that inherits from django.db.models.Model, and is essentially a blueprint 
that defines the fields and behaviors of the data you will store. This allows us to interact with our backing data using
**objects** instead of writing raw SQL queries.

A Django model corresponds to a database table, where the class attributes define the table columns, and instances of 
the class (or objects) represent individual rows in the table. So, when you create an object (an instance of a model), 
you are filling a row in the corresponding database table with data, according to the structure (fields) defined in the 
model. This connection between objects, models, and tables enables Django to provide a high-level, Pythonic interface to 
interact with the database, abstracting away the SQL complexity.

## Migrations

Migrations are important to ensure that the database schema matches the current state of the project models. Whenever 
models are modified, Django needs a way to create a schema change in the database, to make sure the stored data adheres 
to the new structure. That's where migrations come into play.

## When to Create a Migration

You should create a new migration when you have:

- Created a new model. 
- Made changes to an existing model such as adding, deleting, or altering fields.

## When to Apply Migrations

Apply migrations when you need to:
- Reflect the changes made in your models into your database schema.
- Apply changes made in other developers' migrations if you are working in a team environment.

---

### Create Migrations

After modifying your models (including adding or deleting a model), create a new migration using:

```
python manage.py makemigrations
```

This command creates new migration files based on the changes detected to your models.

### Apply Migrations

After creating migrations (or when pulling changes from other developers), the changes have to be applied to your local
database. You will also need to do this if you delete and recreate your local database.

To apply the migrations and update your database schema, run:

```
python manage.py migrate
```

### Rolling Back Migrations

To undo migrations, you can use the migrate command followed by the name of the app and the migration you want to roll 
back to:

```
python manage.py migrate [app_name] [migration_name]
```

It is important to note that a Django project consists of one or more 'apps'. In our case, we have a single app called
'PosteAPI' and the project itself is called 'PosteBackend'. The app name is the name of the directory containing the
app's code, and the project name is the name of the directory containing the project's code (which contains the app).

### Show Migration Status

To show the migrations and their status (applied or not), use:

```
python manage.py showmigrations
```    

### Deleting and Recreating Migrations

There might be scenarios where you want to delete and recreate migrations, especially during development. This is often 
done when you want to clean up your migration history and start afresh.

- To remove migrations, you can simply delete the migration files from the migrations/ directory in your app.
- Clear the migration history from the database. Currently, we are using Django’s default database (SQLite), so we can 
  simply delete the `db.sqlite3` file.
- Then, create a new initial migration using makemigrations and apply it using migrate.

### Key Considerations

- Do not delete migrations once they are applied and pushed to a shared or production environment. Any deletion or 
manual modification in the migrations or their order can lead to inconsistent database states amongst developers and 
deployments.
- Always pull the latest codebase and apply other developers’ migrations before creating your own to minimize conflicts.
- Resolve Merge Conflicts Carefully: If two developers make conflicting model changes, then it can create a conflict in 
migrations. You must resolve this conflict manually with utmost care.
- Be Cautious with Data Migrations: If you’re dealing with data migrations (modifying existing data in the database), 
ensure to have data backup and thoroughly test the migration before applying it.

---

# Django Project Structure - Model-View-Template (MVT)

![mvt.jpg](res%2Fmvt.jpg)

## Models
Models play a crucial role in our Django project, acting as the definitive source of information about our data. Models
are defined in an app's `models.py` file, and are used to create database tables and to query the database.
Because our project has one app, `PosteAPI`, the models are defined in `PosteAPI/models.py`.

Currently, our project has the following models:
- User: Represents a user of the Poste application.
- Post: Represents a post made by a user.
- Folder: Represents a folder created by a user.
- FolderPermission: Represents a permission granted to a user for a folder.

`models.py` also contains helper methods used by the classes; for instance, we can write methods to retrieve all 
folders or posts a user has access to, to create a new post or folder for a user, etc.

## Views
In a Django project, views act as intermediaries between models and templates, receiving HTTP requests from users, 
retrieving data from models, and sending data back to templates to render pages. In our case, however, we are currently
only using Django to create an API, so we do not have any templates. Instead, our views return serialized data in JSON
format. Regardless, Views handle the "logic" of our application. They request information from the model and pass it on. 
If you are familiar with the common MVC (Model-View-Controller) pattern, Django views are the controllers. (Note that
Django does not strictly follow the MVC pattern, instead using a similar pattern called MVT, or Model-View-Template.) In
this way, views manage the communication between the user interface and the data.

Views are defined in an app's `views.py` file, and are used to define the behavior of the API endpoints. Because our
project has one app, `PosteAPI`, the views are defined in `PosteAPI/views.py`. Note that URLs are mapped to views in
`PosteAPI/urls.py` -- as a result, we can have different URLs map to the same view (using different HTTP methods, for
instance) or have different URLs map to different views.

## URLs
URLs are defined in an app's `urls.py` file, and are used to map URLs to views. Because our project has one app,
`PosteAPI`, the URLs are defined in `PosteAPI/urls.py`. This is how we determine which view (logic) to use for a given 
URL (endpoint).


## Serializers
Serializers are used to convert data from models into JSON format, and vice versa. They are defined in an app's
`serializers.py` file, and are used to serialize and deserialize data. Because our project has one app, `PosteAPI`, the
serializers are defined in `PosteAPI/serializers.py`. We can use serializers to validate incoming data, and to convert
data from models / DB into JSON format to send back as the API response.

---

## API Information

![api.png](res%2Fapi.png)

Our project is configured to use Swagger to document the API. Swagger is a tool that allows us to document our API in a
standardized way, and provides a UI to interact with the API. To view the Swagger UI, run the server and navigate to
`http://localhost:8000/swagger/`. This will show the Swagger UI, which contains information about the API endpoints,
including the URL, HTTP method, parameters, and response. You can also use the Swagger UI to test the API endpoints.

Note: As you are building the API, you will need to update the Swagger documentation to reflect the changes you make.
This can be done by adding the `swagger_auto_schema` decorator to the view, and specifying the parameters and response
schema. See the Swagger documentation for more information: https://drf-yasg.readthedocs.io/en/stable/custom_spec.html






