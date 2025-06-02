from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, Http404
import json
import random
import requests
import os
from datetime import datetime, timedelta
from django.utils import translation
from django.conf import settings
from .models import CustomUser, SensorData
from .utils import (
    insert, insert_many, find_one, check_mongodb_connection,
    insert_crop, insert_soil_data,
    get_crops_by_field, get_soil_data_by_field
)
from django.views.decorators.csrf import csrf_exempt
from bson.json_util import dumps

# Add custom error handlers
def page_not_found(request, exception):
    """
    Custom 404 error handler
    """
    return render(request, 'error_pages/404.html', {
        'error_code': '404',
        'error_message': 'The page you requested could not be found',
        'suggestion': 'Please check the URL or navigate using the menu options.'
    }, status=404)

def server_error(request):
    """
    Custom 500 error handler
    """
    return render(request, 'error_pages/500.html', {
        'error_code': '500',
        'error_message': 'Internal server error',
        'suggestion': 'Something went wrong on our end. Please try again later or contact support if the problem persists.'
    }, status=500)

def connection_error(request):
    """
    View to handle connection errors
    """
    return render(request, 'error_pages/connection_error.html', {
        'error_code': 'WinError 10053',
        'error_message': 'An established connection was aborted by the software in your host machine',
        'suggestion': 'Please check your network connection and try again. If the problem persists, contact support.'
    })

def permission_denied(request, exception):
    """
    Custom 403 error handler
    """
    return render(request, 'error_pages/403.html', {
        'error_code': '403',
        'error_message': 'You do not have permission to access this resource',
        'suggestion': 'Please log in with an account that has the necessary permissions, or contact an administrator.'
    }, status=403)

# Modify get_weather_data to handle connection errors better
def get_weather_data(city="London"):
    """Fetch real-time weather data from OpenWeatherMap API with improved error handling"""
    api_key = settings.OPENWEATHER_API_KEY  # Get API key from Django settings
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&units=metric&appid={api_key}"
    
    try:
        response = requests.get(url, timeout=5)
        data = response.json()
        
        if response.status_code == 200:
            return {
                'temperature': data['main']['temp'],
                'humidity': data['main']['humidity'],
                'description': data['weather'][0]['description'],
                'icon': data['weather'][0]['icon'],
                'wind_speed': data['wind']['speed'],
                'pressure': data['main']['pressure'],
                'city': data['name'],
                'country': data['sys']['country'],
            }
        else:
            print(f"Weather API error: {data.get('message', 'Unknown error')}")
            return None
    except requests.exceptions.ConnectionError as e:
        print(f"Connection error when fetching weather data: {e}")
        return None
    except requests.exceptions.Timeout as e:
        print(f"Timeout error when fetching weather data: {e}")
        return None
    except Exception as e:
        print(f"Error fetching weather data: {e}")
        return None
        # Add login_required decorator to protect the home view
@login_required(login_url='login')
def home(request):
    # Set the language from session if available
    language = request.session.get('language', 'en')
    translation.activate(language)
    
    # Get user's location (default to London if not set)
    user_location = request.session.get('location', 'London')
    
    # Get real-time weather data
    weather_data = get_weather_data(user_location)
    
    # If weather API call failed, use default data
    if not weather_data:
        weather_data = {
            'temperature': 24,
            'humidity': 58,
            'description': 'Clear sky',
            'icon': '01d',
        }
    
    # Simulate soil moisture data (in a real app, this would come from sensors)
    soil_moisture = 65
    
    # Simulate rainfall data
    rainfall_data = 25
    rainfall_change = 10
    
    # Temperature change (compare with previous reading)
    temp_change = 2
    
    # Humidity change
    humidity_change = -5
    
    # Initial data for the charts
    temperature_data = [18, 20, 24, 26, 25, 22, 19]
    
    # Context with all the data needed for the page
    context = {
        'temperature_data': json.dumps(temperature_data),
        'current_language': language,
        'weather': weather_data,
        'soil_moisture': soil_moisture,
        'soil_moisture_change': 3,
        'rainfall': rainfall_data,
        'rainfall_change': rainfall_change,
        'temp_change': temp_change,
        'humidity_change': humidity_change
    }
    
    return render(request, 'index.html', context)

def login_view(request):
    # If user is already authenticated, redirect to dashboard
    if request.user.is_authenticated:
        return redirect('home')
        
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        remember_me = request.POST.get('remember') == 'on'
        
        # Debug: Print form data
        print(f"Login form data: email='{email}', password filled: {'yes' if password else 'no'}")
        
        # Validate input
        if not email or not password:
            messages.error(request, 'Please fill in all fields')
            return render(request, 'login.html', {'email': email})
        
        # Authenticate user
        user = authenticate(request, email=email, password=password)
        
        if user is not None:
            login(request, user)
            
            # Handle remember me option
            if not remember_me:
                request.session.set_expiry(0)  # Session expires when browser closes
            
            # Redirect to the 'next' parameter if it exists, otherwise to dashboard
            next_url = request.GET.get('next', 'home')
            messages.success(request, 'Login successful!')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid email or password')
            return render(request, 'login.html', {'email': email})
    
    return render(request, 'login.html')

def forgot_password(request):
    # Handle password reset functionality
    if request.method == 'POST':
        email = request.POST.get('email')
        # In a real app, you would send a password reset email
        messages.info(request, 'Password reset instructions have been sent to your email')
    
    return render(request, 'forgot_password.html')

def signup(request):
    if request.method == 'POST':
        # Get form data
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        phone_number = request.POST.get('phone_number', '').strip()
        address = request.POST.get('address', '').strip()
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')
        
        # Debug: Print form data
        print(f"Form data: first_name='{first_name}', last_name='{last_name}', email='{email}', "
              f"phone_number='{phone_number}', address='{address}', "
              f"password1 filled: {'yes' if password1 else 'no'}, "
              f"password2 filled: {'yes' if password2 else 'no'}")
        
        # Validate form data - make validation more lenient
        missing_fields = []
        if not first_name:
            missing_fields.append('First Name')
        if not last_name:
            missing_fields.append('Last Name')
        if not email:
            missing_fields.append('Email')
        if not password1:
            missing_fields.append('Password')
        if not password2:
            missing_fields.append('Confirm Password')
        
        if missing_fields:
            messages.error(request, f"Please fill in the following fields: {', '.join(missing_fields)}")
            return render(request, 'signup.html', {
                'first_name': first_name,
                'last_name': last_name,
                'email': email,
                'phone_number': phone_number,
                'address': address
            })
        
        if password1 != password2:
            messages.error(request, 'Passwords do not match')
            return render(request, 'signup.html', {
                'first_name': first_name,
                'last_name': last_name,
                'email': email,
                'phone_number': phone_number,
                'address': address
            })
        
        # Check if email already exists
        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists')
            return render(request, 'signup.html', {
                'first_name': first_name,
                'last_name': last_name,
                'phone_number': phone_number,
                'address': address
            })
        
        # Create user
        try:
            user = CustomUser.objects.create_user(
                email=email,
                password=password1,
                first_name=first_name,
                last_name=last_name,
                phone_number=phone_number,
                address=address
            )
            messages.success(request, 'Account created successfully! You can now login.')
            return redirect('login')
        except Exception as e:
            messages.error(request, f'Error creating account: {str(e)}')
            return render(request, 'signup.html', {
                'first_name': first_name,
                'last_name': last_name,
                'email': email,
                'phone_number': phone_number,
                'address': address
            })
    
    return render(request, 'signup.html')

def change_language(request):
    """Change the user's language preference"""
    if request.method == 'GET':
        language = request.GET.get('language', 'en')
        # Save to session
        request.session['django_language'] = language
        
        # Redirect to the referring page or home
        next_url = request.GET.get('next', request.META.get('HTTP_REFERER', '/dashboard/'))
        
        response = redirect(next_url)
        response.set_cookie('django_language', language)
        return response
    
    return redirect('home')

# Add logout functionality
def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully')
    return redirect('login')

# Functions for handling AJAX requests related to the dashboard

@login_required(login_url='login')
def update_sensor_data(request):
    """Update sensor data with real weather data and simulated soil moisture"""
    if request.method == 'GET':
        # Get real weather data
        weather_data = get_weather_data(request.session.get('location', 'London'))
        
        if not weather_data:
            # Generate random sensor data if API fails
            temperature = random.randint(18, 28)
            humidity = random.randint(40, 70)
            weather_description = "Clear"
        else:
            temperature = weather_data['temperature']
            humidity = weather_data['humidity']
            weather_description = weather_data.get('description', 'Clear')
        
        # Simulate soil moisture data (in a real app, this would come from sensors)
        soil_moisture = random.randint(55, 75)
        
        # Simulate rainfall data
        rainfall = random.uniform(0, 50)
        
        # Calculate crop health based on weather conditions
        crops = [
            {
                'name': 'Corn',
                'icon': '🌽',
                'health': calculate_crop_health('corn', temperature, humidity, soil_moisture, rainfall, weather_description),
                'recommendation': get_crop_recommendation('corn', temperature, humidity, soil_moisture, rainfall, weather_description)
            },
            {
                'name': 'Tomatoes',
                'icon': '🍅',
                'health': calculate_crop_health('tomatoes', temperature, humidity, soil_moisture, rainfall, weather_description),
                'recommendation': get_crop_recommendation('tomatoes', temperature, humidity, soil_moisture, rainfall, weather_description)
            },
            {
                'name': 'Potatoes',
                'icon': '🥔',
                'health': calculate_crop_health('potatoes', temperature, humidity, soil_moisture, rainfall, weather_description),
                'recommendation': get_crop_recommendation('potatoes', temperature, humidity, soil_moisture, rainfall, weather_description)
            }
        ]
        
        return JsonResponse({
            'temperature': temperature,
            'humidity': humidity,
            'soil_moisture': soil_moisture,
            'rainfall': round(rainfall),
            'crops': crops,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    
    return JsonResponse({'status': 'error'}, status=400)

def calculate_crop_health(crop_type, temperature, humidity, soil_moisture, rainfall, weather):
    """Calculate crop health percentage based on environmental conditions"""
    # Default health is 70%
    health = 70
    
    # Different crops have different optimal conditions
    if crop_type == 'corn':
        # Corn likes warm weather and moderate moisture
        if temperature < 10 or temperature > 35:
            health -= 20
        if soil_moisture < 40 or soil_moisture > 80:
            health -= 15
        if 'rain' in weather.lower() and rainfall > 30:
            health -= 10
        if humidity > 80:
            health -= 10
    elif crop_type == 'tomatoes':
        # Tomatoes prefer warm, not hot weather and consistent moisture
        if temperature < 15 or temperature > 32:
            health -= 15
        if soil_moisture < 50 or soil_moisture > 70:
            health -= 20
        if 'rain' in weather.lower() and rainfall > 20:
            health -= 15
        if humidity > 85:
            health -= 15
    elif crop_type == 'potatoes':
        # Potatoes like cooler temperatures and moderate moisture
        if temperature < 7 or temperature > 30:
            health -= 10
        if soil_moisture < 60 or soil_moisture > 85:
            health -= 15
        if 'rain' in weather.lower() and rainfall > 40:
            health -= 5
        if humidity < 40 or humidity > 90:
            health -= 10
    
    # Ensure health stays within 0-100 range
    return max(0, min(100, health))

def get_crop_recommendation(crop_type, temperature, humidity, soil_moisture, rainfall, weather):
    """Get recommendations based on crop type and conditions"""
    if crop_type == 'corn':
        if temperature < 10:
            return "Too cold for corn. Consider protective measures."
        if soil_moisture < 40:
            return "Increase irrigation for corn."
        if soil_moisture > 80:
            return "Reduce irrigation for corn."
        if 'rain' in weather.lower() and rainfall > 30:
            return "Check corn for water damage."
        return "Corn growing conditions are good."
    elif crop_type == 'tomatoes':
        if temperature < 15:
            return "Too cold for tomatoes. Consider greenhouse."
        if temperature > 32:
            return "Provide shade for tomatoes in hot weather."
        if soil_moisture < 50:
            return "Increase irrigation for tomatoes."
        if soil_moisture > 70:
            return "Reduce irrigation for tomatoes."
        return "Tomato growing conditions are good."
    elif crop_type == 'potatoes':
        if temperature > 30:
            return "Too hot for potatoes. Provide shade."
        if soil_moisture < 60:
            return "Increase irrigation for potatoes."
        if soil_moisture > 85:
            return "Reduce irrigation for potatoes."
        return "Potato growing conditions are good."
    return "Monitor crop conditions regularly."

@login_required(login_url='login')
def handle_irrigation(request):
    """Handle irrigation activation"""
    if request.method == 'POST':
        zone_id = request.POST.get('zone_id')
        # In a real app, you would trigger actual irrigation hardware
        
        # Simulate increasing moisture level
        current_moisture = int(request.POST.get('current_moisture', 0))
        new_moisture = min(current_moisture + 25, 100)
        
        return JsonResponse({
            'status': 'success',
            'zone_id': zone_id,
            'new_moisture': new_moisture,
            'message': f'Zone {zone_id} irrigation activated'
        })
    
    return JsonResponse({'status': 'error'}, status=400)

@login_required(login_url='login')
def complete_task(request):
    """Mark a task as complete"""
    if request.method == 'POST':
        task_id = request.POST.get('task_id')
        # In a real app, you would update the task in the database
        
        return JsonResponse({
            'status': 'success',
            'task_id': task_id,
            'message': 'Task marked as complete'
        })
    
    return JsonResponse({'status': 'error'}, status=400)

@login_required(login_url='login')
def schedule_irrigation(request):
    """API endpoint to schedule irrigation for a field"""
    if request.method == 'POST':
        try:
            # Parse JSON data from request body
            data = json.loads(request.body)
            
            # In a real app, this would create an irrigation schedule in the database
            # For demo purposes, we'll just return success
            
            return JsonResponse({
                'status': 'success',
                'message': 'Irrigation scheduled successfully',
                'schedule': {
                    'field': data.get('field_name', 'Unknown field'),
                    'start_time': data.get('start_time', 'Now'),
                    'duration': data.get('duration', 30),
                    'water_amount': data.get('water_amount', 100)
                }
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
    
    return JsonResponse({
        'status': 'error',
        'message': 'Method not allowed'
    }, status=405)

@login_required(login_url='login')
def get_weather_alert(request):
    """API endpoint to get weather alerts"""
    # In a real application, this would check a weather API or database
    # For demo purposes, we'll return a sample alert
    
    # Random chance of different alerts for demo
    import random
    alert_chance = random.random()
    
    if alert_chance < 0.2:  # 20% chance of alert
        alert_type = random.choice(['warning', 'danger', 'info'])
        
        if alert_type == 'warning':
            return JsonResponse({
                'status': 'warning',
                'type': 'warning',
                'title': 'Heavy Rain Warning',
                'message': 'Heavy rainfall expected in the next 24 hours. Consider delaying irrigation.'
            })
        elif alert_type == 'danger':
            return JsonResponse({
                'status': 'danger',
                'type': 'danger',
                'title': 'Frost Alert',
                'message': 'Frost expected tonight. Protect sensitive crops.'
            })
        else:
            return JsonResponse({
                'status': 'info',
                'type': 'info',
                'title': 'Weather Update',
                'message': 'Temperatures will be higher than normal this week.'
            })
    else:
        return JsonResponse({
            'status': 'no_alert'
        })

@login_required(login_url='login')
def get_weather_forecast(request):
    """API endpoint to get weather forecast"""
    # In a real application, this would fetch data from a weather API
    # For demo purposes, we'll return sample forecast data
    
    import random
    from datetime import datetime, timedelta
    
    # Generate a 5-day forecast
    forecast = []
    conditions = ['Sunny', 'Partly Cloudy', 'Cloudy', 'Light Rain', 'Heavy Rain']
    
    for i in range(5):
        day_date = datetime.now() + timedelta(days=i)
        day_name = day_date.strftime('%a')
        
        # Generate random temperatures and conditions
        high_temp = random.randint(22, 35)
        low_temp = random.randint(15, 22)
        condition = random.choice(conditions)
        
        forecast.append({
            'day': day_name,
            'date': day_date.strftime('%Y-%m-%d'),
            'high_temp': high_temp,
            'low_temp': low_temp,
            'condition': condition,
            'humidity': random.randint(40, 90),
            'wind_speed': random.randint(0, 30)
        })
    
    return JsonResponse({
        'forecast': forecast
    })

def root_redirect(request):
    """
    Always redirect to login page first
    """
    return redirect('login')

@csrf_exempt
def test_mongodb_insert(request):
    """
    Test view to demonstrate MongoDB insert operations
    """
    if request.method == 'POST':
        try:
            # Parse JSON data from request body
            data = json.loads(request.body)
            
            # Insert document into MongoDB
            collection_name = data.get('collection', 'test_collection')
            document = data.get('document', {'test': True, 'message': 'Test document'})
            
            success, result = insert(collection_name, document)
            
            if success:
                # Convert ObjectId to string for JSON serialization
                inserted_id = str(result)
                
                # Retrieve the inserted document
                _, inserted_doc = find_one(collection_name, {'_id': result})
                
                if inserted_doc:
                    # Convert MongoDB document to JSON-serializable format
                    inserted_doc_json = json.loads(dumps(inserted_doc))
                    
                    return JsonResponse({
                        'status': 'success',
                        'message': 'Document inserted successfully',
                        'inserted_id': inserted_id,
                        'document': inserted_doc_json
                    })
                else:
                    return JsonResponse({
                        'status': 'success',
                        'message': 'Document inserted successfully, but could not retrieve it',
                        'inserted_id': inserted_id
                    })
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Failed to insert document: {result}'
                }, status=500)
                
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Error processing request: {str(e)}'
            }, status=400)
    
    # Check MongoDB connection for GET requests
    elif request.method == 'GET':
        is_connected, message = check_mongodb_connection()
        
        if is_connected:
            return JsonResponse({
                'status': 'success',
                'message': message,
                'example_document': {
                    'name': 'Example Crop',
                    'type': 'Wheat',
                    'field_id': 1,
                    'planting_date': '2023-05-15',
                    'expected_harvest_date': '2023-09-01'
                }
            })
        else:
            return JsonResponse({
                'status': 'error',
                'message': message
            }, status=500)
    
    return JsonResponse({
        'status': 'error',
        'message': 'Method not allowed'
    }, status=405)

@login_required
@csrf_exempt
def manage_crops(request):
    """
    View to manage crops in fields
    - GET: Retrieve crops for a field
    - POST: Add a new crop
    """
    if request.method == 'GET':
        field_id = request.GET.get('field_id')
        if not field_id:
            return JsonResponse({
                'status': 'error',
                'message': 'Field ID is required'
            }, status=400)
        
        success, result = get_crops_by_field(field_id)
        
        if success:
            # Convert MongoDB documents to JSON-serializable format
            crops_json = json.loads(dumps(result))
            return JsonResponse({
                'status': 'success',
                'crops': crops_json
            })
        else:
            return JsonResponse({
                'status': 'error',
                'message': result
            }, status=500)
    
    elif request.method == 'POST':
        try:
            # Parse JSON data from request body
            data = json.loads(request.body)
            
            # Add user information
            data['user_id'] = request.user.id
            
            # Convert string dates to datetime objects
            if 'planting_date' in data and isinstance(data['planting_date'], str):
                data['planting_date'] = datetime.strptime(data['planting_date'], '%Y-%m-%d')
            
            if 'expected_harvest_date' in data and isinstance(data['expected_harvest_date'], str):
                data['expected_harvest_date'] = datetime.strptime(data['expected_harvest_date'], '%Y-%m-%d')
            
            # Insert crop data
            success, result = insert_crop(data)
            
            if success:
                # Return success response
                return JsonResponse({
                    'status': 'success',
                    'message': 'Crop added successfully',
                    'crop_id': str(result)
                })
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': result
                }, status=500)
                
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Error processing request: {str(e)}'
            }, status=400)
    
    return JsonResponse({
        'status': 'error',
        'message': 'Method not allowed'
    }, status=405)

@login_required
@csrf_exempt
def manage_soil_data(request):
    """
    View to manage soil data
    - GET: Retrieve soil data for a field
    - POST: Add new soil data
    """
    if request.method == 'GET':
        field_id = request.GET.get('field_id')
        if not field_id:
            return JsonResponse({
                'status': 'error',
                'message': 'Field ID is required'
            }, status=400)
        
        success, result = get_soil_data_by_field(field_id)
        
        if success:
            # Convert MongoDB document to JSON-serializable format
            soil_data_json = json.loads(dumps(result)) if result else None
            return JsonResponse({
                'status': 'success',
                'soil_data': soil_data_json
            })
        else:
            return JsonResponse({
                'status': 'error',
                'message': result
            }, status=500)
    
    elif request.method == 'POST':
        try:
            # Parse JSON data from request body
            data = json.loads(request.body)
            
            # Add user information
            data['recorded_by'] = request.user.id
            
            # Insert soil data
            success, result = insert_soil_data(data)
            
            if success:
                # Return success response
                return JsonResponse({
                    'status': 'success',
                    'message': 'Soil data added successfully',
                    'record_id': str(result)
                })
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': result
                }, status=500)
                
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Error processing request: {str(e)}'
            }, status=400)
    
    return JsonResponse({
        'status': 'error',
        'message': 'Method not allowed'
    }, status=405)

@login_required
def add_crop_form(request):
    """View to display the crop form"""
    # Get all fields for the current user's farms
    fields = Field.objects.filter(farm__owner=request.user)
    return render(request, 'add_crop_form.html', {'fields': fields})

@login_required(login_url='login')
def soil_crop_recommendations(request):
    """View to recommend crops based on soil type"""
    soil_type = request.GET.get('soil_type', '')
    
    # Dictionary mapping soil types to recommended crops with descriptions
    soil_crop_mapping = {
        'clay': {
            'crops': [
                {'name': 'Rice', 'description': 'Thrives in clay soil due to its water retention properties.'},
                {'name': 'Wheat', 'description': 'Well-suited to clay soils with good nutrient content.'},
                {'name': 'Cabbage', 'description': 'Grows well in heavy clay soils with adequate moisture.'},
                {'name': 'Broccoli', 'description': 'Benefits from the nutrient-rich nature of clay soil.'},
                {'name': 'Brussels Sprouts', 'description': 'Performs well in clay soil with proper drainage.'}
            ]
        },
        'sandy': {
            'crops': [
                {'name': 'Carrots', 'description': 'Thrive in sandy soil that allows for straight root development.'},
                {'name': 'Potatoes', 'description': 'Grow well in loose sandy soil that allows tubers to expand.'},
                {'name': 'Radishes', 'description': 'Develop quickly in light sandy soils.'},
                {'name': 'Lettuce', 'description': 'Grows well in sandy soil with adequate irrigation.'},
                {'name': 'Strawberries', 'description': 'Prefer well-drained sandy soil for optimal growth.'}
            ]
        },
        'loamy': {
            'crops': [
                {'name': 'Corn', 'description': 'Thrives in nutrient-rich loamy soil with good drainage.'},
                {'name': 'Tomatoes', 'description': 'Produce abundant fruit in loamy soil with balanced nutrients.'},
                {'name': 'Peppers', 'description': 'Grow well in loamy soil with consistent moisture.'},
                {'name': 'Beans', 'description': 'Develop strong root systems in loamy soil.'},
                {'name': 'Cucumbers', 'description': 'Produce high yields in fertile loamy soil.'}
            ]
        },
        'chalky': {
            'crops': [
                {'name': 'Spinach', 'description': 'Tolerates the alkaline conditions of chalky soil.'},
                {'name': 'Beets', 'description': 'Grow well in chalky soil with proper nutrient management.'},
                {'name': 'Cabbage', 'description': 'Adapts to chalky soil conditions with adequate moisture.'},
                {'name': 'Sweetcorn', 'description': 'Can perform well in chalky soil with added organic matter.'},
                {'name': 'Beans', 'description': 'Tolerate chalky soil when provided with sufficient nutrients.'}
            ]
        },
        'peaty': {
            'crops': [
                {'name': 'Legumes', 'description': 'Help improve the structure of peaty soil.'},
                {'name': 'Root Vegetables', 'description': 'Benefit from the loose structure of peaty soil.'},
                {'name': 'Brassicas', 'description': 'Grow well in peaty soil with pH adjustment.'},
                {'name': 'Onions', 'description': 'Develop well in the moisture-retentive nature of peaty soil.'},
                {'name': 'Salad Greens', 'description': 'Thrive in the nutrient-rich environment of peaty soil.'}
            ]
        }
    }
    
    # Get recommendations for the selected soil type
    recommendations = soil_crop_mapping.get(soil_type, {})
    
    context = {
        'selected_soil': soil_type,
        'recommendations': recommendations
    }
    
    return render(request, 'soil_crop_recommendations.html', context)

@login_required(login_url='login')
def crop_details(request, crop_name):
    """View to display detailed information about a specific crop"""
    # Dictionary with detailed crop information
    crop_details_data = {
        'rice': {
            'name': 'Rice',
            'scientific_name': 'Oryza sativa',
            'growing_season': 'Warm season',
            'days_to_maturity': '120-180 days',
            'optimal_temperature': '20-35°C',
            'water_needs': 'High',
            'soil_ph': '5.5-6.5',
            'planting_depth': '1-2 cm',
            'row_spacing': '20-30 cm',
            'fertilizer_needs': 'High in nitrogen',
            'common_pests': 'Rice water weevil, stem borers, rice leafhopper',
            'diseases': 'Rice blast, bacterial leaf blight, sheath blight',
            'harvesting': 'When grains are firm but not hard, and straw has turned yellow',
            'description': 'Rice is a staple food for over half of the world\'s population. It is grown in flooded fields called paddies.',
            'tips': 'Maintain consistent water levels. Drain fields before harvesting.',
            'suitable_soils': [
                {'type': 'clay', 'suitability': 'excellent'},
                {'type': 'loamy', 'suitability': 'good'},
                {'type': 'silty', 'suitability': 'good'},
                {'type': 'sandy', 'suitability': 'poor'}
            ]
        },
        'wheat': {
            'name': 'Wheat',
            'scientific_name': 'Triticum aestivum',
            'growing_season': 'Cool season',
            'days_to_maturity': '100-130 days',
            'optimal_temperature': '15-25°C',
            'water_needs': 'Moderate',
            'soil_ph': '6.0-7.0',
            'planting_depth': '2-3 cm',
            'row_spacing': '15-20 cm',
            'fertilizer_needs': 'Balanced NPK',
            'common_pests': 'Aphids, Hessian fly, armyworms',
            'diseases': 'Rust, powdery mildew, Fusarium head blight',
            'harvesting': 'When grain is hard and straw is golden yellow',
            'description': 'Wheat is one of the world\'s most important cereal crops, used for making bread, pasta, and many other food products.',
            'tips': 'Plant at the right time for your climate zone. Control weeds early.',
            'suitable_soils': [
                {'type': 'loamy', 'suitability': 'excellent'},
                {'type': 'clay', 'suitability': 'good'},
                {'type': 'silty', 'suitability': 'good'},
                {'type': 'chalky', 'suitability': 'fair'}
            ]
        },
        'corn': {
            'name': 'Corn',
            'scientific_name': 'Zea mays',
            'growing_season': 'Warm season',
            'days_to_maturity': '60-100 days',
            'optimal_temperature': '20-30°C',
            'water_needs': 'Moderate to high',
            'soil_ph': '5.8-7.0',
            'planting_depth': '3-5 cm',
            'row_spacing': '75-100 cm',
            'fertilizer_needs': 'High in nitrogen',
            'common_pests': 'Corn earworm, European corn borer, corn rootworm',
            'diseases': 'Corn smut, leaf blight, stalk rot',
            'harvesting': 'Sweet corn: when kernels are plump and milky; Field corn: when kernels are hard',
            'description': 'Corn is a versatile crop used for human consumption, animal feed, and industrial products.',
            'tips': 'Plant in blocks rather than single rows for better pollination. Side-dress with nitrogen when plants are knee-high.',
            'suitable_soils': [
                {'type': 'loamy', 'suitability': 'excellent'},
                {'type': 'silty', 'suitability': 'good'},
                {'type': 'sandy', 'suitability': 'fair'},
                {'type': 'clay', 'suitability': 'fair'}
            ]
        },
        'tomatoes': {
            'name': 'Tomatoes',
            'scientific_name': 'Solanum lycopersicum',
            'growing_season': 'Warm season',
            'days_to_maturity': '60-85 days',
            'optimal_temperature': '20-30°C',
            'water_needs': 'Moderate',
            'soil_ph': '6.0-6.8',
            'planting_depth': '0.5-1 cm (seeds), 10-15 cm (transplants)',
            'row_spacing': '60-90 cm',
            'fertilizer_needs': 'Balanced, higher in phosphorus and potassium',
            'common_pests': 'Tomato hornworm, aphids, whiteflies',
            'diseases': 'Early blight, late blight, fusarium wilt',
            'harvesting': 'When fruits are firm and fully colored',
            'description': 'Tomatoes are one of the most popular garden vegetables, used fresh or in countless recipes. They come in many varieties, sizes, and colors.',
            'tips': 'Provide support for indeterminate varieties. Water at the base to prevent leaf diseases. Prune suckers for larger fruits.'
        },
        'potatoes': {
            'name': 'Potatoes',
            'scientific_name': 'Solanum tuberosum',
            'growing_season': 'Cool season',
            'days_to_maturity': '70-120 days',
            'optimal_temperature': '15-20°C',
            'water_needs': 'Moderate, consistent',
            'soil_ph': '5.0-6.5',
            'planting_depth': '10-15 cm',
            'row_spacing': '70-90 cm',
            'fertilizer_needs': 'Balanced NPK, avoid excess nitrogen',
            'common_pests': 'Colorado potato beetle, potato aphid, wireworms',
            'diseases': 'Late blight, early blight, scab',
            'harvesting': 'When tops begin to die back and tubers have firm skins',
            'description': 'Potatoes are a staple crop grown for their starchy tubers. They are versatile and can be prepared in many ways.',
            'tips': 'Plant certified seed potatoes. Hill soil around plants as they grow. Keep tubers covered to prevent greening.'
        },
        'carrots': {
            'name': 'Carrots',
            'scientific_name': 'Daucus carota',
            'growing_season': 'Cool season',
            'days_to_maturity': '60-80 days',
            'optimal_temperature': '15-20°C',
            'water_needs': 'Moderate, consistent',
            'soil_ph': '6.0-6.8',
            'planting_depth': '0.5-1 cm',
            'row_spacing': '30-45 cm',
            'fertilizer_needs': 'Low nitrogen, balanced phosphorus and potassium',
            'common_pests': 'Carrot rust fly, aphids, nematodes',
            'diseases': 'Alternaria leaf blight, powdery mildew',
            'harvesting': 'When roots reach desired size',
            'description': 'Carrots are root vegetables known for their bright orange color and sweet flavor. They are rich in beta-carotene and other nutrients.',
            'tips': 'Grow in loose, stone-free soil for straight roots. Thin seedlings to prevent crowding. Keep soil consistently moist.'
        },
        'strawberries': {
            'name': 'Strawberries',
            'scientific_name': 'Fragaria × ananassa',
            'growing_season': 'Cool to warm season',
            'days_to_maturity': '90-110 days from planting to first harvest',
            'optimal_temperature': '15-26°C',
            'water_needs': 'Moderate, consistent',
            'soil_ph': '5.5-6.5',
            'planting_depth': 'Crown at soil level',
            'row_spacing': '30-45 cm',
            'fertilizer_needs': 'Balanced, higher in phosphorus and potassium',
            'common_pests': 'Slugs, strawberry crown borer, spider mites',
            'diseases': 'Gray mold, powdery mildew, leaf spot',
            'harvesting': 'When fruits are fully red with no white shoulders',
            'description': 'Strawberries are sweet, juicy fruits that are popular in home gardens. They can be grown as annuals or perennials depending on climate.',
            'tips': 'Mulch around plants to keep fruits clean and suppress weeds. Replace plants every 3-4 years for best production.'
        },
        'lettuce': {
            'name': 'Lettuce',
            'scientific_name': 'Lactuca sativa',
            'growing_season': 'Cool season',
            'days_to_maturity': '45-80 days',
            'optimal_temperature': '10-22°C',
            'water_needs': 'Moderate, consistent',
            'soil_ph': '6.0-7.0',
            'planting_depth': '0.5 cm',
            'row_spacing': '20-30 cm',
            'fertilizer_needs': 'Light, balanced fertilizer',
            'common_pests': 'Aphids, slugs, cutworms',
            'diseases': 'Downy mildew, lettuce drop, bottom rot',
            'harvesting': 'Leaf lettuce: outer leaves as needed; Head lettuce: when heads are firm',
            'description': 'Lettuce is a cool-season leafy vegetable that comes in many varieties, including loose-leaf, butterhead, romaine, and crisphead types.',
            'tips': 'Grow in spring and fall in warm climates. Provide afternoon shade in warm weather. Succession plant for continuous harvest.'
        }
    }
    
    # Normalize crop name for dictionary lookup
    normalized_crop_name = crop_name.lower().replace(' ', '_')
    
    # Get crop details or return a default message
    crop_info = crop_details_data.get(normalized_crop_name, {
        'name': crop_name,
        'description': 'Detailed information for this crop is not available yet.'
    })
    
    context = {
        'crop': crop_info
    }
    
    return render(request, 'crop_details.html', context)

@login_required(login_url='login')
def check_crop_soil_compatibility(request):
    """View to check compatibility between crops and soil types with crop management recommendations"""
    selected_crop = request.GET.get('crop_type', '')
    selected_soil = request.GET.get('soil_type', '')
    
    # Define crop-soil compatibility data
    crop_soil_compatibility = {
        'rice': {
            'clay': {'compatible': True, 'rating': 5, 'message': 'Rice thrives in clay soil due to its excellent water retention properties.', 'tips': 'Ensure proper drainage between growing seasons to prevent waterlogging.'},
            'loamy': {'compatible': True, 'rating': 4, 'message': 'Rice grows well in loamy soil with good water retention.', 'tips': 'Add organic matter to improve water retention if needed.'},
            'silty': {'compatible': True, 'rating': 4, 'message': 'Rice performs well in silty soil with its good moisture retention.', 'tips': 'Monitor water levels carefully as silty soil can drain faster than clay.'},
            'sandy': {'compatible': False, 'rating': 2, 'message': 'Sandy soil drains too quickly for rice cultivation.', 'tips': 'If you must grow rice in sandy soil, add clay and organic matter to improve water retention.', 'alternatives': ['Carrots', 'Potatoes', 'Radishes']},
            'peaty': {'compatible': False, 'rating': 2, 'message': 'Peaty soil is too acidic for optimal rice growth.', 'tips': 'Add lime to reduce acidity if you want to try growing rice.', 'alternatives': ['Root crops', 'Legumes']},
            'chalky': {'compatible': False, 'rating': 1, 'message': 'Chalky soil is too alkaline and drains too quickly for rice.', 'tips': 'Not recommended for rice cultivation.', 'alternatives': ['Cabbage', 'Spinach', 'Beets']}
        },
        'wheat': {
            'clay': {'compatible': True, 'rating': 4, 'message': 'Wheat grows well in clay soil with its good nutrient content.', 'tips': 'Ensure proper drainage to prevent waterlogging.'},
            'loamy': {'compatible': True, 'rating': 5, 'message': 'Loamy soil is ideal for wheat cultivation with balanced drainage and nutrients.', 'tips': 'Maintain organic matter content for optimal growth.'},
            'silty': {'compatible': True, 'rating': 4, 'message': 'Wheat performs well in silty soil with good moisture retention.', 'tips': 'Monitor moisture levels during dry periods.'},
            'sandy': {'compatible': False, 'rating': 2, 'message': 'Sandy soil lacks nutrients and moisture retention for wheat.', 'tips': 'Add organic matter and clay to improve soil quality if you want to grow wheat.', 'alternatives': ['Carrots', 'Potatoes', 'Radishes']},
            'peaty': {'compatible': False, 'rating': 2, 'message': 'Peaty soil is too acidic for optimal wheat growth.', 'tips': 'Add lime to reduce acidity if you want to try growing wheat.', 'alternatives': ['Root crops', 'Legumes']},
            'chalky': {'compatible': True, 'rating': 3, 'message': 'Wheat can grow in chalky soil but may need additional nutrients.', 'tips': 'Add organic matter and monitor nutrient levels.'}
        },
        'corn': {
            'clay': {'compatible': True, 'rating': 3, 'message': 'Corn can grow in clay soil but may face drainage issues.', 'tips': 'Improve drainage and add organic matter for better results.'},
            'loamy': {'compatible': True, 'rating': 5, 'message': 'Loamy soil is ideal for corn with balanced drainage and nutrients.', 'tips': 'Maintain organic matter content for optimal growth.'},
            'silty': {'compatible': True, 'rating': 4, 'message': 'Corn grows well in silty soil with good moisture retention.', 'tips': 'Monitor moisture levels during dry periods.'},
            'sandy': {'compatible': True, 'rating': 3, 'message': 'Corn can grow in sandy soil with proper fertilization and irrigation.', 'tips': 'Add organic matter and irrigate frequently.'},
            'peaty': {'compatible': False, 'rating': 2, 'message': 'Peaty soil is too acidic for optimal corn growth.', 'tips': 'Add lime to reduce acidity if you want to try growing corn.', 'alternatives': ['Root crops', 'Legumes']},
            'chalky': {'compatible': True, 'rating': 3, 'message': 'Corn can grow in chalky soil but may need additional nutrients.', 'tips': 'Add organic matter and monitor nutrient levels.'}
        },
        'tomatoes': {
            'clay': {'compatible': False, 'rating': 2, 'message': 'Clay soil can cause drainage issues for tomatoes.', 'tips': 'Add sand and organic matter to improve drainage if you want to grow tomatoes.', 'alternatives': ['Cabbage', 'Broccoli', 'Brussels Sprouts']},
            'loamy': {'compatible': True, 'rating': 5, 'message': 'Loamy soil is ideal for tomatoes with balanced drainage and nutrients.', 'tips': 'Maintain organic matter content for optimal growth.'},
            'silty': {'compatible': True, 'rating': 4, 'message': 'Tomatoes grow well in silty soil with good moisture retention.', 'tips': 'Monitor moisture levels to prevent overwatering.'},
            'sandy': {'compatible': True, 'rating': 3, 'message': 'Tomatoes can grow in sandy soil with proper fertilization and irrigation.', 'tips': 'Add organic matter and irrigate frequently.'},
            'peaty': {'compatible': False, 'rating': 2, 'message': 'Peaty soil is too acidic for optimal tomato growth.', 'tips': 'Add lime to reduce acidity if you want to try growing tomatoes.', 'alternatives': ['Root crops', 'Legumes']},
            'chalky': {'compatible': False, 'rating': 2, 'message': 'Chalky soil is too alkaline for tomatoes.', 'tips': 'Add sulfur to reduce alkalinity if you want to try growing tomatoes.', 'alternatives': ['Cabbage', 'Spinach', 'Beets']}
        },
        'potatoes': {
            'clay': {'compatible': False, 'rating': 2, 'message': 'Clay soil can restrict potato tuber growth.', 'tips': 'Add sand and organic matter to improve soil structure if you want to grow potatoes.', 'alternatives': ['Cabbage', 'Broccoli', 'Brussels Sprouts']},
            'loamy': {'compatible': True, 'rating': 5, 'message': 'Loamy soil is ideal for potatoes with balanced drainage and nutrients.', 'tips': 'Maintain organic matter content for optimal growth.'},
            'silty': {'compatible': True, 'rating': 4, 'message': 'Potatoes grow well in silty soil with good moisture retention.', 'tips': 'Monitor moisture levels to prevent overwatering.'},
            'sandy': {'compatible': True, 'rating': 4, 'message': 'Sandy soil is good for potatoes as it allows tubers to expand easily.', 'tips': 'Add organic matter and irrigate frequently.'},
            'peaty': {'compatible': True, 'rating': 3, 'message': 'Potatoes can grow in peaty soil but may need pH adjustment.', 'tips': 'Add lime to reduce acidity for better results.'},
            'chalky': {'compatible': False, 'rating': 2, 'message': 'Chalky soil is too alkaline for optimal potato growth.', 'tips': 'Add sulfur to reduce alkalinity if you want to try growing potatoes.', 'alternatives': ['Cabbage', 'Spinach', 'Beets']}
        },
        'carrots': {
            'clay': {'compatible': False, 'rating': 1, 'message': 'Clay soil restricts carrot root development.', 'tips': 'Not recommended for carrot cultivation.', 'alternatives': ['Cabbage', 'Broccoli', 'Brussels Sprouts']},
            'loamy': {'compatible': True, 'rating': 4, 'message': 'Loamy soil is good for carrots with balanced drainage and nutrients.', 'tips': 'Maintain organic matter content for optimal growth.'},
            'silty': {'compatible': True, 'rating': 3, 'message': 'Carrots can grow in silty soil but may develop forked roots.', 'tips': 'Loosen soil deeply before planting.'},
            'sandy': {'compatible': True, 'rating': 5, 'message': 'Sandy soil is ideal for carrots as it allows straight root development.', 'tips': 'Add organic matter and irrigate frequently.'},
            'peaty': {'compatible': True, 'rating': 3, 'message': 'Carrots can grow in peaty soil but may need pH adjustment.', 'tips': 'Add lime to reduce acidity for better results.'},
            'chalky': {'compatible': False, 'rating': 2, 'message': 'Chalky soil can cause stunted growth in carrots.', 'tips': 'Add organic matter if you want to try growing carrots.', 'alternatives': ['Cabbage', 'Spinach', 'Beets']}
        }
    }
    
    # Define soil management tasks
    soil_management_tasks = {
        'clay': [
            {'title': 'Add organic matter', 'description': 'Incorporate compost or well-rotted manure to improve soil structure and drainage.', 'priority': 'high'},
            {'title': 'Avoid working when wet', 'description': 'Clay soil becomes compacted when worked while wet. Wait until it\'s moderately dry.', 'priority': 'medium'},
            {'title': 'Mulch soil surface', 'description': 'Apply mulch to prevent surface crusting and improve water infiltration.', 'priority': 'medium'},
            {'title': 'Install drainage', 'description': 'Consider installing drainage systems if waterlogging is a persistent issue.', 'priority': 'high'}
        ],
        'sandy': [
            {'title': 'Add organic matter', 'description': 'Incorporate compost to improve water retention and nutrient-holding capacity.', 'priority': 'high'},
            {'title': 'Mulch heavily', 'description': 'Apply thick mulch to reduce water evaporation and soil temperature fluctuations.', 'priority': 'high'},
            {'title': 'Frequent irrigation', 'description': 'Set up a regular irrigation schedule as sandy soil drains quickly.', 'priority': 'high'},
            {'title': 'Add clay', 'description': 'Consider adding clay to improve water retention in garden beds.', 'priority': 'medium'}
        ],
        'loamy': [
            {'title': 'Maintain organic matter', 'description': 'Add compost annually to maintain the excellent structure of loamy soil.', 'priority': 'medium'},
            {'title': 'Crop rotation', 'description': 'Implement crop rotation to prevent nutrient depletion and pest buildup.', 'priority': 'medium'},
            {'title': 'Minimal tillage', 'description': 'Use minimal tillage methods to preserve soil structure.', 'priority': 'medium'}
        ],
        'silty': [
            {'title': 'Add organic matter', 'description': 'Incorporate compost to improve structure and prevent compaction.', 'priority': 'medium'},
            {'title': 'Avoid compaction', 'description': 'Avoid walking on silty soil when wet to prevent compaction.', 'priority': 'medium'},
            {'title': 'Mulch soil surface', 'description': 'Apply mulch to prevent erosion and crusting.', 'priority': 'medium'}
        ],
        'peaty': [
            {'title': 'Add lime', 'description': 'Apply lime to reduce acidity for most crops.', 'priority': 'high'},
            {'title': 'Improve drainage', 'description': 'Ensure proper drainage as peaty soils can become waterlogged.', 'priority': 'medium'},
            {'title': 'Add balanced fertilizers', 'description': 'Apply balanced fertilizers as peaty soils may lack certain nutrients.', 'priority': 'medium'}
        ],
        'chalky': [
            {'title': 'Add organic matter', 'description': 'Incorporate compost to improve water retention and nutrient availability.', 'priority': 'high'},
            {'title': 'Use acidic fertilizers', 'description': 'Apply acidic fertilizers for acid-loving plants.', 'priority': 'medium'},
            {'title': 'Mulch heavily', 'description': 'Apply thick mulch to reduce water evaporation.', 'priority': 'high'},
            {'title': 'Add sulfur', 'description': 'Consider adding sulfur to lower pH for certain crops.', 'priority': 'medium'}
        ]
    }
    
    # Get all crops and soil types for dropdowns
    all_crops = sorted(list(crop_soil_compatibility.keys()))
    all_soils = ['clay', 'sandy', 'loamy', 'silty', 'peaty', 'chalky']
    
    # Initialize variables
    compatibility_result = None
    crop_soils = None
    soil_crops = None
    management_tasks = None
    
    # Check if both crop and soil are selected
    if selected_crop and selected_soil:
        # Get compatibility data
        if selected_crop in crop_soil_compatibility and selected_soil in crop_soil_compatibility[selected_crop]:
            compatibility_result = crop_soil_compatibility[selected_crop][selected_soil]
            # Get management tasks for the selected soil
            management_tasks = soil_management_tasks.get(selected_soil, [])
    
    # If only crop is selected, show suitable soils
    elif selected_crop and selected_crop in crop_soil_compatibility:
        crop_soils = []
        for soil_type, data in crop_soil_compatibility[selected_crop].items():
            crop_soils.append({
                'type': soil_type,
                'suitability': 'excellent' if data['rating'] == 5 else 
                              'good' if data['rating'] == 4 else 
                              'fair' if data['rating'] == 3 else 'poor'
            })
        # Sort by suitability (excellent first, poor last)
        crop_soils.sort(key=lambda x: {'excellent': 0, 'good': 1, 'fair': 2, 'poor': 3}[x['suitability']])
    
    # If only soil is selected, show suitable crops and management tasks
    elif selected_soil:
        soil_crops = []
        for crop_name, soil_data in crop_soil_compatibility.items():
            if selected_soil in soil_data:
                data = soil_data[selected_soil]
                soil_crops.append({
                    'name': crop_name.title(),
                    'suitability': 'excellent' if data['rating'] == 5 else 
                                  'good' if data['rating'] == 4 else 
                                  'fair' if data['rating'] == 3 else 'poor'
                })
        # Sort by suitability (excellent first, poor last)
        soil_crops.sort(key=lambda x: {'excellent': 0, 'good': 1, 'fair': 2, 'poor': 3}[x['suitability']])
        
        # Get management tasks for the selected soil
        management_tasks = soil_management_tasks.get(selected_soil, [])
    
    # Get user's farms and fields for crop management
    user_farms = []
    if request.user.is_authenticated:
        from .models import Farm, Field
        farms = Farm.objects.filter(owner=request.user)
        for farm in farms:
            fields = Field.objects.filter(farm=farm)
            user_farms.append({
                'farm': farm,
                'fields': fields
            })
    
    context = {
        'selected_crop': selected_crop,
        'selected_soil': selected_soil,
        'all_crops': all_crops,
        'all_soils': all_soils,
        'compatibility_result': compatibility_result,
        'crop_soils': crop_soils,
        'soil_crops': soil_crops,
        'management_tasks': management_tasks,
        'user_farms': user_farms
    }
    
    return render(request, 'crop_soil_compatibility.html', context)

@login_required(login_url='login')
def farms(request):
    """View to display user's farms"""
    from .models import Farm
    farms = Farm.objects.filter(owner=request.user)
    return render(request, 'farms.html', {'farms': farms})

@login_required(login_url='login')
def add_farm(request):
    """View to add a new farm"""
    if request.method == 'POST':
        try:
            # Get form data
            name = request.POST.get('name')
            location = request.POST.get('location')
            size = request.POST.get('size')
            size_unit = request.POST.get('size_unit', 'acres')
            description = request.POST.get('description', '')
            
            # Validate required fields
            if not all([name, location, size]):
                messages.error(request, 'Please fill in all required fields')
                return render(request, 'add_farm.html')
            
            # Create new farm
            from .models import Farm
            farm = Farm(
                name=name,
                location=location,
                size=float(size),
                size_unit=size_unit,
                description=description,
                owner=request.user
            )
            farm.save()
            
            messages.success(request, f'Farm "{name}" added successfully')
            return redirect('farms')
            
        except Exception as e:
            messages.error(request, f'Error adding farm: {str(e)}')
            return render(request, 'add_farm.html')
    
    # If GET request, show the form
    return render(request, 'add_farm.html')

@login_required(login_url='login')
def add_task(request):
    """View to add a new task"""
    if request.method == 'POST':
        try:
            # Get form data
            farm_id = request.POST.get('farm_id')
            title = request.POST.get('title')
            description = request.POST.get('description')
            due_date = request.POST.get('due_date')
            priority = request.POST.get('priority', 'medium')
            
            # Validate required fields
            if not all([farm_id, title, due_date]):
                messages.error(request, 'Please fill in all required fields')
                return redirect(request.META.get('HTTP_REFERER', 'home'))
            
            # Create new task
            from .models import Farm, Task
            farm = Farm.objects.get(id=farm_id)
            
            task = Task(
                title=title,
                description=description,
                due_date=due_date,
                priority=priority,
                farm=farm,
                assigned_to=request.user,
                created_by=request.user,
                is_completed=False
            )
            task.save()
            
            messages.success(request, 'Task added successfully')
            
            # Redirect back to the referring page
            return redirect(request.META.get('HTTP_REFERER', 'home'))
            
        except Exception as e:
            messages.error(request, f'Error adding task: {str(e)}')
            return redirect(request.META.get('HTTP_REFERER', 'home'))
    
    # If not POST, redirect to home
    return redirect('home')

@login_required
def profile(request):
    """
    View to display and update user profile
    """
    user = request.user
    
    if request.method == 'POST':
        # Update profile information
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        phone_number = request.POST.get('phone_number')
        address = request.POST.get('address')
        
        if first_name:
            user.first_name = first_name
        if last_name:
            user.last_name = last_name
        if phone_number:
            user.phone_number = phone_number
        if address:
            user.address = address
            
        # Handle profile picture upload
        if 'profile_picture' in request.FILES:
            # For now, we'll just store the filename since we're using CharField
            user.profile_picture = request.FILES['profile_picture'].name
            
        user.save()
        messages.success(request, 'Profile updated successfully!')
        return redirect('profile')
    
    context = {
        'user': user,
    }
    return render(request, 'profile.html', context)

@csrf_exempt
def test_sensor_data(request):
    """
    Test endpoint for sensor data operations
    """
    if request.method == 'POST':
        try:
            # Create a test sensor reading
            data = json.loads(request.body)
            sensor_data = SensorData.objects.create(
                sensor_id=data.get('sensor_id', 'test_sensor'),
                sensor_type=data.get('sensor_type', 'temperature'),
                value=data.get('value', 25.5),
                unit=data.get('unit', '°C'),
                location=data.get('location', 'test_location'),
                metadata=data.get('metadata', {})
            )
            return JsonResponse({
                'status': 'success',
                'message': 'Sensor data created successfully',
                'data': {
                    'sensor_id': sensor_data.sensor_id,
                    'value': sensor_data.value,
                    'unit': sensor_data.unit,
                    'timestamp': sensor_data.timestamp.isoformat()
                }
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)
    
    elif request.method == 'GET':
        try:
            # Get latest sensor readings
            latest_readings = SensorData.objects.all().order_by('-timestamp')[:5]
            data = [{
                'sensor_id': reading.sensor_id,
                'sensor_type': reading.sensor_type,
                'value': reading.value,
                'unit': reading.unit,
                'timestamp': reading.timestamp.isoformat(),
                'location': reading.location
            } for reading in latest_readings]
            
            return JsonResponse({
                'status': 'success',
                'data': data
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)
    
    return JsonResponse({
        'status': 'error',
        'message': 'Method not allowed'
    }, status=405)