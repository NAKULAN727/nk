from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _
from djongo import models as djongo_models
import json
from django.utils import timezone

class CustomUserManager(BaseUserManager):
    """Define a model manager for User model with no username field."""

    def _create_user(self, email, password=None, **extra_fields):
        """Create and save a User with the given email and password."""
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)

class CustomUser(AbstractUser):
    """Custom user model that uses email as the unique identifier instead of username."""

    # Use email as the unique identifier
    email = models.EmailField(_('email address'), unique=True)

    # Make username optional
    username = models.CharField(_('username'), max_length=150, blank=True)

    # Add additional fields
    phone_number = models.CharField(_('phone number'), max_length=15, blank=True)
    address = models.TextField(_('address'), blank=True)
    profile_picture = models.CharField(_('profile picture URL'), max_length=255, blank=True)

    # Specify the USERNAME_FIELD as email
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []  # Email & Password are required by default

    objects = CustomUserManager()

    def __str__(self):
        return self.email

class Farm(models.Model):
    """Model representing a farm owned by a user"""
    name = models.CharField(_('Farm Name'), max_length=100)
    owner = models.ForeignKey('CustomUser', on_delete=models.CASCADE, related_name='farms')
    location = models.CharField(_('Location'), max_length=100)
    size = models.DecimalField(_('Size'), max_digits=10, decimal_places=2)
    size_unit = models.CharField(_('Size Unit'), max_length=20, default='acres')
    description = models.TextField(_('Description'), blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Field(models.Model):
    """Model representing a field within a farm"""
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='fields')
    name = models.CharField(_('Field Name'), max_length=100)
    size = models.DecimalField(_('Size (acres)'), max_digits=10, decimal_places=2)
    soil_type = models.CharField(_('Soil Type'), max_length=50)
    
    def __str__(self):
        return f"{self.farm.name} - {self.name}"

class Crop(models.Model):
    """Model representing a crop planted in a field"""
    CROP_TYPES = [
        ('rice', _('Rice')),
        ('wheat', _('Wheat')),
        ('corn', _('Corn')),
        ('tomato', _('Tomato')),
        ('potato', _('Potato')),
        ('other', _('Other')),
    ]
    
    field = models.ForeignKey(Field, on_delete=models.CASCADE, related_name='crops')
    crop_type = models.CharField(_('Crop Type'), max_length=50, choices=CROP_TYPES)
    planting_date = models.DateField(_('Planting Date'))
    expected_harvest_date = models.DateField(_('Expected Harvest Date'))
    
    def __str__(self):
        return f"{self.get_crop_type_display()} in {self.field.name}"

class Sensor(models.Model):
    """Model representing a sensor installed in a field"""
    SENSOR_TYPES = [
        ('soil_moisture', _('Soil Moisture')),
        ('temperature', _('Temperature')),
        ('humidity', _('Humidity')),
        ('rainfall', _('Rainfall')),
        ('light', _('Light')),
    ]
    
    field = models.ForeignKey(Field, on_delete=models.CASCADE, related_name='sensors')
    sensor_type = models.CharField(_('Sensor Type'), max_length=50, choices=SENSOR_TYPES)
    name = models.CharField(_('Sensor Name'), max_length=100)
    installation_date = models.DateField(_('Installation Date'))
    is_active = models.BooleanField(_('Is Active'), default=True)
    
    def __str__(self):
        return f"{self.name} ({self.get_sensor_type_display()})"

class SensorReading(models.Model):
    """Model representing a reading from a sensor"""
    sensor = models.ForeignKey(Sensor, on_delete=models.CASCADE, related_name='readings')
    value = models.FloatField(_('Value'))
    timestamp = models.DateTimeField(_('Timestamp'), auto_now_add=True)
    
    def __str__(self):
        return f"{self.sensor.name}: {self.value} at {self.timestamp}"

class WeatherData(models.Model):
    """Model representing weather data for a farm"""
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='weather_data')
    temperature = models.FloatField(_('Temperature (°C)'))
    humidity = models.FloatField(_('Humidity (%)'))
    rainfall = models.FloatField(_('Rainfall (mm)'))
    wind_speed = models.FloatField(_('Wind Speed (km/h)'))
    description = models.CharField(_('Description'), max_length=100)
    timestamp = models.DateTimeField(_('Timestamp'), auto_now_add=True)
    
    def __str__(self):
        return f"Weather at {self.farm.name}: {self.temperature}°C, {self.description}"

class IrrigationSchedule(models.Model):
    """Model representing an irrigation schedule for a field"""
    field = models.ForeignKey(Field, on_delete=models.CASCADE, related_name='irrigation_schedules')
    start_time = models.DateTimeField(_('Start Time'))
    duration = models.IntegerField(_('Duration (minutes)'))
    water_amount = models.FloatField(_('Water Amount (liters)'))
    is_completed = models.BooleanField(_('Is Completed'), default=False)
    created_by = models.ForeignKey('CustomUser', on_delete=models.CASCADE, related_name='created_schedules')
    
    def __str__(self):
        return f"Irrigation for {self.field.name} at {self.start_time}"

class Task(models.Model):
    """Model representing a task to be completed on a farm"""
    PRIORITY_CHOICES = [
        ('low', _('Low')),
        ('medium', _('Medium')),
        ('high', _('High')),
    ]

    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(_('Title'), max_length=200)
    description = models.TextField(_('Description'))
    due_date = models.DateField(_('Due Date'))
    priority = models.CharField(_('Priority'), max_length=10, choices=PRIORITY_CHOICES, default='medium')
    is_completed = models.BooleanField(_('Is Completed'), default=False)
    assigned_to = models.ForeignKey('CustomUser', on_delete=models.CASCADE, related_name='assigned_tasks')
    created_by = models.ForeignKey('CustomUser', on_delete=models.CASCADE, related_name='created_tasks')

    def __str__(self):
        return self.title


# MongoDB Models - These will be stored in MongoDB
class UserLoginLog(djongo_models.Model):
    """Model for storing user login information in MongoDB"""
    user_email = djongo_models.CharField(max_length=255)
    user_id = djongo_models.IntegerField()
    login_timestamp = djongo_models.DateTimeField(auto_now_add=True)
    ip_address = djongo_models.CharField(max_length=45, blank=True)  # IPv6 support
    user_agent = djongo_models.TextField(blank=True)
    session_key = djongo_models.CharField(max_length=40, blank=True)
    login_successful = djongo_models.BooleanField(default=True)
    logout_timestamp = djongo_models.DateTimeField(null=True, blank=True)
    session_duration = djongo_models.IntegerField(null=True, blank=True)  # in seconds

    class Meta:
        db_table = 'user_login_logs'

    def __str__(self):
        return f"Login: {self.user_email} at {self.login_timestamp}"


class AdminActivityLog(djongo_models.Model):
    """Model for storing admin activity information in MongoDB"""
    admin_email = djongo_models.CharField(max_length=255)
    admin_id = djongo_models.IntegerField()
    activity_type = djongo_models.CharField(max_length=100)  # login, logout, create_user, delete_user, etc.
    activity_description = djongo_models.TextField()
    timestamp = djongo_models.DateTimeField(auto_now_add=True)
    ip_address = djongo_models.CharField(max_length=45, blank=True)
    user_agent = djongo_models.TextField(blank=True)
    affected_user_id = djongo_models.IntegerField(null=True, blank=True)
    affected_user_email = djongo_models.CharField(max_length=255, blank=True)
    additional_data = djongo_models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'admin_activity_logs'

    def __str__(self):
        return f"Admin {self.admin_email}: {self.activity_type} at {self.timestamp}"


class UserSessionInfo(djongo_models.Model):
    """Model for storing detailed user session information in MongoDB"""
    user_email = djongo_models.CharField(max_length=255)
    user_id = djongo_models.IntegerField()
    session_key = djongo_models.CharField(max_length=40, unique=True)
    session_data = djongo_models.JSONField(default=dict)
    created_at = djongo_models.DateTimeField(auto_now_add=True)
    last_activity = djongo_models.DateTimeField(auto_now=True)
    ip_address = djongo_models.CharField(max_length=45, blank=True)
    user_agent = djongo_models.TextField(blank=True)
    is_active = djongo_models.BooleanField(default=True)
    device_info = djongo_models.JSONField(default=dict, blank=True)
    location_info = djongo_models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'user_session_info'

    def __str__(self):
        return f"Session: {self.user_email} - {self.session_key}"

class SensorData(models.Model):
    """
    Model to store sensor data in MongoDB
    """
    mongodb_model = True  # This flag tells the router to use MongoDB

    sensor_id = models.CharField(max_length=100)
    sensor_type = models.CharField(max_length=50)
    value = models.FloatField()
    unit = models.CharField(max_length=20)
    timestamp = models.DateTimeField(default=timezone.now)
    location = models.CharField(max_length=100)
    
    # Additional metadata stored as JSON
    metadata = djongo_models.JSONField(default=dict)

    class Meta:
        db_table = 'sensor_data'

    def __str__(self):
        return f"{self.sensor_type} - {self.value}{self.unit} at {self.timestamp}"
