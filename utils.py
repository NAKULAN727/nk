from pymongo import MongoClient
from django.conf import settings
import logging
from bson.objectid import ObjectId
from datetime import datetime
from django.utils import timezone

logger = logging.getLogger(__name__)

def check_mongodb_connection():
    """
    Checks if MongoDB is accessible and returns connection status
    
    Returns:
        tuple: (is_connected, message)
    """
    try:
        # Get database settings
        db_settings = settings.DATABASES['default']
        host = db_settings['CLIENT']['host']
        
        # Connect to MongoDB
        client = MongoClient(host, serverSelectionTimeoutMS=2000)
        
        # Test connection
        server_info = client.server_info()
        version = server_info.get('version', 'unknown')
        
        return True, f"Connected to MongoDB {version}"
    except Exception as e:
        logger.error(f"MongoDB connection error: {str(e)}")
        return False, f"Failed to connect to MongoDB: {str(e)}"

def get_mongodb_client():
    """
    Returns a MongoDB client instance
    
    Returns:
        MongoClient: MongoDB client instance
    """
    db_settings = settings.DATABASES['default']
    host = db_settings['CLIENT']['host']
    return MongoClient(host, serverSelectionTimeoutMS=5000)

def insert(collection_name, document, database_name=None):
    """
    Inserts a document into the specified MongoDB collection
    
    Args:
        collection_name (str): Name of the collection
        document (dict): Document to insert
        database_name (str, optional): Name of the database. Defaults to settings.DATABASES['default']['NAME'].
    
    Returns:
        tuple: (success, result_or_error)
            - success (bool): True if insertion was successful, False otherwise
            - result_or_error: ObjectId of inserted document if successful, error message otherwise
    """
    try:
        # Get MongoDB client
        client = get_mongodb_client()
        
        # Get database name from settings if not provided
        if not database_name:
            database_name = settings.DATABASES['default']['NAME']
        
        # Get database and collection
        db = client[database_name]
        collection = db[collection_name]
        
        # Insert document
        result = collection.insert_one(document)
        
        # Return inserted ID
        return True, result.inserted_id
    
    except Exception as e:
        error_msg = f"Error inserting document into {collection_name}: {str(e)}"
        logger.error(error_msg)
        return False, error_msg

def insert_many(collection_name, documents, database_name=None, ordered=True):
    """
    Inserts multiple documents into the specified MongoDB collection
    
    Args:
        collection_name (str): Name of the collection
        documents (list): List of documents to insert
        database_name (str, optional): Name of the database. Defaults to settings.DATABASES['default']['NAME'].
        ordered (bool, optional): Whether to perform an ordered insert. Defaults to True.
    
    Returns:
        tuple: (success, result_or_error)
            - success (bool): True if insertion was successful, False otherwise
            - result_or_error: List of inserted IDs if successful, error message otherwise
    """
    try:
        # Get MongoDB client
        client = get_mongodb_client()
        
        # Get database name from settings if not provided
        if not database_name:
            database_name = settings.DATABASES['default']['NAME']
        
        # Get database and collection
        db = client[database_name]
        collection = db[collection_name]
        
        # Insert documents
        result = collection.insert_many(documents, ordered=ordered)
        
        # Return inserted IDs
        return True, result.inserted_ids
    
    except Exception as e:
        error_msg = f"Error inserting documents into {collection_name}: {str(e)}"
        logger.error(error_msg)
        return False, error_msg

def find_one(collection_name, query=None, database_name=None):
    """
    Finds a single document in the specified MongoDB collection
    
    Args:
        collection_name (str): Name of the collection
        query (dict, optional): Query filter. Defaults to None.
        database_name (str, optional): Name of the database. Defaults to settings.DATABASES['default']['NAME'].
    
    Returns:
        tuple: (success, result_or_error)
            - success (bool): True if query was successful, False otherwise
            - result_or_error: Document if found, None if not found, error message if error
    """
    try:
        # Get MongoDB client
        client = get_mongodb_client()
        
        # Get database name from settings if not provided
        if not database_name:
            database_name = settings.DATABASES['default']['NAME']
        
        # Get database and collection
        db = client[database_name]
        collection = db[collection_name]
        
        # Find document
        if query is None:
            query = {}
        
        document = collection.find_one(query)
        return True, document
    
    except Exception as e:
        error_msg = f"Error finding document in {collection_name}: {str(e)}"
        logger.error(error_msg)
        return False, error_msg

def insert_crop(crop_data):
    """
    Inserts a crop record into the 'crops' collection
    
    Args:
        crop_data (dict): Crop data with fields like name, type, field_id, etc.
    
    Returns:
        tuple: (success, result_or_error)
    """
    # Validate required fields
    required_fields = ['name', 'crop_type', 'field_id', 'planting_date']
    missing_fields = [field for field in required_fields if field not in crop_data]
    
    if missing_fields:
        return False, f"Missing required fields: {', '.join(missing_fields)}"
    
    # Add timestamp if not provided
    if 'created_at' not in crop_data:
        crop_data['created_at'] = datetime.now()
    
    # Insert into crops collection
    return insert('crops', crop_data)

def insert_soil_data(soil_data):
    """
    Inserts soil data into the 'soil_records' collection
    
    Args:
        soil_data (dict): Soil data with fields like field_id, type, ph_level, etc.
    
    Returns:
        tuple: (success, result_or_error)
    """
    # Validate required fields
    required_fields = ['field_id', 'soil_type']
    missing_fields = [field for field in required_fields if field not in soil_data]
    
    if missing_fields:
        return False, f"Missing required fields: {', '.join(missing_fields)}"
    
    # Add timestamp if not provided
    if 'recorded_at' not in soil_data:
        soil_data['recorded_at'] = datetime.now()
    
    # Insert into soil_records collection
    return insert('soil_records', soil_data)

def get_crops_by_field(field_id):
    """
    Retrieves all crops for a specific field
    
    Args:
        field_id: ID of the field
    
    Returns:
        tuple: (success, result_or_error)
    """
    try:
        client = get_mongodb_client()
        db_name = settings.DATABASES['default']['NAME']
        db = client[db_name]
        collection = db['crops']
        
        # Find all crops for the field
        cursor = collection.find({'field_id': field_id})
        crops = list(cursor)
        
        return True, crops
    except Exception as e:
        error_msg = f"Error retrieving crops for field {field_id}: {str(e)}"
        logger.error(error_msg)
        return False, error_msg

def get_soil_data_by_field(field_id):
    """
    Retrieves soil data for a specific field

    Args:
        field_id: ID of the field

    Returns:
        tuple: (success, result_or_error)
    """
    try:
        client = get_mongodb_client()
        db_name = settings.DATABASES['default']['NAME']
        db = client[db_name]
        collection = db['soil_records']

        # Find the most recent soil record for the field
        cursor = collection.find({'field_id': field_id}).sort('recorded_at', -1).limit(1)
        soil_data = list(cursor)

        if soil_data:
            return True, soil_data[0]
        else:
            return True, None
    except Exception as e:
        error_msg = f"Error retrieving soil data for field {field_id}: {str(e)}"
        logger.error(error_msg)
        return False, error_msg


# Authentication and Admin Logging Functions for MongoDB
def log_user_login(user, request, login_successful=True):
    """
    Logs user login information to MongoDB

    Args:
        user: User object
        request: Django request object
        login_successful: Boolean indicating if login was successful

    Returns:
        tuple: (success, result_or_error)
    """
    try:
        # Get client IP address
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0]
        else:
            ip_address = request.META.get('REMOTE_ADDR', '')

        # Get user agent
        user_agent = request.META.get('HTTP_USER_AGENT', '')

        # Get session key
        session_key = request.session.session_key or ''

        # Create login log document
        login_log = {
            'user_email': user.email if user else '',
            'user_id': user.id if user else 0,
            'login_timestamp': timezone.now(),
            'ip_address': ip_address,
            'user_agent': user_agent,
            'session_key': session_key,
            'login_successful': login_successful
        }

        # Insert into MongoDB
        return insert('user_login_logs', login_log)

    except Exception as e:
        error_msg = f"Error logging user login: {str(e)}"
        logger.error(error_msg)
        return False, error_msg


def log_user_logout(user, request):
    """
    Logs user logout information to MongoDB

    Args:
        user: User object
        request: Django request object

    Returns:
        tuple: (success, result_or_error)
    """
    try:
        # Get session key
        session_key = request.session.session_key or ''

        # Update the login log with logout timestamp
        client = get_mongodb_client()
        db_name = settings.DATABASES['mongodb']['NAME']
        db = client[db_name]
        collection = db['user_login_logs']

        # Find the most recent login for this user and session
        logout_time = timezone.now()
        result = collection.update_one(
            {
                'user_id': user.id,
                'session_key': session_key,
                'logout_timestamp': {'$exists': False}
            },
            {
                '$set': {
                    'logout_timestamp': logout_time
                }
            }
        )

        return True, result.modified_count

    except Exception as e:
        error_msg = f"Error logging user logout: {str(e)}"
        logger.error(error_msg)
        return False, error_msg


def log_admin_activity(admin_user, activity_type, description, request, affected_user=None, additional_data=None):
    """
    Logs admin activity to MongoDB

    Args:
        admin_user: Admin user object
        activity_type: Type of activity (login, logout, create_user, etc.)
        description: Description of the activity
        request: Django request object
        affected_user: User object that was affected by the activity (optional)
        additional_data: Additional data to store (optional)

    Returns:
        tuple: (success, result_or_error)
    """
    try:
        # Get client IP address
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0]
        else:
            ip_address = request.META.get('REMOTE_ADDR', '')

        # Get user agent
        user_agent = request.META.get('HTTP_USER_AGENT', '')

        # Create admin activity log document
        activity_log = {
            'admin_email': admin_user.email,
            'admin_id': admin_user.id,
            'activity_type': activity_type,
            'activity_description': description,
            'timestamp': timezone.now(),
            'ip_address': ip_address,
            'user_agent': user_agent,
            'affected_user_id': affected_user.id if affected_user else None,
            'affected_user_email': affected_user.email if affected_user else '',
            'additional_data': additional_data or {}
        }

        # Insert into MongoDB
        return insert('admin_activity_logs', activity_log)

    except Exception as e:
        error_msg = f"Error logging admin activity: {str(e)}"
        logger.error(error_msg)
        return False, error_msg


def create_user_session_info(user, request):
    """
    Creates detailed user session information in MongoDB

    Args:
        user: User object
        request: Django request object

    Returns:
        tuple: (success, result_or_error)
    """
    try:
        # Get client IP address
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0]
        else:
            ip_address = request.META.get('REMOTE_ADDR', '')

        # Get user agent
        user_agent = request.META.get('HTTP_USER_AGENT', '')

        # Get session key
        session_key = request.session.session_key or ''

        # Parse device info from user agent (basic parsing)
        device_info = {
            'user_agent': user_agent,
            'is_mobile': 'Mobile' in user_agent or 'Android' in user_agent or 'iPhone' in user_agent
        }

        # Create session info document
        session_info = {
            'user_email': user.email,
            'user_id': user.id,
            'session_key': session_key,
            'session_data': {},
            'created_at': timezone.now(),
            'last_activity': timezone.now(),
            'ip_address': ip_address,
            'user_agent': user_agent,
            'is_active': True,
            'device_info': device_info,
            'location_info': {}
        }

        # Insert into MongoDB
        return insert('user_session_info', session_info)

    except Exception as e:
        error_msg = f"Error creating user session info: {str(e)}"
        logger.error(error_msg)
        return False, error_msg

