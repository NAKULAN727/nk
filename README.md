# Smart Agriculture Project - MongoDB Integration

This project uses MongoDB for storing certain types of data like sensor readings, user logs, and session information.

## MongoDB Setup

1. Make sure MongoDB is installed on your system. If not, download and install it from [MongoDB's official website](https://www.mongodb.com/try/download/community).

2. Start the MongoDB service:
   - On Windows: Start the MongoDB service from Services or run `mongod` from the command line
   - On Linux/Mac: Run `sudo systemctl start mongod` or `brew services start mongodb-community`

3. The project is configured to connect to MongoDB at `mongodb://localhost:27017/` with database name `smart_agri_db`.

## Testing MongoDB Connection

You can test the MongoDB connection using the provided script:

```bash
python test_mongodb_connection.py
```

This script will:
1. Test direct connection to MongoDB using pymongo
2. Test the Django ORM integration with MongoDB
3. Create and retrieve test records in both cases

Alternatively, you can use the Django management command:

```bash
cd smart_agri2/smart_agri/agri_dashboard
python manage.py test_mongodb
```

## MongoDB Models

The following models are configured to use MongoDB:

- `UserLoginLog`: Stores user login information
- `AdminActivityLog`: Tracks admin activities
- `UserSessionInfo`: Stores detailed user session data
- `SensorData`: Stores IoT sensor readings

## Configuration

The MongoDB connection is configured in `settings.py` under the `DATABASES` dictionary:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'smart_agri.sqlite3',
    },
    'mongodb': {
        'ENGINE': 'djongo',
        'NAME': 'smart_agri_db',
        'CLIENT': {
            'host': 'mongodb://localhost:27017',
            'port': 27017,
            'username': '',
            'password': '',
            'authSource': 'admin',
        }
    }
}
```

To modify the connection settings, update the values in this configuration.

## Dependencies

The project requires the following packages for MongoDB integration:
- djongo>=1.3.6
- pymongo>=3.12.0,<4.0.0
- dnspython>=2.1.0

These are already included in the requirements.txt file.