from django.db import migrations

def add_default_settings(apps, schema_editor):
    Settings = apps.get_model('core', 'Settings')
    default_settings = [
        # General Settings
        {'name': 'business_name', 'value': 'Upendo Bakery', 'setting_type': 'general', 
         'description': 'Name of your business'},
        {'name': 'business_address', 'value': '', 'setting_type': 'general',
         'description': 'Business address'},
        {'name': 'business_phone', 'value': '', 'setting_type': 'general',
         'description': 'Business phone number'},
        {'name': 'business_email', 'value': '', 'setting_type': 'general',
         'description': 'Business email address'},
        
        # Appearance Settings
        {'name': 'primary_color', 'value': '#007bff', 'setting_type': 'appearance',
         'description': 'Primary color for the system (hex code)'},
        {'name': 'secondary_color', 'value': '#6c757d', 'setting_type': 'appearance',
         'description': 'Secondary color for the system (hex code)'},
        {'name': 'accent_color', 'value': '#28a745', 'setting_type': 'appearance',
         'description': 'Accent color for the system (hex code)'},
        {'name': 'logo', 'value': '', 'setting_type': 'appearance',
         'description': 'URL to your business logo'},
        
        # System Settings
        {'name': 'currency', 'value': 'KES', 'setting_type': 'system',
         'description': 'Currency code (e.g., KES, USD)'},
        {'name': 'timezone', 'value': 'Africa/Nairobi', 'setting_type': 'system',
         'description': 'System timezone'},
        {'name': 'date_format', 'value': 'DD/MM/YYYY', 'setting_type': 'system',
         'description': 'Date format'},
        {'name': 'time_format', 'value': '24', 'setting_type': 'system',
         'description': 'Time format (12 or 24 hour)'},
        
        # Notification Settings
        {'name': 'low_stock_alert', 'value': 'true', 'setting_type': 'notification',
         'description': 'Enable low stock alerts'},
        {'name': 'email_notifications', 'value': 'false', 'setting_type': 'notification',
         'description': 'Enable email notifications'},
        {'name': 'notification_email', 'value': '', 'setting_type': 'notification',
         'description': 'Email address for notifications'},
        
        # Payment Settings
        {'name': 'enable_mpesa', 'value': 'true', 'setting_type': 'payment',
         'description': 'Enable M-Pesa payments'},
        {'name': 'enable_cash', 'value': 'true', 'setting_type': 'payment',
         'description': 'Enable cash payments'},
        {'name': 'enable_card', 'value': 'false', 'setting_type': 'payment',
         'description': 'Enable card payments'},
    ]
    
    for setting_data in default_settings:
        Settings.objects.get_or_create(
            name=setting_data['name'],
            defaults={
                'value': setting_data['value'],
                'setting_type': setting_data['setting_type'],
                'description': setting_data['description']
            }
        )

def remove_default_settings(apps, schema_editor):
    Settings = apps.get_model('core', 'Settings')
    Settings.objects.all().delete()

class Migration(migrations.Migration):
    dependencies = [
        ('core', '0017_settings'),
    ]

    operations = [
        migrations.RunPython(add_default_settings, remove_default_settings),
    ] 