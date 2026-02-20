import mysql.connector
from mysql.connector import Error
import hashlib
from datetime import datetime

class DatabaseHandler:
    def __init__(self):
        self.config = {
            'host': 'localhost',
            'user': 'root',
            'password': '',  # XAMPP default is empty
            'database': 'bus_booking_system',
            'port': 3306,
            'charset': 'utf8mb4'
        }
    
    def check_connection(self):
        """Check if MySQL database is accessible"""
        try:
            conn = mysql.connector.connect(**self.config)
            if conn.is_connected():
                conn.close()
                return True
        except Error:
            pass
        return False
    
    def get_connection(self):
        """Establish database connection"""
        try:
            conn = mysql.connector.connect(**self.config)
            return conn
        except Error as e:
            print(f"Database connection error: {e}")
            return None
    
    def hash_password(self, password):
        """Hash password for storage"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def register_user(self, username, email, password, full_name, phone=None):
        """Register a new user"""
        conn = self.get_connection()
        if not conn:
            return False
        
        cursor = None
        try:
            cursor = conn.cursor()
            hashed_pw = self.hash_password(password)
            
            query = """
            INSERT INTO users (username, email, password_hash, full_name, phone)
            VALUES (%s, %s, %s, %s, %s)
            """
            
            cursor.execute(query, (username, email, hashed_pw, full_name, phone))
            conn.commit()
            return cursor.lastrowid
            
        except Error as e:
            print(f"Registration error: {e}")
            return False
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    def authenticate_user(self, username, password):
        """Authenticate user login"""
        conn = self.get_connection()
        if not conn:
            return None
        
        cursor = None
        try:
            cursor = conn.cursor(dictionary=True)
            hashed_pw = self.hash_password(password)
            
            query = """
            SELECT user_id, username, email, full_name, is_admin 
            FROM users 
            WHERE username = %s AND password_hash = %s
            """
            
            cursor.execute(query, (username, hashed_pw))
            user = cursor.fetchone()
            return user
            
        except Error as e:
            print(f"Authentication error: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    def get_all_schedules(self):
        """Get all schedules for caching"""
        conn = self.get_connection()
        if not conn:
            return []
        
        cursor = None
        try:
            cursor = conn.cursor(dictionary=True)
            
            query = """
            SELECT s.*, r.route_name, r.origin_city, r.destination_city
            FROM bus_schedules s
            JOIN bus_routes r ON s.route_id = r.route_id
            WHERE s.travel_date >= CURDATE()
            ORDER BY s.travel_date, s.departure_time
            """
            
            cursor.execute(query)
            schedules = cursor.fetchall()
            
            # Convert datetime objects to strings
            for schedule in schedules:
                if 'travel_date' in schedule and schedule['travel_date']:
                    schedule['travel_date'] = schedule['travel_date'].isoformat()
                if 'departure_time' in schedule and schedule['departure_time']:
                    if isinstance(schedule['departure_time'], str):
                        schedule['departure_time'] = schedule['departure_time']
                    else:
                        schedule['departure_time'] = str(schedule['departure_time'])
                if 'arrival_time' in schedule and schedule['arrival_time']:
                    if isinstance(schedule['arrival_time'], str):
                        schedule['arrival_time'] = schedule['arrival_time']
                    else:
                        schedule['arrival_time'] = str(schedule['arrival_time'])
            
            return schedules
            
        except Error as e:
            print(f"Get schedules error: {e}")
            return []
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    def search_schedules(self, origin, destination, travel_date):
        """Search for available bus schedules"""
        conn = self.get_connection()
        if not conn:
            return []
        
        cursor = None
        try:
            cursor = conn.cursor(dictionary=True)
            
            query = """
            SELECT s.*, r.route_name, r.origin_city, r.destination_city
            FROM bus_schedules s
            JOIN bus_routes r ON s.route_id = r.route_id
            WHERE LOWER(r.origin_city) LIKE LOWER(%s)
            AND LOWER(r.destination_city) LIKE LOWER(%s)
            AND s.travel_date = %s
            AND s.available_seats > 0
            ORDER BY s.departure_time
            """
            
            cursor.execute(query, (f"%{origin}%", f"%{destination}%", travel_date))
            schedules = cursor.fetchall()
            
            # Format dates and times
            for schedule in schedules:
                if 'travel_date' in schedule:
                    schedule['travel_date'] = schedule['travel_date'].isoformat()
            
            return schedules
            
        except Error as e:
            print(f"Search error: {e}")
            return []
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    def get_schedule_details(self, schedule_id):
        """Get details for a specific schedule"""
        conn = self.get_connection()
        if not conn:
            return None
        
        cursor = None
        try:
            cursor = conn.cursor(dictionary=True)
            
            query = """
            SELECT s.*, r.route_name, r.origin_city, r.destination_city
            FROM bus_schedules s
            JOIN bus_routes r ON s.route_id = r.route_id
            WHERE s.schedule_id = %s
            """
            
            cursor.execute(query, (schedule_id,))
            schedule = cursor.fetchone()
            
            if schedule and 'travel_date' in schedule:
                schedule['travel_date'] = schedule['travel_date'].isoformat()
            
            return schedule
            
        except Error as e:
            print(f"Get schedule error: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    def create_booking(self, user_id, schedule_id, passenger_name, 
                      passenger_age, passenger_gender, seat_count, booking_ref):
        """Create a new booking"""
        conn = self.get_connection()
        if not conn:
            return {'success': False, 'message': 'Database connection failed'}
        
        cursor = None
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
            
            # Create booking
            booking_query = """
            INSERT INTO bookings 
            (user_id, schedule_id, booking_reference, passenger_name, passenger_age, 
             passenger_gender, seat_numbers, total_fare, booking_status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'Confirmed')
            """
            
            cursor.execute(booking_query, (
                user_id, schedule_id, booking_ref, passenger_name, passenger_age,
                passenger_gender, seat_numbers, total_fare
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
                'booking_id': cursor.lastrowid
            }
            
        except Error as e:
            if conn:
                conn.rollback()
            print(f"Booking error: {e}")
            return {'success': False, 'message': f'Booking failed: {str(e)}'}
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    def get_user_bookings(self, user_id):
        """Get all bookings for a user"""
        conn = self.get_connection()
        if not conn:
            return []
        
        cursor = None
        try:
            cursor = conn.cursor(dictionary=True)
            
            query = """
            SELECT b.*, s.bus_number, s.departure_time, s.arrival_time, s.travel_date,
                   r.route_name, r.origin_city, r.destination_city
            FROM bookings b
            JOIN bus_schedules s ON b.schedule_id = s.schedule_id
            JOIN bus_routes r ON s.route_id = r.route_id
            WHERE b.user_id = %s
            ORDER BY b.booking_date DESC
            """
            
            cursor.execute(query, (user_id,))
            bookings = cursor.fetchall()
            
            # Format dates
            for booking in bookings:
                if 'booking_date' in booking:
                    booking['booking_date'] = booking['booking_date'].isoformat()
                if 'travel_date' in booking:
                    booking['travel_date'] = booking['travel_date'].isoformat()
                booking['is_offline'] = False
            
            return bookings
            
        except Error as e:
            print(f"Get bookings error: {e}")
            return []
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    def get_admin_stats(self):
        """Get statistics for admin panel"""
        conn = self.get_connection()
        if not conn:
            return {}
        
        cursor = None
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
                SELECT b.booking_reference, u.username, b.passenger_name, b.total_fare, b.booking_date
                FROM bookings b
                JOIN users u ON b.user_id = u.user_id
                ORDER BY b.booking_date DESC
                LIMIT 5
            """)
            stats['recent_bookings'] = cursor.fetchall()
            
            # Format dates in recent bookings
            for booking in stats['recent_bookings']:
                if 'booking_date' in booking:
                    booking['booking_date'] = booking['booking_date'].isoformat()
            
            return stats
            
        except Error as e:
            print(f"Stats error: {e}")
            return {}
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()