from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import CustomUser, Farm, Field, Crop, Sensor, SensorReading, WeatherData, IrrigationSchedule, Task

# Create a custom admin class for Task model
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'farm', 'due_date', 'priority', 'is_completed', 'assigned_to')
    list_filter = ('is_completed', 'priority', 'due_date')
    search_fields = ('title', 'description')
    date_hierarchy = 'due_date'

# Register models with default admin site
admin.site.register(CustomUser, UserAdmin)
admin.site.register(Farm)
admin.site.register(Field)
admin.site.register(Crop)
admin.site.register(Sensor)
admin.site.register(SensorReading)
admin.site.register(WeatherData)
admin.site.register(IrrigationSchedule)
admin.site.register(Task, TaskAdmin)  # Register with custom admin class
