from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from flask_session import Session
from datetime import datetime, date, timedelta
import uuid
import json
import os
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)
app.secret_key = 'philippine-bus-booking-2024-system'
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

class DatabaseHandler:
    def __init__(self):
        self.config = {
            'host': 'localhost',
            'user': 'root',
            'password': '',
            'database': 'bus_booking_system',
            'port': 3306,
            'charset': 'utf8mb4'
        }
        self.connection = None
    
    def get_connection(self):
        """Establish database connection"""
        try:
            self.connection = mysql.connector.connect(**self.config)
            return self.connection
        except Error as e:
            print(f"Database connection error: {e}")
            return None
    
    def check_connection(self):
        """Check if MySQL is accessible"""
        try:
            conn = self.get_connection()
            if conn and conn.is_connected():
                conn.close()
                return True
        except:
            pass
        return False
    
    def hash_password(self, password):
        """Simple password hashing"""
        import hashlib
        return hashlib.sha256(password.encode()).hexdigest()
    
    def execute_query(self, cursor, query, params=None, description=""):
        """Debug wrapper for execute"""
        print(f"\n🔍 Executing {description}:")
        print(f"   Query: {query}")
        if params:
            print(f"   Params: {params}")
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
        except Error as e:
            print(f"❌ ERROR in {description}: {e}")
            raise e

    # Then update your methods to use it. For example, in get_admin_stats:

    def get_admin_stats(self):
        """Get statistics for admin panel - DEBUG VERSION"""
        conn = self.get_connection()
        if not conn:
            return self.get_sample_admin_stats()
        
        try:
            cursor = conn.cursor(dictionary=True)
            stats = {}
            
            # Total bookings
            self.execute_query(cursor, "SELECT COUNT(*) as total FROM bookings", description="total_bookings")
            stats['total_bookings'] = cursor.fetchone()['total']
            
            # Total users
            self.execute_query(cursor, "SELECT COUNT(*) as total FROM users", description="total_users")
            stats['total_users'] = cursor.fetchone()['total']
            
            # Today's bookings
            self.execute_query(cursor, """
                SELECT COUNT(*) as total FROM bookings 
                WHERE DATE(booking_date) = CURDATE()
            """, description="today_bookings")
            stats['today_bookings'] = cursor.fetchone()['total']
            
            # Total revenue
            self.execute_query(cursor, """
                SELECT COALESCE(SUM(total_fare), 0) as revenue 
                FROM bookings 
                WHERE booking_status = 'Confirmed'
            """, description="revenue")
            stats['revenue'] = float(cursor.fetchone()['revenue'])
            
            # Available schedules
            self.execute_query(cursor, """
                SELECT COUNT(*) as total FROM bus_schedules 
                WHERE travel_date >= CURDATE()
            """, description="active_schedules")
            stats['active_schedules'] = cursor.fetchone()['total']
            
            # Recent bookings - THIS IS THE CRITICAL ONE
            recent_query = """
                SELECT b.booking_reference, u.username, 
                    CONCAT(u.first_name, ' ', u.last_name) as passenger_name, 
                    b.total_fare, b.booking_date
                FROM bookings b
                JOIN users u ON b.user_id = u.user_id
                ORDER BY b.booking_date DESC
                LIMIT 5
            """
            self.execute_query(cursor, recent_query, description="recent_bookings")
            stats['recent_bookings'] = cursor.fetchall()
            
            # Format dates
            for booking in stats['recent_bookings']:
                if 'booking_date' in booking and booking['booking_date']:
                    if hasattr(booking['booking_date'], 'isoformat'):
                        booking['booking_date'] = booking['booking_date'].isoformat()
            
            return stats
            
        except Error as e:
            print(f"❌ Stats error: {e}")
            return self.get_sample_admin_stats()
        finally:
            if conn:
                conn.close()

    def register_user(self, username, email, password, full_name, phone=None):
        """Register new user - FIXED to match database structure"""
        conn = self.get_connection()
        if not conn:
            return {'success': False, 'message': 'Database not connected'}
        
        try:
            cursor = conn.cursor()
            hashed_pw = self.hash_password(password)
            
            # Split full_name into first and last name
            name_parts = full_name.strip().split(' ', 1)
            first_name = name_parts[0]
            last_name = name_parts[1] if len(name_parts) > 1 else ''
            
            # Use default location IDs (Manila)
            query = """
            INSERT INTO users (
                username, email, password_hash, first_name, last_name, 
                phone, city_muni_id, province_id, region_id
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            cursor.execute(query, (
                username, email, hashed_pw, first_name, last_name, 
                phone, 1, 1, 1  # Default to Manila, Metro Manila, NCR
            ))
            
            conn.commit()
            return {'success': True, 'user_id': cursor.lastrowid}
            
        except Error as e:
            if 'Duplicate entry' in str(e):
                return {'success': False, 'message': 'Username or email already exists'}
            print(f"Registration error: {e}")
            return {'success': False, 'message': str(e)}
        finally:
            if conn:
                conn.close()
    
    def authenticate_user(self, username, password):
        """Authenticate user login"""
        conn = self.get_connection()
        if not conn:
            # Return test user for demo when database is not connected
            if username == 'admin' and password == 'admin123':
                return {
                    'user_id': 1, 
                    'username': 'admin', 
                    'full_name': 'Admin User',
                    'is_admin': True
                }
            # Check offline users in database when connected but no connection?
            return None
        
        try:
            cursor = conn.cursor(dictionary=True)
            hashed_pw = self.hash_password(password)
            
            query = """
            SELECT 
                user_id, username, email, 
                CONCAT(first_name, ' ', last_name) as full_name,
                is_admin 
            FROM users 
            WHERE username = %s AND password_hash = %s
            """
            
            cursor.execute(query, (username, hashed_pw))
            user = cursor.fetchone()
            
            # If user not found, check if it's the admin with default credentials
            if not user and username == 'admin' and password == 'admin123':
                return {
                    'user_id': 1, 
                    'username': 'admin', 
                    'full_name': 'Admin User',
                    'is_admin': True
                }
                
            return user
            
        except Error as e:
            print(f"Authentication error: {e}")
            # Fallback to admin if database error
            if username == 'admin' and password == 'admin123':
                return {
                    'user_id': 1, 
                    'username': 'admin', 
                    'full_name': 'Admin User',
                    'is_admin': True
                }
            return None
        finally:
            if conn:
                conn.close()
    
    def search_schedules(self, origin, destination, travel_date):
        """Search for bus schedules"""
        conn = self.get_connection()
        if not conn:
            return self.get_sample_schedules(origin, destination, travel_date)
        
        try:
            cursor = conn.cursor(dictionary=True)
            
            # First, check what dates have schedules
            cursor.execute("SELECT DISTINCT travel_date FROM bus_schedules ORDER BY travel_date LIMIT 5")
            available_dates = cursor.fetchall()
            print(f"📅 Available dates in DB: {[d['travel_date'] for d in available_dates]}")
            
            query = """
            SELECT 
                s.schedule_id,
                s.bus_number,
                TIME_FORMAT(s.departure_time, '%H:%i') as departure_time,
                TIME_FORMAT(s.arrival_time, '%H:%i') as arrival_time,
                s.travel_date,
                s.total_seats,
                s.available_seats,
                s.fare,
                s.bus_operator,
                s.bus_type,
                s.amenities,
                r.route_name,
                o.name as origin_city,
                d.name as destination_city,
                r.distance_km,
                r.estimated_hours,
                r.estimated_hours as estimated_duration_hours,
                r.route_type,
                r.via_route
            FROM bus_schedules s
            JOIN bus_routes r ON s.route_id = r.route_id
            JOIN cities_municipalities o ON r.origin_city_muni_id = o.city_muni_id
            JOIN cities_municipalities d ON r.destination_city_muni_id = d.city_muni_id
            WHERE (o.name LIKE %s OR %s = '')
            AND (d.name LIKE %s OR %s = '')
            AND s.travel_date >= CURDATE()  /* Show future dates */
            AND s.available_seats > 0
            ORDER BY s.travel_date, s.departure_time
            LIMIT 20
            """
            
            origin_pattern = f"%{origin}%" if origin else "%"
            dest_pattern = f"%{destination}%" if destination else "%"
            
            cursor.execute(query, (
                origin_pattern, origin_pattern,
                dest_pattern, dest_pattern
            ))
            
            schedules = cursor.fetchall()
            print(f"   Found {len(schedules)} schedules for future dates")
            
            # Format the results
            for schedule in schedules:
                if 'travel_date' in schedule and schedule['travel_date']:
                    if hasattr(schedule['travel_date'], 'isoformat'):
                        schedule['travel_date'] = schedule['travel_date'].isoformat()
                if 'amenities' in schedule and schedule['amenities']:
                    schedule['amenities_list'] = schedule['amenities'].split(', ')
            
            return schedules
            
        except Error as e:
            print(f"❌ Search error: {e}")
            return self.get_sample_schedules(origin, destination, travel_date)
        finally:
            if conn:
                conn.close()
                
    def get_sample_schedules(self, origin, destination, travel_date):
        """Return sample schedules when database is not connected"""
        # Sample Philippine routes
        sample_routes = [
            {
                'schedule_id': 101,
                'bus_number': 'PHB-SAMPLE-001',
                'departure_time': '08:00',
                'arrival_time': '14:00',
                'travel_date': travel_date if travel_date else date.today().isoformat(),
                'total_seats': 45,
                'available_seats': 25,
                'fare': 850.00,
                'bus_operator': 'Victory Liner',
                'bus_type': 'Deluxe',
                'amenities': 'Aircon, TV, Reclining Seats',
                'route_name': f'{origin if origin else "Manila"} to {destination if destination else "Baguio"} Express',
                'origin_city': origin if origin else 'Manila',
                'destination_city': destination if destination else 'Baguio',
                'distance_km': 250,
                'estimated_hours': 6,
                'estimated_duration_hours': 6,
                'route_type': 'Deluxe',
                'via_route': 'NLEX, SCTEX',
                'amenities_list': ['Aircon', 'TV', 'Reclining Seats']
            },
            {
                'schedule_id': 102,
                'bus_number': 'PHZM-SAMPLE-001',
                'departure_time': '20:00',
                'arrival_time': '02:00',
                'travel_date': travel_date if travel_date else date.today().isoformat(),
                'total_seats': 45,
                'available_seats': 18,
                'fare': 2200.00,
                'bus_operator': 'RORO Bus',
                'bus_type': 'Premium',
                'amenities': 'Aircon, Bunks, Toilet, Meal',
                'route_name': 'Zamboanga to Manila (RORO)',
                'origin_city': 'Zamboanga City',
                'destination_city': 'Manila',
                'distance_km': 1100,
                'estimated_hours': 30,
                'estimated_duration_hours': 30,
                'route_type': 'Premium',
                'via_route': 'RORO via Cebu',
                'amenities_list': ['Aircon', 'Bunks', 'Toilet', 'Meal']
            }
        ]
        return sample_routes
    
    def get_schedule_details(self, schedule_id):
        """Get details for a specific schedule"""
        conn = self.get_connection()
        if not conn:
            return self.get_sample_schedule_details(schedule_id)
        
        try:
            cursor = conn.cursor(dictionary=True)
            
            query = """
            SELECT 
                s.*,
                r.route_name,
                o.name as origin_city,
                d.name as destination_city,
                r.distance_km,
                r.estimated_hours,
                r.route_type,
                r.via_route
            FROM bus_schedules s
            JOIN bus_routes r ON s.route_id = r.route_id
            JOIN cities_municipalities o ON r.origin_city_muni_id = o.city_muni_id
            JOIN cities_municipalities d ON r.destination_city_muni_id = d.city_muni_id
            WHERE s.schedule_id = %s
            """
            
            cursor.execute(query, (schedule_id,))
            schedule = cursor.fetchone()
            
            if schedule:
                if 'travel_date' in schedule and schedule['travel_date']:
                    if hasattr(schedule['travel_date'], 'isoformat'):
                        schedule['travel_date'] = schedule['travel_date'].isoformat()
                if 'amenities' in schedule and schedule['amenities']:
                    schedule['amenities_list'] = schedule['amenities'].split(', ')
            
            return schedule
            
        except Error as e:
            print(f"Get schedule error: {e}")
            return self.get_sample_schedule_details(schedule_id)
        finally:
            if conn:
                conn.close()
    
    def get_sample_schedule_details(self, schedule_id):
        """Sample schedule details for demo"""
        return {
            'schedule_id': schedule_id,
            'bus_number': f'PHB-{schedule_id:03d}',
            'departure_time': '20:00:00',
            'arrival_time': '08:00:00',
            'travel_date': date.today().isoformat(),
            'total_seats': 45,
            'available_seats': 25,
            'fare': 2200.00,
            'bus_operator': 'RORO Bus',
            'bus_type': 'Premium',
            'amenities': 'Aircon, Bunks, Toilet, Meal, WiFi',
            'route_name': 'Zamboanga to Manila Express',
            'origin_city': 'Zamboanga City',
            'destination_city': 'Manila',
            'distance_km': 1100,
            'estimated_hours': 30,
            'route_type': 'Premium',
            'via_route': 'RORO via Cebu',
            'amenities_list': ['Aircon', 'Bunks', 'Toilet', 'Meal', 'WiFi']
        }
    
    def create_booking(self, user_id, schedule_id, passenger_name, 
                    passenger_age, passenger_gender, seat_count, booking_ref):
        """Create a new booking"""
        conn = self.get_connection()
        if not conn:
            return {'success': False, 'message': 'Database not connected'}
        
        try:
            cursor = conn.cursor(dictionary=True)
            
            # Check seat availability
            cursor.execute(
                "SELECT available_seats, fare FROM bus_schedules WHERE schedule_id = %s FOR UPDATE",
                (schedule_id,)
            )
            schedule = cursor.fetchone()
            
            if not schedule:
                return {'success': False, 'message': 'Schedule not found'}
            
            if schedule['available_seats'] < seat_count:
                return {'success': False, 'message': 'Not enough seats available'}
            
            # Calculate total fare
            total_fare = schedule['fare'] * seat_count
            
            # Generate seat numbers
            seat_numbers = ", ".join([f"Seat-{i+1}" for i in range(seat_count)])
            
            # First, let's check what columns actually exist in the bookings table
            cursor.execute("SHOW COLUMNS FROM bookings")
            columns = [col['Field'] for col in cursor.fetchall()]
            print("Available columns in bookings table:", columns)
            
            # Build the INSERT query based on actual columns
            if 'passenger_name' in columns:
                # Your current table structure
                booking_query = """
                INSERT INTO bookings 
                (user_id, schedule_id, booking_reference, passenger_name, passenger_age, 
                passenger_gender, seat_numbers, total_fare, booking_status, payment_status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                
                cursor.execute(booking_query, (
                    user_id, schedule_id, booking_ref, passenger_name, passenger_age,
                    passenger_gender, seat_numbers, total_fare, 'Confirmed', 'Pending'
                ))
            else:
                # Try alternative column names
                booking_query = """
                INSERT INTO bookings 
                (user_id, schedule_id, booking_reference, passenger_first_name, passenger_last_name,
                passenger_age, passenger_gender, seat_numbers, number_of_seats, total_fare, 
                booking_status, payment_status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                
                # Split passenger name into first and last
                name_parts = passenger_name.split(' ', 1)
                first_name = name_parts[0]
                last_name = name_parts[1] if len(name_parts) > 1 else ''
                
                cursor.execute(booking_query, (
                    user_id, schedule_id, booking_ref, first_name, last_name,
                    passenger_age, passenger_gender, seat_numbers, seat_count, total_fare,
                    'Confirmed', 'Pending'
                ))
            
            # Update available seats
            cursor.execute(
                "UPDATE bus_schedules SET available_seats = available_seats - %s WHERE schedule_id = %s",
                (seat_count, schedule_id)
            )
            
            conn.commit()
            return {
                'success': True, 
                'booking_ref': booking_ref, 
                'total_fare': total_fare,
                'booking_id': cursor.lastrowid,
                'message': 'Booking confirmed successfully!'
            }
            
        except Error as e:
            if conn:
                conn.rollback()
            print(f"Booking error: {e}")
            return {'success': False, 'message': f'Booking failed: {str(e)}'}
        finally:
            if conn:
                conn.close()
    
    def get_user_bookings(self, user_id):
        """Get all bookings for a user"""
        conn = self.get_connection()
        if not conn:
            return self.get_sample_bookings(user_id)
        
        try:
            cursor = conn.cursor(dictionary=True)
            
            # Simplified query that doesn't rely on bus_routes table
            query = """
            SELECT 
                b.booking_reference,
                b.passenger_name,
                b.booking_date,
                b.total_fare,
                b.booking_status,
                b.payment_status,
                b.seat_numbers,
                b.number_of_seats,
                s.bus_number,
                s.departure_time,
                s.arrival_time,
                s.travel_date,
                s.fare as seat_fare,
                s.bus_operator,
                s.bus_type,
                'Bus Schedule' as route_name,
                'Origin' as origin_city,
                'Destination' as destination_city
            FROM bookings b
            LEFT JOIN bus_schedules s ON b.schedule_id = s.schedule_id
            WHERE b.user_id = %s
            ORDER BY b.booking_date DESC
            """
            
            cursor.execute(query, (user_id,))
            bookings = cursor.fetchall()
            
            # Format dates and add missing fields
            for booking in bookings:
                if booking.get('booking_date'):
                    if hasattr(booking['booking_date'], 'isoformat'):
                        booking['booking_date'] = booking['booking_date'].isoformat()
                
                if booking.get('travel_date'):
                    if hasattr(booking['travel_date'], 'isoformat'):
                        booking['travel_date'] = booking['travel_date'].isoformat()
                
                # Add default values for template
                booking['is_offline'] = False
                if not booking.get('route_name'):
                    booking['route_name'] = f"{booking.get('origin_city', 'Unknown')} to {booking.get('destination_city', 'Unknown')}"
            
            return bookings
            
        except Error as e:
            print(f"Get bookings error: {e}")
            return self.get_sample_bookings(user_id)
        finally:
            if conn:
                conn.close()

    def get_sample_bookings(self, user_id):
        """Sample bookings for demo"""
        return [
            {
                'booking_reference': 'BKP202412001',
                'passenger_name': 'Juan Dela Cruz',
                'booking_date': '2024-12-01 10:30:00',
                'total_fare': 2200.00,
                'booking_status': 'Confirmed',
                'payment_status': 'Paid',
                'bus_number': 'PHZM-001',
                'departure_time': '20:00:00',
                'travel_date': date.today().isoformat(),
                'route_name': 'Zamboanga to Manila',
                'origin_city': 'Zamboanga City',
                'destination_city': 'Manila',
                'seat_numbers': 'Seat-10, Seat-11',
                'is_offline': False
            }
        ]
    
    def get_admin_stats(self):
        """Get statistics for admin panel"""
        conn = self.get_connection()
        if not conn:
            return self.get_sample_admin_stats()
        
        try:
            cursor = conn.cursor(dictionary=True)
            stats = {}
            
            # Total bookings
            cursor.execute("SELECT COUNT(*) as total FROM bookings")
            stats['total_bookings'] = cursor.fetchone()['total']
            
            # Total users
            cursor.execute("SELECT COUNT(*) as total FROM users")
            stats['total_users'] = cursor.fetchone()['total']
            
            # Today's bookings
            cursor.execute("""
                SELECT COUNT(*) as total FROM bookings 
                WHERE DATE(booking_date) = CURDATE()
            """)
            stats['today_bookings'] = cursor.fetchone()['total']
            
            # Total revenue
            cursor.execute("""
                SELECT COALESCE(SUM(total_fare), 0) as revenue 
                FROM bookings 
                WHERE booking_status = 'Confirmed'
            """)
            stats['revenue'] = float(cursor.fetchone()['revenue'])
            
            # Available schedules
            cursor.execute("SELECT COUNT(*) as total FROM bus_schedules WHERE travel_date >= CURDATE()")
            stats['active_schedules'] = cursor.fetchone()['total']
            
            # Recent bookings
            cursor.execute("""
                SELECT b.booking_reference, u.username, 
                       CONCAT(u.first_name, ' ', u.last_name) as passenger_name, 
                       b.total_fare, b.booking_date
                FROM bookings b
                JOIN users u ON b.user_id = u.user_id
                ORDER BY b.booking_date DESC
                LIMIT 5
            """)
            stats['recent_bookings'] = cursor.fetchall()
            
            # Format dates
            for booking in stats['recent_bookings']:
                if 'booking_date' in booking and booking['booking_date']:
                    if hasattr(booking['booking_date'], 'isoformat'):
                        booking['booking_date'] = booking['booking_date'].isoformat()
            
            return stats
            
        except Error as e:
            print(f"Stats error: {e}")
            return self.get_sample_admin_stats()
        finally:
            if conn:
                conn.close()
    
    def get_sample_admin_stats(self):
        """Sample admin stats for demo"""
        return {
            'total_bookings': 45,
            'total_users': 25,
            'today_bookings': 8,
            'revenue': 56750.00,
            'active_schedules': 28,
            'recent_bookings': [
                {'booking_reference': 'BKP202412045', 'username': 'juan', 'passenger_name': 'Juan Dela Cruz', 'total_fare': 2200.00, 'booking_date': '2024-12-05'},
                {'booking_reference': 'BKP202412044', 'username': 'maria', 'passenger_name': 'Maria Santos', 'total_fare': 1250.00, 'booking_date': '2024-12-04'},
                {'booking_reference': 'BKP202412043', 'username': 'pedro', 'passenger_name': 'Pedro Reyes', 'total_fare': 850.00, 'booking_date': '2024-12-03'}
            ]
        }
    
    def get_all_cities(self):
        """Get all Philippine cities for autocomplete"""
        conn = self.get_connection()
        if not conn:
            return self.get_sample_cities()
        
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT cm.name as city_name, p.province_name as province, r.region_name as region 
                FROM cities_municipalities cm
                JOIN provinces p ON cm.province_id = p.province_id
                JOIN regions r ON p.region_id = r.region_id
                ORDER BY cm.name
                LIMIT 50
            """)
            cities = cursor.fetchall()
            return cities
        except Error as e:
            print(f"Error getting cities: {e}")
            return self.get_sample_cities()
        finally:
            if conn:
                conn.close()
    
    def get_sample_cities(self):
        """Sample cities for demo"""
        return [
            {'city_name': 'Manila', 'province': 'Metro Manila', 'region': 'NCR'},
            {'city_name': 'Cebu City', 'province': 'Cebu', 'region': 'Central Visayas'},
            {'city_name': 'Davao City', 'province': 'Davao del Sur', 'region': 'Davao'},
            {'city_name': 'Zamboanga City', 'province': 'Zamboanga del Sur', 'region': 'Zamboanga Peninsula'},
            {'city_name': 'Baguio', 'province': 'Benguet', 'region': 'CAR'},
            {'city_name': 'Iloilo City', 'province': 'Iloilo', 'region': 'Western Visayas'},
            {'city_name': 'Pagadian', 'province': 'Zamboanga del Sur', 'region': 'Zamboanga Peninsula'},
            {'city_name': 'Cagayan de Oro', 'province': 'Misamis Oriental', 'region': 'Northern Mindanao'},
            {'city_name': 'Legazpi', 'province': 'Albay', 'region': 'Bicol'},
            {'city_name': 'Bacolod', 'province': 'Negros Occidental', 'region': 'Western Visayas'}
        ]

class OfflineManager:
    def __init__(self):
        self.data_dir = "database/offline_data"
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(f"{self.data_dir}/users", exist_ok=True)
        os.makedirs(f"{self.data_dir}/bookings", exist_ok=True)
        os.makedirs(f"{self.data_dir}/schedules", exist_ok=True)
    
    def save_user_offline(self, user_data):
        try:
            user_id = str(uuid.uuid4())
            filepath = f"{self.data_dir}/users/{user_id}.json"
            user_data['offline_id'] = user_id
            user_data['created_at'] = datetime.now().isoformat()
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(user_data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving offline user: {e}")
            return False
    
    def authenticate_offline(self, username, password):
        try:
            users_dir = f"{self.data_dir}/users"
            if not os.path.exists(users_dir):
                return None
            
            for filename in os.listdir(users_dir):
                if filename.endswith('.json'):
                    filepath = f"{users_dir}/{filename}"
                    with open(filepath, 'r', encoding='utf-8') as f:
                        user = json.load(f)
                    
                    if user.get('username') == username and user.get('password') == password:
                        return user
            return None
        except Exception as e:
            print(f"Error in offline authentication: {e}")
            return None
    
    def save_booking_offline(self, booking_data):
        try:
            booking_id = str(uuid.uuid4())
            filepath = f"{self.data_dir}/bookings/{booking_id}.json"
            booking_data['offline_id'] = booking_id
            booking_data['saved_at'] = datetime.now().isoformat()
            booking_data['is_synced'] = False
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(booking_data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving offline booking: {e}")
            return False
    
    def get_user_offline_bookings(self, username):
        bookings = []
        try:
            bookings_dir = f"{self.data_dir}/bookings"
            if not os.path.exists(bookings_dir):
                return bookings
            
            for filename in os.listdir(bookings_dir):
                if filename.endswith('.json'):
                    filepath = f"{bookings_dir}/{filename}"
                    with open(filepath, 'r', encoding='utf-8') as f:
                        booking = json.load(f)
                    
                    if booking.get('username') == username:
                        bookings.append({
                            'booking_reference': booking.get('booking_reference', 'OFFLINE-' + booking.get('offline_id', 'unknown')),
                            'passenger_name': booking.get('passenger_name', 'Passenger'),
                            'booking_date': booking.get('saved_at', datetime.now().isoformat()),
                            'total_fare': booking.get('total_fare', 0),
                            'booking_status': 'Pending Sync',
                            'payment_status': 'Pending',
                            'is_offline': True,
                            'seat_numbers': f"Seat-{booking.get('seat_count', 1)}",
                            'route_name': booking.get('route_name', 'Offline Booking')
                        })
        except Exception as e:
            print(f"Error getting offline bookings: {e}")
        return bookings
    
    def search_schedules_offline(self, origin, destination, travel_date):
        """Return cached schedules for offline mode"""
        try:
            cache_file = f"{self.data_dir}/schedules/cache.json"
            if os.path.exists(cache_file):
                with open(cache_file, 'r', encoding='utf-8') as f:
                    all_schedules = json.load(f)
                
                # Filter by search criteria
                filtered = []
                for schedule in all_schedules:
                    origin_match = not origin or origin.lower() in schedule.get('origin_city', '').lower()
                    dest_match = not destination or destination.lower() in schedule.get('destination_city', '').lower()
                    date_match = schedule.get('travel_date', '') == travel_date
                    
                    if origin_match and dest_match and date_match:
                        filtered.append(schedule)
                
                return filtered[:10]  # Limit to 10 results
        except Exception as e:
            print(f"Error reading offline cache: {e}")
            pass
        
        # Return sample data if no cache
        return self.get_sample_offline_schedules(origin, destination, travel_date)
    
    def get_sample_offline_schedules(self, origin, destination, travel_date):
        """Sample schedules for offline mode"""
        return [
            {
                'schedule_id': 101,
                'bus_number': 'PH-OFFLINE-001',
                'departure_time': '08:00:00',
                'arrival_time': '14:00:00',
                'travel_date': travel_date if travel_date else date.today().isoformat(),
                'total_seats': 45,
                'available_seats': 25,
                'fare': 850.00,
                'bus_operator': 'Sample Operator',
                'bus_type': 'Regular',
                'amenities': 'Aircon, TV',
                'route_name': f'{origin if origin else "Manila"} to {destination if destination else "Baguio"}',
                'origin_city': origin if origin else 'Manila',
                'destination_city': destination if destination else 'Baguio',
                'distance_km': 250,
                'estimated_hours': 6,
                'route_type': 'Regular',
                'amenities_list': ['Aircon', 'TV']
            }
        ]
    
    def cache_schedules(self, schedules):
        """Cache schedules for offline use"""
        try:
            with open(f"{self.data_dir}/schedules/cache.json", 'w', encoding='utf-8') as f:
                json.dump(schedules, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error caching schedules: {e}")
            return False
    
    def get_pending_sync_count(self):
        try:
            user_files = 0
            booking_files = 0
            
            users_dir = f"{self.data_dir}/users"
            if os.path.exists(users_dir):
                user_files = len([f for f in os.listdir(users_dir) if f.endswith('.json')])
            
            bookings_dir = f"{self.data_dir}/bookings"
            if os.path.exists(bookings_dir):
                booking_files = len([f for f in os.listdir(bookings_dir) if f.endswith('.json')])
                
            return user_files + booking_files
        except Exception as e:
            print(f"Error getting pending sync count: {e}")
            return 0

class SyncManager:
    def sync_all_data(self, db_handler, offline_mgr):
        """Sync offline data to database"""
        results = {
            'success': True,
            'users_synced': 0,
            'bookings_synced': 0,
            'errors': []
        }
        
        # Sync users
        user_results = self.sync_users(db_handler, offline_mgr)
        results['users_synced'] = user_results.get('users_synced', 0)
        results['errors'].extend(user_results.get('errors', []))
        
        # Sync bookings
        booking_results = self.sync_bookings(db_handler, offline_mgr)
        results['bookings_synced'] = booking_results.get('bookings_synced', 0)
        results['errors'].extend(booking_results.get('errors', []))
        
        return results
    
    def sync_users(self, db_handler, offline_mgr):
        """Sync offline users"""
        results = {'users_synced': 0, 'errors': []}
        
        users_dir = f"{offline_mgr.data_dir}/users"
        if not os.path.exists(users_dir):
            return results
        
        for filename in os.listdir(users_dir):
            if not filename.endswith('.json'):
                continue
            
            filepath = f"{users_dir}/{filename}"
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    user_data = json.load(f)
                
                # Register user in database
                result = db_handler.register_user(
                    user_data.get('username', ''),
                    user_data.get('email', ''),
                    user_data.get('password', ''),
                    user_data.get('full_name', ''),  # This comes from offline storage
                    user_data.get('phone')
                )
                
                if result.get('success'):
                    os.remove(filepath)
                    results['users_synced'] += 1
                else:
                    results['errors'].append(f"User {user_data.get('username')}: {result.get('message')}")
                    
            except Exception as e:
                results['errors'].append(f"File {filename}: {str(e)}")
        
        return results
    
    def sync_bookings(self, db_handler, offline_mgr):
        """Sync offline bookings"""
        results = {'bookings_synced': 0, 'errors': []}
        
        bookings_dir = f"{offline_mgr.data_dir}/bookings"
        if not os.path.exists(bookings_dir):
            return results
        
        for filename in os.listdir(bookings_dir):
            if not filename.endswith('.json'):
                continue
            
            filepath = f"{bookings_dir}/{filename}"
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    booking_data = json.load(f)
                
                # For demo purposes, just remove the file
                # In production, you would need to find the real user_id
                print(f"Would sync booking: {booking_data.get('booking_reference')}")
                
                os.remove(filepath)
                results['bookings_synced'] += 1
                    
            except Exception as e:
                results['errors'].append(f"File {filename}: {str(e)}")
        
        return results

# Initialize components
db_handler = DatabaseHandler()
offline_mgr = OfflineManager()
sync_mgr = SyncManager()

def check_connection():
    """Check and update connection status"""
    is_online = db_handler.check_connection()
    session['online_mode'] = is_online
    return is_online

@app.route('/')
def index():
    """Home page"""
    is_online = check_connection()
    return render_template('index.html', 
                         online=is_online,
                         current_date=date.today().isoformat())
@app.route('/profile')
def profile():
    """User profile page"""
    is_online = check_connection()
    
    if 'user_id' not in session:
        flash('Please login to view profile', 'error')
        return redirect(url_for('login'))
    
    user_info = None
    if is_online and not session.get('offline_user'):
        # Get user info from database
        conn = db_handler.get_connection()
        if conn:
            try:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT username, email, full_name, phone, created_at FROM users WHERE user_id = %s", 
                             (session['user_id'],))
                user_info = cursor.fetchone()
            except Error as e:
                print(f"Error fetching user: {e}")
            finally:
                if conn:
                    conn.close()
    
    return render_template('profile.html', online=is_online, user=user_info or session)

@app.route('/debug-bookings')
def debug_bookings():
    """Debug endpoint to check bookings"""
    if 'user_id' not in session:
        return "Please login first"
    
    conn = db_handler.get_connection()
    if not conn:
        return "Database not connected"
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Check if bookings table exists and what columns it has
        cursor.execute("SHOW TABLES LIKE 'bookings'")
        if not cursor.fetchone():
            return "Bookings table does not exist!"
        
        # Show table structure
        cursor.execute("DESCRIBE bookings")
        columns = cursor.fetchall()
        
        # Show all bookings for this user
        cursor.execute("SELECT * FROM bookings WHERE user_id = %s", (session['user_id'],))
        bookings = cursor.fetchall()
        
        result = "<h2>Bookings Table Structure:</h2><pre>"
        for col in columns:
            result += f"{col}\n"
        
        result += f"</pre><h2>Your Bookings ({len(bookings)}):</h2><pre>"
        for booking in bookings:
            result += f"{booking}\n\n"
        result += "</pre>"
        
        return result
    except Error as e:
        return f"Error: {str(e)}"
    finally:
        if conn:
            conn.close()

@app.route('/debug-routes')
def debug_routes():
    """Debug route to see available routes"""
    conn = db_handler.get_connection()
    if not conn:
        return jsonify({'error': 'No database connection'})
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Get all routes with city names
        cursor.execute("""
            SELECT 
                r.route_id,
                r.route_name,
                o.name as origin_city,
                d.name as destination_city,
                r.distance_km,
                r.estimated_hours,
                r.base_fare
            FROM bus_routes r
            JOIN cities_municipalities o ON r.origin_city_muni_id = o.city_muni_id
            JOIN cities_municipalities d ON r.destination_city_muni_id = d.city_muni_id
            WHERE r.is_active = 1
        """)
        routes = cursor.fetchall()
        
        # Get all schedules for today and future
        cursor.execute("""
            SELECT 
                s.schedule_id,
                s.travel_date,
                s.departure_time,
                s.available_seats,
                o.name as origin,
                d.name as destination
            FROM bus_schedules s
            JOIN bus_routes r ON s.route_id = r.route_id
            JOIN cities_municipalities o ON r.origin_city_muni_id = o.city_muni_id
            JOIN cities_municipalities d ON r.destination_city_muni_id = d.city_muni_id
            WHERE s.travel_date >= CURDATE()
            ORDER BY s.travel_date, s.departure_time
            LIMIT 20
        """)
        schedules = cursor.fetchall()
        
        return jsonify({
            'routes': routes,
            'upcoming_schedules': schedules,
            'total_routes': len(routes),
            'total_schedules': len(schedules)
        })
    except Error as e:
        return jsonify({'error': str(e)})
    finally:
        if conn:
            conn.close()

@app.route('/debug-database')
def debug_database():
    """Check what's in the database"""
    conn = db_handler.get_connection()
    if not conn:
        return jsonify({'error': 'No database connection'})
    
    try:
        cursor = conn.cursor(dictionary=True)
        results = {}
        
        # Check cities
        cursor.execute("SELECT name FROM cities_municipalities LIMIT 10")
        results['cities'] = [c['name'] for c in cursor.fetchall()]
        
        # Check routes
        cursor.execute("""
            SELECT r.route_name, o.name as origin, d.name as destination
            FROM bus_routes r
            JOIN cities_municipalities o ON r.origin_city_muni_id = o.city_muni_id
            JOIN cities_municipalities d ON r.destination_city_muni_id = d.city_muni_id
        """)
        results['routes'] = cursor.fetchall()
        
        # Check schedules with actual dates
        cursor.execute("""
            SELECT 
                s.schedule_id,
                s.travel_date,
                s.departure_time,
                s.available_seats,
                o.name as origin,
                d.name as destination
            FROM bus_schedules s
            JOIN bus_routes r ON s.route_id = r.route_id
            JOIN cities_municipalities o ON r.origin_city_muni_id = o.city_muni_id
            JOIN cities_municipalities d ON r.destination_city_muni_id = d.city_muni_id
            ORDER BY s.travel_date
        """)
        schedules = cursor.fetchall()
        results['schedules'] = schedules
        
        # Get today's date
        results['today'] = date.today().isoformat()
        
        # Show what dates have schedules
        dates = {}
        for s in schedules:
            date_str = s['travel_date'].isoformat() if hasattr(s['travel_date'], 'isoformat') else str(s['travel_date'])
            if date_str not in dates:
                dates[date_str] = []
            dates[date_str].append(f"{s['origin']} → {s['destination']}")
        
        results['schedules_by_date'] = dates
        
        return jsonify(results)
    except Error as e:
        return jsonify({'error': str(e)})
    finally:
        if conn:
            conn.close()

@app.route('/debug-cities')
def debug_cities():
    """Debug route to see available cities"""
    conn = db_handler.get_connection()
    if not conn:
        return jsonify({'error': 'No database connection'})
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Get all cities
        cursor.execute("""
            SELECT cm.name, p.province_name 
            FROM cities_municipalities cm
            JOIN provinces p ON cm.province_id = p.province_id
            ORDER BY cm.name
        """)
        cities = cursor.fetchall()
        
        # Get all routes
        cursor.execute("""
            SELECT r.route_name, o.name as origin, d.name as destination
            FROM bus_routes r
            JOIN cities_municipalities o ON r.origin_city_muni_id = o.city_muni_id
            JOIN cities_municipalities d ON r.destination_city_muni_id = d.city_muni_id
        """)
        routes = cursor.fetchall()
        
        # Get today's schedules
        today = date.today().isoformat()
        cursor.execute("""
            SELECT s.schedule_id, s.bus_number, s.travel_date, 
                   o.name as origin, d.name as destination
            FROM bus_schedules s
            JOIN bus_routes r ON s.route_id = r.route_id
            JOIN cities_municipalities o ON r.origin_city_muni_id = o.city_muni_id
            JOIN cities_municipalities d ON r.destination_city_muni_id = d.city_muni_id
            WHERE s.travel_date >= CURDATE()
            LIMIT 10
        """)
        schedules = cursor.fetchall()
        
        return jsonify({
            'cities': cities,
            'routes': routes,
            'schedules': schedules,
            'sample_date': today
        })
    except Error as e:
        return jsonify({'error': str(e)})
    finally:
        if conn:
            conn.close()
    
@app.route("/barangays")
def barangays():
    conn = db_handler.get_connection()
    if not conn:
        flash('Database connection error', 'error')
        return redirect(url_for('index'))
    
    try:
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT b.barangay_id, b.name as barangay_name, cm.name as city_name
            FROM barangays b
            LEFT JOIN cities_municipalities cm ON b.city_muni_id = cm.city_muni_id
            LIMIT 100
        """
        cursor.execute(query)
        barangay_list = cursor.fetchall()
    except Error as e:
        flash(f'Error loading barangays: {str(e)}', 'error')
        barangay_list = []
    finally:
        if conn:
            conn.close()
    
    return render_template("barangays.html", barangays=barangay_list)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    is_online = check_connection()
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        if not username or not password:
            flash('Please enter username and password', 'error')
            return render_template('login.html', online=is_online)
        
        if is_online:
            # Online login
            user = db_handler.authenticate_user(username, password)
            if user:
                session['user_id'] = user['user_id']
                session['username'] = user['username']
                session['full_name'] = user.get('full_name', username)
                session['is_admin'] = user.get('is_admin', False)
                session['offline_user'] = False
                flash(f'Welcome back, {user.get("full_name", username)}!', 'success')
                return redirect(url_for('index'))
            else:
                flash('Invalid username or password', 'error')
        else:
            # Offline login
            user = offline_mgr.authenticate_offline(username, password)
            if user:
                session['user_id'] = user.get('offline_id')
                session['username'] = user.get('username')
                session['full_name'] = user.get('full_name', username)
                session['is_admin'] = False
                session['offline_user'] = True
                flash('Logged in offline mode', 'warning')
                return redirect(url_for('index'))
            else:
                flash('Invalid username or password', 'error')
    
    return render_template('login.html', online=is_online)

@app.route('/logout')
def logout():
    """User logout"""
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    is_online = check_connection()
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        full_name = request.form.get('full_name', '').strip()
        phone = request.form.get('phone', '').strip()
        
        # Validation
        if not all([username, email, password, confirm_password, full_name]):
            flash('Please fill all required fields', 'error')
            return render_template('register.html', online=is_online)
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('register.html', online=is_online)
        
        if len(password) < 6:
            flash('Password must be at least 6 characters long', 'error')
            return render_template('register.html', online=is_online)
        
        if len(username) < 3 or len(username) > 20:
            flash('Username must be between 3-20 characters', 'error')
            return render_template('register.html', online=is_online)
        
        if is_online:
            # Online registration
            result = db_handler.register_user(username, email, password, full_name, phone)
            if result.get('success'):
                flash('Registration successful! Please login.', 'success')
                return redirect(url_for('login'))
            else:
                error_msg = result.get('message', 'Registration failed')
                if 'Duplicate' in error_msg:
                    flash('Username or email already exists', 'error')
                else:
                    flash(error_msg, 'error')
        else:
            # Offline registration
            user_data = {
                'username': username,
                'email': email,
                'password': password,
                'full_name': full_name,
                'phone': phone
            }
            
            if offline_mgr.save_user_offline(user_data):
                flash('Registration saved offline. Will sync when online.', 'warning')
                return redirect(url_for('login'))
            else:
                flash('Offline registration failed', 'error')
    
    return render_template('register.html', online=is_online)


@app.route('/search', methods=['GET', 'POST'])
def search_routes():
    """Search bus routes"""
    is_online = check_connection()
    schedules = []
    search_data = {}
    current_date = date.today().isoformat()
    ph_cities = db_handler.get_all_cities()
    
    if request.method == 'POST':
        origin = request.form.get('origin', '').strip()
        destination = request.form.get('destination', '').strip()
        travel_date = request.form.get('travel_date', current_date).strip()
        
        search_data = {
            'origin': origin,
            'destination': destination,
            'date': travel_date
        }
        
        if origin or destination:
            if is_online:
                # Try to search with the exact date first
                schedules = db_handler.search_schedules(origin, destination, travel_date)
                
                # If no results, try with a future date range (for demo purposes)
                if not schedules:
                    print(f"No schedules found for {travel_date}, checking future dates...")
                    # You could modify your search_schedules to try future dates
                    # Or show sample data for demo
                    if origin and destination:
                        flash(f'No schedules found for {travel_date}. Showing sample data for demonstration.', 'info')
                        schedules = db_handler.get_sample_schedules(origin, destination, travel_date)
                
                # Cache results for offline use
                if schedules:
                    offline_mgr.cache_schedules(schedules)
            else:
                schedules = offline_mgr.search_schedules_offline(origin, destination, travel_date)
    
    return render_template('search_routes.html',
                         online=is_online,
                         schedules=schedules,
                         search_data=search_data,
                         current_date=current_date,
                         ph_cities=ph_cities)

@app.route('/book/<int:schedule_id>', methods=['GET', 'POST'])
def book_ticket(schedule_id):
    """Book a ticket"""
    is_online = check_connection()
    
    if 'user_id' not in session:
        flash('Please login to book tickets', 'error')
        return redirect(url_for('login'))
    
    # Get schedule details
    if is_online:
        schedule = db_handler.get_schedule_details(schedule_id)
    else:
        schedule = db_handler.get_sample_schedule_details(schedule_id)  # Use sample for offline
    
    if not schedule:
        flash('Schedule not found', 'error')
        return redirect(url_for('search_routes'))
    
    if request.method == 'POST':
        passenger_name = request.form.get('passenger_name', '').strip()
        passenger_age = request.form.get('passenger_age', '25')
        passenger_gender = request.form.get('passenger_gender', 'Other')
        seat_count = int(request.form.get('seat_count', 1))
        
        if not passenger_name:
            flash('Please enter passenger name', 'error')
            return render_template('booking.html', online=is_online, schedule=schedule)
        
        # Generate booking reference
        booking_ref = f"BKP{datetime.now().strftime('%Y%m%d')}{uuid.uuid4().hex[:6].upper()}"
        
        if is_online:
            # Online booking
            result = db_handler.create_booking(
                user_id=session['user_id'],
                schedule_id=schedule_id,
                passenger_name=passenger_name,
                passenger_age=passenger_age,
                passenger_gender=passenger_gender,
                seat_count=seat_count,
                booking_ref=booking_ref
            )
            
            if result['success']:
                flash(f'Booking confirmed! Reference: {booking_ref}', 'success')
                return redirect(url_for('my_bookings'))
            else:
                flash(result.get('message', 'Booking failed'), 'error')
        else:
            # Offline booking
            booking_data = {
                'booking_reference': booking_ref,
                'user_id': session['user_id'],
                'username': session.get('username', 'unknown'),
                'schedule_id': schedule_id,
                'passenger_name': passenger_name,
                'passenger_age': passenger_age,
                'passenger_gender': passenger_gender,
                'seat_count': seat_count,
                'total_fare': float(schedule.get('fare', 2200)) * seat_count,
                'route_name': schedule.get('route_name', 'Unknown Route')
            }
            
            if offline_mgr.save_booking_offline(booking_data):
                flash(f'Booking saved offline! Reference: {booking_ref}', 'warning')
                return redirect(url_for('my_bookings'))
            else:
                flash('Booking failed', 'error')
    
    return render_template('booking.html', online=is_online, schedule=schedule)

@app.route('/my-bookings')
def my_bookings():
    """View user bookings"""
    is_online = check_connection()
    
    if 'user_id' not in session:
        flash('Please login to view bookings', 'error')
        return redirect(url_for('login'))
    
    bookings = []
    
    if is_online and not session.get('offline_user'):
        # Online bookings
        bookings = db_handler.get_user_bookings(session['user_id'])
    
    # Offline bookings
    offline_bookings = offline_mgr.get_user_offline_bookings(session.get('username', ''))
    bookings.extend(offline_bookings)
    
    return render_template('my_bookings.html', online=is_online, bookings=bookings)

@app.route('/admin')
def admin():
    """Admin panel"""
    is_online = check_connection()
    
    if 'user_id' not in session or not session.get('is_admin', False):
        flash('Admin access required', 'error')
        return redirect(url_for('index'))
    
    if not is_online:
        flash('Admin panel requires online connection', 'error')
        return redirect(url_for('index'))
    
    stats = db_handler.get_admin_stats()
    pending_sync = offline_mgr.get_pending_sync_count()
    
    return render_template('admin.html', 
                         online=True, 
                         stats=stats, 
                         pending_sync=pending_sync)

@app.route('/sync-data', methods=['POST'])
def sync_data():
    """Sync offline data"""
    if not check_connection():
        return jsonify({'success': False, 'message': 'No database connection'})
    
    result = sync_mgr.sync_all_data(db_handler, offline_mgr)
    return jsonify(result)

@app.route('/sync-offline-data')
def sync_offline_data():
    """Alias for sync_data"""
    return redirect(url_for('sync_data'))

@app.route('/check-connection')
def check_connection_status():
    """Check connection status"""
    is_online = check_connection()
    return jsonify({'online': is_online})

@app.route('/api/cities')
def api_cities():
    """API endpoint for cities autocomplete"""
    cities = db_handler.get_all_cities()
    return jsonify(cities)

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

if __name__ == '__main__':
    # Ensure directories exist
    os.makedirs('database/offline_data/users', exist_ok=True)
    os.makedirs('database/offline_data/bookings', exist_ok=True)
    os.makedirs('database/offline_data/schedules', exist_ok=True)
    
    print("=" * 70)
    print("🇵🇭 PHILIPPINE BUS BOOKING SYSTEM - SCHOOL PROJECT")
    print("=" * 70)
    print(f"📅 Date: {date.today()}")
    print("🌐 Server: http://localhost:5000")
    print("-" * 70)
    
    # Check database connection
    if db_handler.check_connection():
        print("✅ Database: Connected to MySQL")
        print("   Database: bus_booking_system")
        
        # DEBUG: Test all queries
        conn = db_handler.get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                
                # Test 1: Check users table structure
                print("\n📊 Testing database queries:")
                cursor.execute("SHOW COLUMNS FROM users")
                columns = cursor.fetchall()
                print(f"   ✅ Users table columns: {', '.join([col[0] for col in columns])}")
                
                # Test 2: Test the problematic query directly
                print("\n🔍 Testing admin stats query:")
                test_query = """
                    SELECT b.booking_reference, u.username, 
                           CONCAT(u.first_name, ' ', u.last_name) as passenger_name, 
                           b.total_fare, b.booking_date
                    FROM bookings b
                    JOIN users u ON b.user_id = u.user_id
                    LIMIT 1
                """
                cursor.execute(test_query)
                result = cursor.fetchone()
                if result:
                    print(f"   ✅ Query successful! Sample: {result}")
                else:
                    print("   ⚠️ Query ran but no results (this is OK if no bookings exist)")
                    
                # Test 3: Check if any view or trigger exists that might use full_name
                cursor.execute("""
                    SELECT TABLE_NAME, VIEW_DEFINITION 
                    FROM information_schema.VIEWS 
                    WHERE TABLE_SCHEMA = 'bus_booking_system'
                """)
                views = cursor.fetchall()
                if views:
                    print("\n📊 Found views:")
                    for view in views:
                        if 'full_name' in str(view[1]):
                            print(f"   ⚠️ View {view[0]} contains 'full_name'")
                
                # Test 4: Check for any triggers
                cursor.execute("""
                    SELECT TRIGGER_NAME, ACTION_TIMING, EVENT_MANIPULATION
                    FROM information_schema.TRIGGERS
                    WHERE TRIGGER_SCHEMA = 'bus_booking_system'
                """)
                triggers = cursor.fetchall()
                if triggers:
                    print("\n📊 Found triggers:")
                    for trigger in triggers:
                        print(f"   • {trigger[0]}")
                        
            except Error as e:
                print(f"❌ Error in debug tests: {e}")
            finally:
                conn.close()
    else:
        print("⚠️  Database: Not connected to MySQL")
        print("   Mode: Offline (Local storage with sample data)")
        print("   Tip: Import database/philippine_bus_routes_complete.sql in phpMyAdmin")
    
    print("-" * 70)
    print("📁 AVAILABLE ROUTES:")
    print("   • Manila to Baguio, Laoag, Legazpi, Naga")
    print("   • Zamboanga to Manila, Cagayan de Oro, Davao")
    print("   • Pagadian to Manila, Cagayan de Oro")
    print("   • Cebu to Tagbilaran, Dumaguete, Manila")
    print("   • Davao to Manila, Cagayan de Oro, General Santos")
    print("-" * 70)
    print("👤 TEST USERS:")
    print("   Admin: admin / admin123")
    print("   User: zambo_user / password123")
    print("   User: pagadian_user / password123")
    print("   User: cebu_user / password123")
    print("   User: davao_user / password123")
    print("-" * 70)
    print("🛑 Press Ctrl+C to stop the server")
    print("=" * 70)
    
    app.run(debug=True, port=5000, use_reloader=False)