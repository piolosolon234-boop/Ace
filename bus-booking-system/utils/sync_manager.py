import json
import os
import mysql.connector
from datetime import datetime
import hashlib

class SyncManager:
    def __init__(self):
        self.offline_dir = "database/offline_data"
    
    def hash_password(self, password):
        """Hash password consistently with database"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def sync_all_data(self, db_handler, offline_mgr):
        """Sync all offline data to MySQL database"""
        results = {
            'success': True,
            'users_synced': 0,
            'bookings_synced': 0,
            'errors': []
        }
        
        # Sync offline users first
        results.update(self.sync_offline_users(db_handler))
        
        # Sync offline bookings
        results.update(self.sync_offline_bookings(db_handler))
        
        # Update success flag if there were errors
        if results['errors']:
            results['success'] = False
        
        return results
    
    def sync_offline_users(self, db_handler):
        """Sync offline users to database"""
        results = {
            'users_synced': 0,
            'user_errors': []
        }
        
        users_dir = f"{self.offline_dir}/users"
        if not os.path.exists(users_dir):
            return results
        
        for filename in os.listdir(users_dir):
            if not filename.endswith('.json'):
                continue
                
            filepath = f"{users_dir}/{filename}"
            user_synced = False
            
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    user_data = json.load(f)
                
                # Connect to database
                conn = db_handler.get_connection()
                if not conn:
                    results['user_errors'].append(f"No database connection for {filename}")
                    continue
                
                cursor = conn.cursor()
                
                # Check if user already exists
                check_query = "SELECT user_id FROM users WHERE username = %s OR email = %s"
                cursor.execute(check_query, (user_data['username'], user_data['email']))
                existing_user = cursor.fetchone()
                
                if existing_user:
                    # User already exists, just delete the offline file
                    os.remove(filepath)
                    results['users_synced'] += 1
                    continue
                
                # Insert new user
                hashed_pw = self.hash_password(user_data['password'])
                insert_query = """
                INSERT INTO users 
                (username, email, password_hash, full_name, phone, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                """
                
                cursor.execute(insert_query, (
                    user_data['username'],
                    user_data['email'],
                    hashed_pw,
                    user_data['full_name'],
                    user_data.get('phone', ''),
                    user_data.get('created_at', datetime.now().isoformat())
                ))
                
                conn.commit()
                cursor.close()
                conn.close()
                
                # Delete offline file after successful sync
                os.remove(filepath)
                results['users_synced'] += 1
                print(f"Synced user: {user_data['username']}")
                
            except mysql.connector.Error as e:
                results['user_errors'].append(f"Database error for {filename}: {str(e)}")
                print(f"Database error syncing user {filename}: {e}")
            except Exception as e:
                results['user_errors'].append(f"Error processing {filename}: {str(e)}")
                print(f"Error syncing user {filename}: {e}")
        
        return results
    
    def sync_offline_bookings(self, db_handler):
        """Sync offline bookings to database"""
        results = {
            'bookings_synced': 0,
            'booking_errors': []
        }
        
        bookings_dir = f"{self.offline_dir}/bookings"
        if not os.path.exists(bookings_dir):
            return results
        
        for filename in os.listdir(bookings_dir):
            if not filename.endswith('.json'):
                continue
                
            filepath = f"{bookings_dir}/{filename}"
            
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    booking_data = json.load(f)
                
                # Connect to database
                conn = db_handler.get_connection()
                if not conn:
                    results['booking_errors'].append(f"No database connection for {filename}")
                    continue
                
                cursor = conn.cursor(dictionary=True)
                
                # Get user_id from username
                user_query = "SELECT user_id FROM users WHERE username = %s"
                cursor.execute(user_query, (booking_data.get('username', ''),))
                user_result = cursor.fetchone()
                
                if not user_result:
                    results['booking_errors'].append(f"User not found for booking {filename}")
                    cursor.close()
                    conn.close()
                    continue
                
                user_id = user_result['user_id']
                
                # Check if schedule still has available seats
                schedule_query = "SELECT available_seats, fare FROM bus_schedules WHERE schedule_id = %s"
                cursor.execute(schedule_query, (booking_data['schedule_id'],))
                schedule_result = cursor.fetchone()
                
                if not schedule_result:
                    results['booking_errors'].append(f"Schedule not found for booking {filename}")
                    cursor.close()
                    conn.close()
                    continue
                
                seat_count = booking_data.get('seat_count', 1)
                if schedule_result['available_seats'] < seat_count:
                    results['booking_errors'].append(f"Not enough seats for booking {filename}")
                    cursor.close()
                    conn.close()
                    continue
                
                # Insert booking
                booking_query = """
                INSERT INTO bookings 
                (user_id, schedule_id, booking_reference, passenger_name, passenger_age, 
                 passenger_gender, seat_numbers, total_fare, booking_status, booking_date)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'Confirmed', %s)
                """
                
                seat_numbers = ", ".join([f"Seat-{i+1}" for i in range(seat_count)])
                total_fare = booking_data.get('total_fare', schedule_result['fare'] * seat_count)
                
                cursor.execute(booking_query, (
                    user_id,
                    booking_data['schedule_id'],
                    booking_data['booking_reference'],
                    booking_data['passenger_name'],
                    booking_data.get('passenger_age', 25),
                    booking_data.get('passenger_gender', 'Other'),
                    seat_numbers,
                    total_fare,
                    booking_data.get('booking_date', datetime.now().isoformat())
                ))
                
                # Update available seats
                update_query = """
                UPDATE bus_schedules 
                SET available_seats = available_seats - %s 
                WHERE schedule_id = %s
                """
                cursor.execute(update_query, (seat_count, booking_data['schedule_id']))
                
                conn.commit()
                cursor.close()
                conn.close()
                
                # Delete offline file after successful sync
                os.remove(filepath)
                results['bookings_synced'] += 1
                print(f"Synced booking: {booking_data['booking_reference']}")
                
            except mysql.connector.Error as e:
                results['booking_errors'].append(f"Database error for {filename}: {str(e)}")
                print(f"Database error syncing booking {filename}: {e}")
            except Exception as e:
                results['booking_errors'].append(f"Error processing {filename}: {str(e)}")
                print(f"Error syncing booking {filename}: {e}")
        
        return results
    
    def cache_schedules(self, schedules):
        """Cache schedules for offline use"""
        try:
            cache_dir = f"{self.offline_dir}/schedules"
            os.makedirs(cache_dir, exist_ok=True)
            
            cache_file = f"{cache_dir}/cache.json"
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(schedules, f, indent=2, ensure_ascii=False)
            
            print(f"Cached {len(schedules)} schedules for offline use")
            return True
        except Exception as e:
            print(f"Cache error: {e}")
            return False