from django.core.management.base import BaseCommand
from main.models import UserLoginLog, SensorData
from django.utils import timezone
import random

class Command(BaseCommand):
    help = 'Test MongoDB connection by creating and retrieving test records'

    def handle(self, *args, **kwargs):
        try:
            # Test UserLoginLog
            self.stdout.write(self.style.SUCCESS('Testing MongoDB connection...'))
            
            # Create a test login log
            test_log = UserLoginLog(
                user_email='test@example.com',
                user_id=1,
                ip_address='127.0.0.1',
                user_agent='Test Agent',
                session_key='test_session',
                login_successful=True
            )
            test_log.save()
            self.stdout.write(self.style.SUCCESS(f'Created test login log with ID: {test_log.id}'))
            
            # Retrieve the log
            retrieved_log = UserLoginLog.objects.filter(user_email='test@example.com').first()
            if retrieved_log:
                self.stdout.write(self.style.SUCCESS(f'Successfully retrieved log: {retrieved_log}'))
            else:
                self.stdout.write(self.style.ERROR('Failed to retrieve log'))
            
            # Test SensorData
            # Create test sensor data
            test_sensor = SensorData(
                sensor_id='test-sensor-001',
                sensor_type='temperature',
                value=random.uniform(20.0, 30.0),
                unit='°C',
                timestamp=timezone.now(),
                location='Test Farm',
                metadata={
                    'battery': '85%',
                    'signal_strength': 'good',
                    'firmware_version': '1.2.3'
                }
            )
            test_sensor.save()
            self.stdout.write(self.style.SUCCESS(f'Created test sensor data with ID: {test_sensor.id}'))
            
            # Retrieve the sensor data
            retrieved_sensor = SensorData.objects.filter(sensor_id='test-sensor-001').first()
            if retrieved_sensor:
                self.stdout.write(self.style.SUCCESS(
                    f'Successfully retrieved sensor data: {retrieved_sensor.sensor_type} - {retrieved_sensor.value}{retrieved_sensor.unit}'
                ))
                self.stdout.write(self.style.SUCCESS(f'Metadata: {retrieved_sensor.metadata}'))
            else:
                self.stdout.write(self.style.ERROR('Failed to retrieve sensor data'))
                
            self.stdout.write(self.style.SUCCESS('MongoDB connection test completed successfully!'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error testing MongoDB connection: {str(e)}'))