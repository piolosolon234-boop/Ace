import os

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'bus-booking-school-project-2024')
    SESSION_TYPE = 'filesystem'
    
    # Database configuration (XAMPP default)
    DB_CONFIG = {
        'host': 'localhost',
        'user': 'root',
        'password': '',
        'database': 'bus_booking_system',
        'port': 3306
    }
    
    # Offline storage
    OFFLINE_DATA_DIR = 'database/offline_data'