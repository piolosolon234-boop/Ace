-- ============================================
-- COMPLETE PHILIPPINE ADDRESS DATABASE
-- For Bus Booking System - School Project
-- Includes: Regions, Provinces, Cities/Municipalities, Barangays
-- ============================================

-- Create database if not exists
CREATE DATABASE IF NOT EXISTS bus_booking_system;
USE bus_booking_system;

-- Drop tables if they exist (in correct order due to foreign keys)
DROP TABLE IF EXISTS bookings;
DROP TABLE IF EXISTS bus_schedules;
DROP TABLE IF EXISTS bus_routes;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS barangays;
DROP TABLE IF EXISTS cities_municipalities;
DROP TABLE IF EXISTS provinces;
DROP TABLE IF EXISTS regions;

-- ============================================
-- 1. REGIONS TABLE
-- ============================================
CREATE TABLE regions (
    region_id INT PRIMARY KEY AUTO_INCREMENT,
    region_code VARCHAR(10) UNIQUE NOT NULL,
    region_name VARCHAR(100) NOT NULL,
    island_group ENUM('Luzon', 'Visayas', 'Mindanao') NOT NULL,
    INDEX idx_region_name (region_name),
    INDEX idx_island_group (island_group)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- 2. PROVINCES TABLE
-- ============================================
CREATE TABLE provinces (
    province_id INT PRIMARY KEY AUTO_INCREMENT,
    province_code VARCHAR(10) UNIQUE NOT NULL,
    province_name VARCHAR(100) NOT NULL,
    region_id INT NOT NULL,
    capital_city VARCHAR(100),
    FOREIGN KEY (region_id) REFERENCES regions(region_id) ON DELETE CASCADE,
    INDEX idx_province_name (province_name),
    INDEX idx_region (region_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- 3. CITIES/MUNICIPALITIES TABLE
-- ============================================
CREATE TABLE cities_municipalities (
    city_muni_id INT PRIMARY KEY AUTO_INCREMENT,
    city_muni_code VARCHAR(10) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    province_id INT NOT NULL,
    type ENUM('City', 'Municipality', 'Highly Urbanized City', 'Independent Component City') NOT NULL,
    income_class VARCHAR(20),
    population BIGINT,
    is_urban BOOLEAN DEFAULT FALSE,
    is_major_transport_hub BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (province_id) REFERENCES provinces(province_id) ON DELETE CASCADE,
    INDEX idx_city_name (name),
    INDEX idx_province (province_id),
    INDEX idx_type (type),
    INDEX idx_transport_hub (is_major_transport_hub)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- 4. BARANGAYS TABLE
-- ============================================
CREATE TABLE barangays (
    barangay_id INT PRIMARY KEY AUTO_INCREMENT,
    barangay_code VARCHAR(15) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    city_muni_id INT NOT NULL,
    population INT,
    is_urban BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (city_muni_id) REFERENCES cities_municipalities(city_muni_id) ON DELETE CASCADE,
    INDEX idx_barangay_name (name),
    INDEX idx_city_muni (city_muni_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- 5. USERS TABLE
-- ============================================
CREATE TABLE users (
    user_id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(50) NOT NULL,
    middle_name VARCHAR(50),
    last_name VARCHAR(50) NOT NULL,
    suffix VARCHAR(10),
    birthdate DATE,
    gender ENUM('Male', 'Female', 'Other'),
    
    -- Complete Philippine Address
    house_number_street VARCHAR(200),
    barangay_id INT,
    city_muni_id INT NOT NULL,
    province_id INT NOT NULL,
    region_id INT NOT NULL,
    zip_code VARCHAR(10),
    
    phone VARCHAR(15),
    mobile VARCHAR(15),
    is_admin BOOLEAN DEFAULT FALSE,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (barangay_id) REFERENCES barangays(barangay_id) ON DELETE SET NULL,
    FOREIGN KEY (city_muni_id) REFERENCES cities_municipalities(city_muni_id) ON DELETE CASCADE,
    FOREIGN KEY (province_id) REFERENCES provinces(province_id) ON DELETE CASCADE,
    FOREIGN KEY (region_id) REFERENCES regions(region_id) ON DELETE CASCADE,
    
    INDEX idx_username (username),
    INDEX idx_email (email),
    INDEX idx_name (last_name, first_name),
    INDEX idx_city (city_muni_id),
    INDEX idx_province_user (province_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- 6. BUS ROUTES TABLE
-- ============================================
CREATE TABLE bus_routes (
    route_id INT PRIMARY KEY AUTO_INCREMENT,
    route_code VARCHAR(20) UNIQUE NOT NULL,
    route_name VARCHAR(150) NOT NULL,
    
    -- Origin Address
    origin_city_muni_id INT NOT NULL,
    origin_terminal_name VARCHAR(100),
    origin_terminal_address VARCHAR(200),
    
    -- Destination Address
    destination_city_muni_id INT NOT NULL,
    destination_terminal_name VARCHAR(100),
    destination_terminal_address VARCHAR(200),
    
    distance_km DECIMAL(8,2),
    estimated_hours DECIMAL(5,2),
    base_fare DECIMAL(10,2) NOT NULL,
    route_type ENUM('Regular', 'Deluxe', 'Executive', 'Premium', 'Aircon', 'Ordinary') DEFAULT 'Regular',
    via_route VARCHAR(200),
    is_active BOOLEAN DEFAULT TRUE,
    
    FOREIGN KEY (origin_city_muni_id) REFERENCES cities_municipalities(city_muni_id) ON DELETE CASCADE,
    FOREIGN KEY (destination_city_muni_id) REFERENCES cities_municipalities(city_muni_id) ON DELETE CASCADE,
    
    INDEX idx_route_name (route_name),
    INDEX idx_origin (origin_city_muni_id),
    INDEX idx_destination (destination_city_muni_id),
    INDEX idx_route_search (origin_city_muni_id, destination_city_muni_id),
    INDEX idx_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- 7. BUS SCHEDULES TABLE
-- ============================================
CREATE TABLE bus_schedules (
    schedule_id INT PRIMARY KEY AUTO_INCREMENT,
    route_id INT NOT NULL,
    bus_number VARCHAR(20) NOT NULL,
    departure_time TIME NOT NULL,
    arrival_time TIME NOT NULL,
    travel_date DATE NOT NULL,
    total_seats INT DEFAULT 45,
    available_seats INT DEFAULT 45,
    fare DECIMAL(10,2) NOT NULL,
    bus_operator VARCHAR(100),
    bus_type ENUM('Regular', 'Aircon', 'Deluxe', 'Executive', 'Premium', 'Sleeper') DEFAULT 'Regular',
    amenities TEXT,
    driver_name VARCHAR(100),
    conductor_name VARCHAR(100),
    status ENUM('Scheduled', 'Departed', 'Arrived', 'Cancelled', 'Delayed') DEFAULT 'Scheduled',
    
    FOREIGN KEY (route_id) REFERENCES bus_routes(route_id) ON DELETE CASCADE,
    
    INDEX idx_travel_date (travel_date),
    INDEX idx_availability (available_seats),
    INDEX idx_bus_operator (bus_operator),
    INDEX idx_status (status),
    INDEX idx_departure (departure_time),
    UNIQUE INDEX idx_unique_schedule (route_id, departure_time, travel_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- 8. BOOKINGS TABLE
-- ============================================
CREATE TABLE bookings (
    booking_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    schedule_id INT NOT NULL,
    booking_reference VARCHAR(20) UNIQUE NOT NULL,
    
    -- Passenger Details
    passenger_first_name VARCHAR(50) NOT NULL,
    passenger_middle_name VARCHAR(50),
    passenger_last_name VARCHAR(50) NOT NULL,
    passenger_suffix VARCHAR(10),
    passenger_age INT,
    passenger_gender ENUM('Male', 'Female', 'Other'),
    passenger_contact VARCHAR(15),
    passenger_email VARCHAR(100),
    
    -- Passenger Address (simplified for booking)
    passenger_barangay VARCHAR(100),
    passenger_city_municipality VARCHAR(100),
    passenger_province VARCHAR(100),
    
    -- Booking Details
    seat_numbers VARCHAR(100) NOT NULL,
    number_of_seats INT NOT NULL,
    total_fare DECIMAL(10,2) NOT NULL,
    discount_amount DECIMAL(10,2) DEFAULT 0,
    net_fare DECIMAL(10,2) NOT NULL,
    
    booking_status ENUM('Confirmed', 'Pending', 'Cancelled', 'No-show', 'Completed') DEFAULT 'Confirmed',
    payment_status ENUM('Paid', 'Pending', 'Failed', 'Refunded') DEFAULT 'Pending',
    payment_method ENUM('Cash', 'GCash', 'PayMaya', 'Bank Transfer', 'Credit Card') DEFAULT 'Cash',
    
    booking_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    payment_date TIMESTAMP NULL,
    cancellation_date TIMESTAMP NULL,
    
    is_synced BOOLEAN DEFAULT TRUE,
    offline_id VARCHAR(50) DEFAULT NULL,
    notes TEXT,
    
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (schedule_id) REFERENCES bus_schedules(schedule_id) ON DELETE CASCADE,
    
    INDEX idx_user (user_id),
    INDEX idx_schedule (schedule_id),
    INDEX idx_booking_ref (booking_reference),
    INDEX idx_booking_date (booking_date),
    INDEX idx_status (booking_status),
    INDEX idx_payment_status (payment_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- INSERT PHILIPPINE REGIONS
-- ============================================
INSERT INTO regions (region_code, region_name, island_group) VALUES
-- LUZON
('NCR', 'National Capital Region', 'Luzon'),
('CAR', 'Cordillera Administrative Region', 'Luzon'),
('I', 'Ilocos Region', 'Luzon'),
('II', 'Cagayan Valley', 'Luzon'),
('III', 'Central Luzon', 'Luzon'),
('IV-A', 'CALABARZON', 'Luzon'),
('IV-B', 'MIMAROPA', 'Luzon'),
('V', 'Bicol Region', 'Luzon'),

-- VISAYAS
('VI', 'Western Visayas', 'Visayas'),
('VII', 'Central Visayas', 'Visayas'),
('VIII', 'Eastern Visayas', 'Visayas'),

-- MINDANAO
('IX', 'Zamboanga Peninsula', 'Mindanao'),
('X', 'Northern Mindanao', 'Mindanao'),
('XI', 'Davao Region', 'Mindanao'),
('XII', 'SOCCSKSARGEN', 'Mindanao'),
('XIII', 'Caraga', 'Mindanao'),
('BARMM', 'Bangsamoro Autonomous Region in Muslim Mindanao', 'Mindanao');

-- ============================================
-- INSERT PROVINCES
-- ============================================
INSERT INTO provinces (province_code, province_name, region_id, capital_city) VALUES
-- NCR
('NCR-MNL', 'Metro Manila', 1, 'Manila'),

-- Region I - Ilocos
('ILN', 'Ilocos Norte', 3, 'Laoag'),
('ILS', 'Ilocos Sur', 3, 'Vigan'),
('LUN', 'La Union', 3, 'San Fernando'),
('PAN', 'Pangasinan', 3, 'Lingayen'),

-- CAR - Cordillera
('BEN', 'Benguet', 2, 'La Trinidad'),

-- Region III - Central Luzon
('BUL', 'Bulacan', 5, 'Malolos'),
('PAM', 'Pampanga', 5, 'San Fernando'),
('TAR', 'Tarlac', 5, 'Tarlac City'),
('NUE', 'Nueva Ecija', 5, 'Palayan'),
('ZAM', 'Zambales', 5, 'Iba'),

-- Region IV-A - CALABARZON
('CAV', 'Cavite', 6, 'Imus'),
('LAG', 'Laguna', 6, 'Santa Cruz'),
('BAT', 'Batangas', 6, 'Batangas City'),
('RIZ', 'Rizal', 6, 'Antipolo'),
('QUE', 'Quezon', 6, 'Lucena'),

-- Region V - Bicol
('ALB', 'Albay', 8, 'Legazpi'),
('CAS', 'Camarines Sur', 8, 'Pili'),

-- Region VI - Western Visayas
('AKL', 'Aklan', 9, 'Kalibo'),
('ANT', 'Antique', 9, 'San Jose'),
('CAP', 'Capiz', 9, 'Roxas'),
('ILI', 'Iloilo', 9, 'Iloilo City'),
('NEC', 'Negros Occidental', 9, 'Bacolod'),

-- Region VII - Central Visayas
('CEB', 'Cebu', 10, 'Cebu City'),
('BOH', 'Bohol', 10, 'Tagbilaran'),
('NER', 'Negros Oriental', 10, 'Dumaguete'),
('SIG', 'Siquijor', 10, 'Siquijor'),

-- Region VIII - Eastern Visayas
('LEY', 'Leyte', 11, 'Tacloban'),
('SLE', 'Southern Leyte', 11, 'Maasin'),

-- Region IX - Zamboanga Peninsula
('ZAS', 'Zamboanga del Sur', 12, 'Pagadian'),
('ZAN', 'Zamboanga del Norte', 12, 'Dipolog'),
('ZSI', 'Zamboanga Sibugay', 12, 'Ipil'),

-- Region X - Northern Mindanao
('BUK', 'Bukidnon', 13, 'Malaybalay'),
('MSC', 'Misamis Occidental', 13, 'Oroquieta'),
('MSR', 'Misamis Oriental', 13, 'Cagayan de Oro'),
('LAN', 'Lanao del Norte', 13, 'Tubod'),

-- Region XI - Davao Region
('DAV', 'Davao del Sur', 14, 'Digos'),
('DAO', 'Davao Oriental', 14, 'Mati'),
('DAN', 'Davao del Norte', 14, 'Tagum'),

-- Region XII - SOCCSKSARGEN
('SCO', 'South Cotabato', 15, 'Koronadal'),
('NCO', 'North Cotabato', 15, 'Kidapawan'),
('SAR', 'Sarangani', 15, 'Alabel'),

-- Region XIII - Caraga
('AGN', 'Agusan del Norte', 16, 'Cabadbaran'),
('AGS', 'Agusan del Sur', 16, 'Prosperidad'),

-- BARMM
('MAG', 'Maguindanao', 17, 'Buluan'),
('LAS', 'Lanao del Sur', 17, 'Marawi');

-- ============================================
-- INSERT CITIES/MUNICIPALITIES
-- ============================================
INSERT INTO cities_municipalities (city_muni_code, name, province_id, type, is_major_transport_hub) VALUES
-- Metro Manila Cities
('MNL-MNL', 'Manila', 1, 'Highly Urbanized City', TRUE),
('MNL-QC', 'Quezon City', 1, 'Highly Urbanized City', TRUE),
('MNL-MKT', 'Makati', 1, 'Highly Urbanized City', TRUE),
('MNL-TAG', 'Taguig', 1, 'Highly Urbanized City', TRUE),
('MNL-PSG', 'Pasig', 1, 'Highly Urbanized City', TRUE),
('MNL-MND', 'Mandaluyong', 1, 'Highly Urbanized City', TRUE),
('MNL-MRK', 'Marikina', 1, 'Highly Urbanized City', TRUE),
('MNL-PRQ', 'Parañaque', 1, 'Highly Urbanized City', TRUE),

-- Ilocos Norte
('ILN-LAO', 'Laoag', 2, 'City', TRUE),
('ILN-BAC', 'Bacarra', 2, 'Municipality', FALSE),

-- Ilocos Sur
('ILS-VGN', 'Vigan', 3, 'City', TRUE),

-- La Union
('LUN-SFE', 'San Fernando', 4, 'City', TRUE),

-- Benguet (CAR)
('BEN-BAG', 'Baguio', 5, 'Highly Urbanized City', TRUE),

-- Bulacan
('BUL-MAL', 'Malolos', 6, 'City', TRUE),
('BUL-MEY', 'Meycauayan', 6, 'City', FALSE),

-- Pampanga
('PAM-ANG', 'Angeles', 7, 'Highly Urbanized City', TRUE),
('PAM-SFP', 'San Fernando', 7, 'City', TRUE),

-- Cavite
('CAV-BCR', 'Bacoor', 8, 'City', FALSE),
('CAV-IMS', 'Imus', 8, 'City', FALSE),

-- Batangas
('BAT-BTC', 'Batangas City', 9, 'City', TRUE),
('BAT-LPA', 'Lipa', 9, 'City', TRUE),

-- Laguna
('LAG-CLB', 'Calamba', 10, 'City', TRUE),
('LAG-SRO', 'Santa Rosa', 10, 'City', TRUE),

-- Albay (Bicol)
('ALB-LEG', 'Legazpi', 17, 'City', TRUE),

-- Camarines Sur
('CAS-NAG', 'Naga', 18, 'City', TRUE),

-- Iloilo (Western Visayas)
('ILI-ILO', 'Iloilo City', 19, 'Highly Urbanized City', TRUE),

-- Negros Occidental
('NEC-BCD', 'Bacolod', 20, 'Highly Urbanized City', TRUE),

-- Cebu (Central Visayas)
('CEB-CEB', 'Cebu City', 21, 'Highly Urbanized City', TRUE),
('CEB-MAN', 'Mandaue', 21, 'City', TRUE),
('CEB-LAP', 'Lapu-Lapu', 21, 'City', TRUE),

-- Bohol
('BOH-TAG', 'Tagbilaran', 22, 'City', TRUE),

-- Negros Oriental
('NER-DGT', 'Dumaguete', 23, 'City', TRUE),

-- Leyte (Eastern Visayas)
('LEY-TAC', 'Tacloban', 24, 'Highly Urbanized City', TRUE),

-- ZAMBOANGA DEL SUR
('ZAS-PAG', 'Pagadian', 25, 'City', TRUE),
('ZAS-ZAM', 'Zamboanga City', 25, 'Highly Urbanized City', TRUE),
('ZAS-MOL', 'Molave', 25, 'Municipality', FALSE),

-- ZAMBOANGA DEL NORTE
('ZAS-DIP', 'Dipolog', 26, 'City', TRUE),
('ZAS-DPT', 'Dapitan', 26, 'City', FALSE),

-- Misamis Oriental (Northern Mindanao)
('MSR-CDO', 'Cagayan de Oro', 29, 'Highly Urbanized City', TRUE),

-- Davao del Sur
('DAV-DVO', 'Davao City', 31, 'Highly Urbanized City', TRUE),

-- South Cotabato
('SCO-GEN', 'General Santos', 33, 'Highly Urbanized City', TRUE),

-- Agusan del Norte (Caraga)
('AGN-BTN', 'Butuan', 35, 'Highly Urbanized City', TRUE);

-- ============================================
-- INSERT BARANGAYS
-- ============================================
-- Manila Barangays
INSERT INTO barangays (barangay_code, name, city_muni_id) VALUES
('MNL-001', 'Barangay 1', 1),
('MNL-002', 'Barangay 2', 1),
('MNL-003', 'Barangay 3', 1),

-- Quezon City Barangays
('QC-001', 'Barangay Bahay Toro', 2),
('QC-002', 'Barangay Batasan Hills', 2),
('QC-003', 'Barangay Commonwealth', 2),

-- Zamboanga City Barangays
('ZAM-001', 'Barangay Ayala', 28),
('ZAM-002', 'Barangay Canelar', 28),
('ZAM-003', 'Barangay Guiwan', 28),
('ZAM-004', 'Barangay Mercedes', 28),
('ZAM-005', 'Barangay Putik', 28),

-- Pagadian City Barangays
('PAG-001', 'Barangay Balangasan', 27),
('PAG-002', 'Barangay Buenavista', 27),
('PAG-003', 'Barangay Gatas', 27),
('PAG-004', 'Barangay San Pedro', 27),
('PAG-005', 'Barangay Santa Lucia', 27),

-- Cebu City Barangays
('CEB-001', 'Barangay Lahug', 22),
('CEB-002', 'Barangay Mabolo', 22),
('CEB-003', 'Barangay Guadalupe', 22),

-- Davao City Barangays
('DVO-001', 'Barangay Agdao', 32),
('DVO-002', 'Barangay Bucana', 32),
('DVO-003', 'Barangay Toril', 32),

-- Baguio City Barangays
('BAG-001', 'Barangay Session Road', 11),
('BAG-002', 'Barangay Camp 7', 11),
('BAG-003', 'Barangay Loakan', 11);

-- ============================================
-- INSERT USERS
-- ============================================
-- Password for all: password123 (SHA256 hash)
INSERT INTO users (username, email, password_hash, first_name, last_name, 
                   house_number_street, barangay_id, city_muni_id, province_id, region_id, 
                   zip_code, phone, mobile, is_admin) VALUES
-- Admin from Manila
('admin', 'admin@busbooking.ph', 'ef797c8118f02dfb649607dd5d3f8c7623048c9c063d532cc95c5ed7a898a64f',
 'Juan', 'Dela Cruz', '123 Rizal Street', 1, 1, 1, 1, '1000', '02-1234567', '09171234567', TRUE),

-- User from Zamboanga City
('zambo_user', 'zambo@email.com', 'ef797c8118f02dfb649607dd5d3f8c7623048c9c063d532cc95c5ed7a898a64f',
 'Maria', 'Santos', '456 Veterans Avenue', 4, 28, 25, 12, '7000', NULL, '09181234567', FALSE),

-- User from Pagadian City
('pagadian_user', 'pagadian@email.com', 'ef797c8118f02dfb649607dd5d3f8c7623048c9c063d532cc95c5ed7a898a64f',
 'Pedro', 'Reyes', '789 San Pedro Street', 19, 27, 25, 12, '7016', NULL, '09191234567', FALSE),

-- User from Cebu
('cebu_user', 'cebu@email.com', 'ef797c8118f02dfb649607dd5d3f8c7623048c9c063d532cc95c5ed7a898a64f',
 'Ana', 'Garcia', '321 Osmeña Boulevard', 16, 22, 21, 10, '6000', '032-1234567', '09201234567', FALSE),

-- User from Davao
('davao_user', 'davao@email.com', 'ef797c8118f02dfb649607dd5d3f8c7623048c9c063d532cc95c5ed7a898a64f',
 'Luis', 'Torres', '654 Roxas Avenue', 22, 32, 31, 14, '8000', '082-1234567', '09211234567', FALSE);

-- ============================================
-- INSERT BUS ROUTES
-- ============================================
INSERT INTO bus_routes (route_code, route_name, origin_city_muni_id, origin_terminal_name, 
                        destination_city_muni_id, destination_terminal_name, distance_km, 
                        estimated_hours, base_fare, route_type, via_route) VALUES
-- Manila to Baguio
('MNLBAG', 'Manila to Baguio', 1, 'Victory Liner Cubao Terminal', 11, 'Victory Liner Baguio Terminal', 
 250, 6, 850, 'Deluxe', 'NLEX, SCTEX, TPLEX'),

-- Zamboanga to Manila
('ZAMMNL', 'Zamboanga to Manila', 28, 'Zamboanga City Integrated Bus Terminal', 1, 'Pasay Buendia Bus Terminal',
 1100, 30, 2200, 'Premium', 'RORO via Cebu, Ferry'),

-- Pagadian to Manila
('PAGMNL', 'Pagadian to Manila', 27, 'Pagadian City Bus Terminal', 1, 'Cubao Bus Terminal',
 1050, 28, 2100, 'Premium', 'RORO via Cebu'),

-- Manila to Bicol
('MNLBIC', 'Manila to Legazpi', 1, 'Cubao Bus Terminal', 17, 'Legazpi Grand Terminal',
 500, 10, 1250, 'Deluxe', 'SLEX, STAR Tollway'),

-- Cebu to Bohol
('CEBBOH', 'Cebu to Tagbilaran', 22, 'Cebu Pier 1', 23, 'Tagbilaran City Port',
 72, 2, 400, 'Regular', 'Fast Ferry'),

-- Davao to Cagayan de Oro
('DVOCDO', 'Davao to Cagayan de Oro', 32, 'Davao Overland Transport Terminal', 29, 'Cagayan de Oro Bus Terminal',
 280, 6, 600, 'Deluxe', 'Bukidnon-Davao Road'),

-- Zamboanga to Cagayan de Oro
('ZAMCDO', 'Zamboanga to Cagayan de Oro', 28, 'Zamboanga City Bus Terminal', 29, 'Cagayan de Oro Integrated Terminal',
 450, 10, 1000, 'Deluxe', 'Sayre Highway'),

-- Pagadian to Zamboanga
('PAGZAM', 'Pagadian to Zamboanga', 27, 'Pagadian City Terminal', 28, 'Zamboanga City Terminal',
 200, 4, 450, 'Regular', 'National Highway'),

-- Manila to Cebu (RORO)
('MNLCEB', 'Manila to Cebu', 1, 'Manila North Harbor', 22, 'Cebu Pier 3',
 600, 24, 1600, 'Premium', '2GO Travel, Ferry'),

-- Davao to Manila
('DVOMNL', 'Davao to Manila', 32, 'Davao EcoWest Terminal', 1, 'Pasay Buendia Terminal',
 1500, 48, 3000, 'Premium', 'RORO via Matnog');

-- ============================================
-- INSERT BUS SCHEDULES
-- ============================================
INSERT INTO bus_schedules (route_id, bus_number, departure_time, arrival_time, travel_date, 
                           total_seats, available_seats, fare, bus_operator, bus_type, amenities) VALUES
-- Zamboanga to Manila schedules
(2, 'PH-ZM-001', '18:00:00', '00:00:00', CURDATE() + INTERVAL 2 DAY, 45, 25, 2200, 'RORO Bus', 'Premium', 'Aircon, Bunks, Toilet, Meal'),
(2, 'PH-ZM-002', '19:00:00', '01:00:00', CURDATE() + INTERVAL 3 DAY, 45, 18, 2400, 'SuperFerry', 'Premium', 'Aircon, Cabin, WiFi, Meals'),

-- Pagadian to Manila
(3, 'PH-PM-001', '17:00:00', '21:00:00', CURDATE() + INTERVAL 2 DAY, 45, 20, 2100, 'RORO Bus', 'Premium', 'Aircon, Bunks, Toilet'),
(3, 'PH-PM-002', '18:00:00', '22:00:00', CURDATE() + INTERVAL 3 DAY, 45, 15, 2200, 'SuperCat', 'Premium', 'Aircon, Cabin, WiFi'),

-- Manila to Baguio
(1, 'PH-MB-001', '06:00:00', '12:00:00', CURDATE() + INTERVAL 1 DAY, 45, 30, 850, 'Victory Liner', 'Deluxe', 'Aircon, TV, Reclining Seats'),
(1, 'PH-MB-002', '22:00:00', '04:00:00', CURDATE() + INTERVAL 2 DAY, 45, 40, 800, 'Solid North', 'Regular', 'Aircon, TV'),

-- Zamboanga to Cagayan de Oro
(7, 'PH-ZC-001', '08:00:00', '18:00:00', CURDATE() + INTERVAL 1 DAY, 45, 30, 1000, 'Rural Transit', 'Deluxe', 'Aircon, TV, Reclining'),
(7, 'PH-ZC-002', '09:00:00', '19:00:00', CURDATE() + INTERVAL 2 DAY, 45, 22, 1100, 'Bachelor Express', 'Executive', 'Aircon, WiFi, Snack'),

-- Pagadian to Zamboanga
(8, 'PH-PZ-001', '07:00:00', '11:00:00', CURDATE() + INTERVAL 1 DAY, 45, 35, 450, 'Rural Transit', 'Regular', 'Aircon'),
(8, 'PH-PZ-002', '13:00:00', '17:00:00', CURDATE() + INTERVAL 1 DAY, 45, 28, 500, 'Bachelor Express', 'Deluxe', 'Aircon, TV');

-- ============================================
-- INSERT SAMPLE BOOKINGS
-- ============================================
INSERT INTO bookings (user_id, schedule_id, booking_reference, 
                      passenger_first_name, passenger_last_name, passenger_age, passenger_gender,
                      passenger_barangay, passenger_city_municipality, passenger_province,
                      seat_numbers, number_of_seats, total_fare, discount_amount, net_fare,
                      booking_status, payment_status, payment_method) VALUES
(2, 1, 'BKP202412001', 'Maria', 'Santos', 25, 'Female', 'Guiwan', 'Zamboanga City', 'Zamboanga del Sur',
 'Seat-10, Seat-11', 2, 4400, 0, 4400, 'Confirmed', 'Paid', 'GCash'),

(3, 3, 'BKP202412002', 'Pedro', 'Reyes', 30, 'Male', 'San Pedro', 'Pagadian City', 'Zamboanga del Sur',
 'Seat-5', 1, 2100, 100, 2000, 'Confirmed', 'Paid', 'Cash'),

(4, 5, 'BKP202412003', 'Ana', 'Garcia', 28, 'Female', 'Lahug', 'Cebu City', 'Cebu',
 'Seat-15, Seat-16', 2, 1700, 0, 1700, 'Confirmed', 'Paid', 'Credit Card');

-- ============================================
-- UPDATE AVAILABLE SEATS
-- ============================================
UPDATE bus_schedules SET available_seats = available_seats - 2 WHERE schedule_id = 1;
UPDATE bus_schedules SET available_seats = available_seats - 1 WHERE schedule_id = 3;
UPDATE bus_schedules SET available_seats = available_seats - 2 WHERE schedule_id = 5;

-- ============================================
-- VERIFY DATA
-- ============================================
SELECT '✅ DATABASE SETUP COMPLETE!' as 'STATUS';
SELECT CONCAT('📊 Total Regions: ', COUNT(*)) as 'SUMMARY' FROM regions
UNION ALL
SELECT CONCAT('📊 Total Provinces: ', COUNT(*)) FROM provinces
UNION ALL
SELECT CONCAT('📊 Total Cities/Municipalities: ', COUNT(*)) FROM cities_municipalities
UNION ALL
SELECT CONCAT('📊 Total Barangays: ', COUNT(*)) FROM barangays
UNION ALL
SELECT CONCAT('📊 Total Users: ', COUNT(*)) FROM users
UNION ALL
SELECT CONCAT('📊 Total Bus Routes: ', COUNT(*)) FROM bus_routes
UNION ALL
SELECT CONCAT('📊 Total Bus Schedules: ', COUNT(*)) FROM bus_schedules
UNION ALL
SELECT CONCAT('📊 Total Bookings: ', COUNT(*)) FROM bookings;