#!/usr/bin/env python
"""
Script to test MongoDB connection both directly and through Django.
"""
import os
import sys
import pymongo
from datetime import datetime

def test_direct_connection():
    """Test direct connection to MongoDB using pymongo."""
    print("Testing direct MongoDB connection...")
    try:
        # Connect to MongoDB
        client = pymongo.MongoClient("mongodb://localhost:27017/")
        
        # Get database information
        db_info = client.server_info()
        print(f"Successfully connected to MongoDB!")
        print(f"MongoDB version: {db_info.get('version', 'unknown')}")
        
        # List databases
        databases = client.list_database_names()
        print(f"Available databases: {', '.join(databases)}")
        
        # Create a test document in a test collection
        db = client["smart_agri_db"]
        collection = db["connection_test"]
        
        test_doc = {
            "test_id": "direct_connection_test",
            "timestamp": datetime.now(),
            "status": "success"
        }
        
        result = collection.insert_one(test_doc)
        print(f"Inserted test document with ID: {result.inserted_id}")
        
        # Retrieve the document
        retrieved = collection.find_one({"test_id": "direct_connection_test"})
        if retrieved:
            print(f"Successfully retrieved test document: {retrieved}")
        
        return True
    except Exception as e:
        print(f"Error connecting to MongoDB: {str(e)}")
        return False

def test_django_connection():
    """Test MongoDB connection through Django ORM."""
    print("\nTesting Django MongoDB connection...")
    
    # Add the Django project directory to the Python path
    project_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                               "smart_agri2", "smart_agri", "agri_dashboard")
    sys.path.append(project_path)
    
    # Set up Django environment
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agri_dashboard.settings')
    
    try:
        import django
        django.setup()
        
        # Import models after Django setup
        from main.models import UserLoginLog, SensorData
        from django.utils import timezone
        
        # Create a test login log
        test_log = UserLoginLog(
            user_email='test_script@example.com',
            user_id=999,
            ip_address='127.0.0.1',
            user_agent='Test Script',
            session_key='test_script_session',
            login_successful=True
        )
        test_log.save()
        print(f"Created test login log with ID: {test_log.id}")
        
        # Retrieve the log
        retrieved_log = UserLoginLog.objects.filter(user_email='test_script@example.com').first()
        if retrieved_log:
            print(f"Successfully retrieved log: {retrieved_log}")
        else:
            print("Failed to retrieve log")
        
        # Create test sensor data
        test_sensor = SensorData(
            sensor_id='test-script-sensor-001',
            sensor_type='temperature',
            value=25.5,
            unit='°C',
            timestamp=timezone.now(),
            location='Test Script Location',
            metadata={
                'battery': '90%',
                'signal_strength': 'excellent',
                'test_source': 'test_script'
            }
        )
        test_sensor.save()
        print(f"Created test sensor data with ID: {test_sensor.id}")
        
        # Retrieve the sensor data
        retrieved_sensor = SensorData.objects.filter(sensor_id='test-script-sensor-001').first()
        if retrieved_sensor:
            print(f"Successfully retrieved sensor data: {retrieved_sensor.sensor_type} - {retrieved_sensor.value}{retrieved_sensor.unit}")
            print(f"Metadata: {retrieved_sensor.metadata}")
        else:
            print("Failed to retrieve sensor data")
            
        return True
    except Exception as e:
        print(f"Error testing Django MongoDB connection: {str(e)}")
        return False

if __name__ == "__main__":
    print("MongoDB Connection Test Script")
    print("==============================")
    
    direct_success = test_direct_connection()
    django_success = test_django_connection()
    
    print("\nTest Results:")
    print(f"Direct MongoDB Connection: {'SUCCESS' if direct_success else 'FAILED'}")
    print(f"Django MongoDB Connection: {'SUCCESS' if django_success else 'FAILED'}")
    
    if direct_success and django_success:
        print("\nAll MongoDB connection tests passed successfully!")
    else:
        print("\nSome tests failed. Please check the error messages above.")