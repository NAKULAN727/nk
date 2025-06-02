from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('signup/', views.signup, name='signup'),
    path('profile/', views.profile, name='profile'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('change-language/', views.change_language, name='change_language'),
    path('update-sensor-data/', views.update_sensor_data, name='update_sensor_data'),
    path('soil-crop-recommendations/', views.soil_crop_recommendations, name='soil_crop_recommendations'),
    path('crop-details/<str:crop_name>/', views.crop_details, name='crop_details'),
    path('api/get-weather-alert/', views.get_weather_alert, name='get_weather_alert'),
    path('api/get-weather-forecast/', views.get_weather_forecast, name='get_weather_forecast'),
    path('api/schedule-irrigation/', views.schedule_irrigation, name='schedule_irrigation'),
    path('crop-soil-compatibility/', views.check_crop_soil_compatibility, name='crop_soil_compatibility'),
    path('add-task/', views.add_task, name='add_task'),
    path('farms/', views.farms, name='farms'),
    path('add-farm/', views.add_farm, name='add_farm'),
    path('manage-crops/', views.manage_crops, name='manage_crops'),
]
