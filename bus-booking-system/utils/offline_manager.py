import json
import os
import uuid
from datetime import datetime
import hashlib

class OfflineManager:
    def __init__(self):
        self.offline_dir = "database/offline_data"
        self.ensure_directories()
    
    def ensure_directories(self):
        """Create necessary directories for offline storage"""
        os.makedirs(f"{self.offline_dir}/users", exist_ok=True)
        os.makedirs(f"{self.offline_dir}/bookings", exist_ok=True)
        os.makedirs(f"{self.offline_dir}/schedules", exist_ok=True)
    
    def hash_password(self, password):
        """Consistent password hashing with database handler"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def save_user_offline(self, user_data):
        """Save user registration data offline"""
        try:
            # Generate unique filename
            filename = f"{user_data['offline_id']}.json"
            filepath = f"{self.offline_dir}/users/{filename}"
            
            # Ensure all required fields
            user_data.setdefault('created_at', datetime.now().isoformat())
            user_data.setdefault('is_admin', False)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(user_data, f, indent=2, ensure_ascii=False)
            
            print(f"Saved offline user: {user_data['username']}")
            return True
            
        except Exception as e:
            print(f"Save user offline error: {e}")
            return False
    
    def authenticate_offline(self, username, password):
        """Authenticate user from offline storage"""
        try:
            users_dir = f"{self.offline_dir}/users"
            if not os.path.exists(users_dir):
                return None
            
            for filename in os.listdir(users_dir):
                if filename.endswith('.json'):
                    filepath = f"{users_dir}/{filename}"
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            user = json.load(f)
                        
                        # Simple password check (in production, use hashing)
                        if user['username'] == username and user['password'] == password:
                            return user
                    except (json.JSONDecodeError, KeyError) as e:
                        print(f"Error reading user file {filename}: {e}")
                        continue
            
            return None
            
        except Exception as e:
            print(f"Offline auth error: {e}")
            return None
    
    def save_booking_offline(self, booking_data):
        """Save booking data offline"""
        try:
            # Generate unique filename
            filename = f"{booking_data['offline_id']}.json"
            filepath = f"{self.offline_dir}/bookings/{filename}"
            
            # Ensure all required fields
            booking_data.setdefault('booking_status', 'Pending Sync')
            booking_data.setdefault('is_synced', False)
            booking_data.setdefault('booking_date', datetime.now().isoformat())
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(booking_data, f, indent=2, ensure_ascii=False)
            
            print(f"Saved offline booking: {booking_data['booking_reference']}")
            return True
            
        except Exception as e:
            print(f"Save booking offline error: {e}")
            return False
    
    def get_user_offline_bookings(self, username):
        """Get offline bookings for a user"""
        bookings = []
        try:
            bookings_dir = f"{self.offline_dir}/bookings"
            if not os.path.exists(bookings_dir):
                return bookings
            
            for filename in os.listdir(bookings_dir):
                if filename.endswith('.json'):
                    filepath = f"{bookings_dir}/{filename}"
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            booking = json.load(f)
                        
                        # Check if booking belongs to this user
                        if booking.get('username') == username:
                            # Format for display
                            formatted_booking = {
                                'booking_reference': booking['booking_reference'],
                                'passenger_name': booking['passenger_name'],
                                'booking_date': booking['booking_date'],
                                'total_fare': booking.get('total_fare', 50),
                                'booking_status': 'Pending Sync',
                                'is_offline': True,
                                'seat_count': booking.get('seat_count', 1),
                                'schedule_data': booking.get('schedule_data', {})
                            }
                            bookings.append(formatted_booking)
                            
                    except (json.JSONDecodeError, KeyError) as e:
                        print(f"Error reading booking file {filename}: {e}")
                        continue
            
            return bookings
            
        except Exception as e:
            print(f"Get offline bookings error: {e}")
            return []
    
    def search_schedules_offline(self, origin, destination, travel_date):
        """Search schedules from cached offline data"""
        try:
            cache_file = f"{self.offline_dir}/schedules/cache.json"
            if not os.path.exists(cache_file):
                # Return sample data if cache doesn't exist
                return self.get_sample_schedules(origin, destination, travel_date)
            
            with open(cache_file, 'r', encoding='utf-8') as f:
                all_schedules = json.load(f)
            
            # Filter schedules
            filtered_schedules = []
            origin_lower = origin.lower()
            destination_lower = destination.lower()
            
            for schedule in all_schedules:
                schedule_origin = schedule.get('origin_city', '').lower()
                schedule_dest = schedule.get('destination_city', '').lower()
                schedule_date = schedule.get('travel_date', '')
                
                if (origin_lower in schedule_origin and 
                    destination_lower in schedule_dest and 
                    schedule_date == travel_date):
                    filtered_schedules.append(schedule)
            
            return filtered_schedules
            
        except Exception as e:
            print(f"Offline search error: {e}")
            return self.get_sample_schedules(origin, destination, travel_date)
    
    def get_sample_schedules(self, origin, destination, travel_date):
        """Return sample schedules for offline mode"""
        sample_schedules = [
            {
                'schedule_id': 1,
                'route_id': 1,
                'route_name': f'{origin} to {destination} Express',
                'origin_city': origin,
                'destination_city': destination,
                'bus_number': 'BUS-001',
                'departure_time': '08:00:00',
                'arrival_time': '12:00:00',
                'travel_date': travel_date,
                'total_seats': 40,
                'available_seats': 20,
                'fare': 50.00,
                'estimated_duration_hours': 4.0
            },
            {
                'schedule_id': 2,
                'route_id': 1,
                'route_name': f'{origin} to {destination} Deluxe',
                'origin_city': origin,
                'destination_city': destination,
                'bus_number': 'BUS-002',
                'departure_time': '14:00:00',
                'arrival_time': '18:30:00',
                'travel_date': travel_date,
                'total_seats': 40,
                'available_seats': 15,
                'fare': 65.00,
                'estimated_duration_hours': 4.5
            }
        ]
        return sample_schedules
    
    def get_schedule_offline(self, schedule_id):
        """Get a specific schedule from cache or sample data"""
        try:
            cache_file = f"{self.offline_dir}/schedules/cache.json"
            if os.path.exists(cache_file):
                with open(cache_file, 'r', encoding='utf-8') as f:
                    all_schedules = json.load(f)
                
                for schedule in all_schedules:
                    if schedule.get('schedule_id') == schedule_id:
                        return schedule
            
            # Return sample schedule if not found in cache
            return {
                'schedule_id': schedule_id,
                'route_id': 1,
                'route_name': 'Sample Route',
                'origin_city': 'Sample City',
                'destination_city': 'Destination City',
                'bus_number': 'BUS-SAMPLE',
                'departure_time': '10:00:00',
                'arrival_time': '14:00:00',
                'travel_date': datetime.now().date().isoformat(),
                'total_seats': 40,
                'available_seats': 30,
                'fare': 50.00
            }
            
        except Exception as e:
            print(f"Get schedule offline error: {e}")
            return None
    
    def get_cached_schedules(self):
        """Get all cached schedules"""
        try:
            cache_file = f"{self.offline_dir}/schedules/cache.json"
            if os.path.exists(cache_file):
                with open(cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return []
        except Exception as e:
            print(f"Get cached schedules error: {e}")
            return []
    
    def get_pending_sync_count(self):
        """Count pending sync items"""
        try:
            count = 0
            
            # Count pending users
            users_dir = f"{self.offline_dir}/users"
            if os.path.exists(users_dir):
                count += len([f for f in os.listdir(users_dir) if f.endswith('.json')])
            
            # Count pending bookings
            bookings_dir = f"{self.offline_dir}/bookings"
            if os.path.exists(bookings_dir):
                count += len([f for f in os.listdir(bookings_dir) if f.endswith('.json')])
            
            return count
            
        except Exception as e:
            print(f"Get pending sync count error: {e}")
            return 0