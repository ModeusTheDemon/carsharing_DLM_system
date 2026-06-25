-- ==========================================
-- ПОЛНОЕ ПЕРЕСОЗДАНИЕ БАЗЫ ДАННЫХ CARSHARING
-- ==========================================
-- Удаляем старую базу и создаем новую
-- DROP DATABASE IF EXISTS carsharing_db WITH (FORCE);
-- CREATE DATABASE carsharing_db;

-- ==========================================
-- СХЕМА MAIN (для Java-сервиса)
-- ==========================================
CREATE SCHEMA IF NOT EXISTS main;

-- Таблица пользователей
CREATE TABLE main.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(20),
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP,
    terms_accepted BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица транспортных средств
CREATE TABLE main.vehicles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    brand VARCHAR(100) NOT NULL,
    model VARCHAR(100) NOT NULL,
    plate_number VARCHAR(20) UNIQUE NOT NULL,
    color VARCHAR(50),
    status VARCHAR(20) DEFAULT 'available',
    current_location TEXT,
    fuel_level DOUBLE PRECISION DEFAULT 100.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица поездок
CREATE TABLE main.rides (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    vehicle_id UUID NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    start_location TEXT NOT NULL,
    end_location TEXT,
    total_cost DECIMAL(10, 2),
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица платежей
CREATE TABLE main.payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ride_id UUID NOT NULL,
    user_id UUID NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'RUB',
    status VARCHAR(20) DEFAULT 'pending',
    payment_method VARCHAR(50),
    transaction_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- Таблица телеметрии
CREATE TABLE main.telemetry (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ride_id UUID NOT NULL,
    vehicle_id UUID NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    data TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Внешние ключи для rides
ALTER TABLE main.rides ADD CONSTRAINT fk_rides_user FOREIGN KEY (user_id) REFERENCES main.users(id);
ALTER TABLE main.rides ADD CONSTRAINT fk_rides_vehicle FOREIGN KEY (vehicle_id) REFERENCES main.vehicles(id);

-- Внешние ключи для payments
ALTER TABLE main.payments ADD CONSTRAINT fk_payments_ride FOREIGN KEY (ride_id) REFERENCES main.rides(id);
ALTER TABLE main.payments ADD CONSTRAINT fk_payments_user FOREIGN KEY (user_id) REFERENCES main.users(id);

-- Внешние ключи для telemetry
ALTER TABLE main.telemetry ADD CONSTRAINT fk_telemetry_ride FOREIGN KEY (ride_id) REFERENCES main.rides(id);
ALTER TABLE main.telemetry ADD CONSTRAINT fk_telemetry_vehicle FOREIGN KEY (vehicle_id) REFERENCES main.vehicles(id);

-- Индексы для main schema
CREATE INDEX idx_users_email ON main.users(email);
CREATE INDEX idx_users_is_deleted ON main.users(is_deleted);
CREATE INDEX idx_vehicles_plate_number ON main.vehicles(plate_number);
CREATE INDEX idx_vehicles_status ON main.vehicles(status);
CREATE INDEX idx_rides_user_id ON main.rides(user_id);
CREATE INDEX idx_rides_vehicle_id ON main.rides(vehicle_id);
CREATE INDEX idx_rides_status ON main.rides(status);
CREATE INDEX idx_rides_created_at ON main.rides(created_at);
CREATE INDEX idx_payments_ride_id ON main.payments(ride_id);
CREATE INDEX idx_payments_user_id ON main.payments(user_id);
CREATE INDEX idx_payments_status ON main.payments(status);
CREATE INDEX idx_payments_created_at ON main.payments(created_at);
CREATE INDEX idx_telemetry_ride_id ON main.telemetry(ride_id);
CREATE INDEX idx_telemetry_vehicle_id ON main.telemetry(vehicle_id);
CREATE INDEX idx_telemetry_timestamp ON main.telemetry(timestamp);

-- Комментарии
COMMENT ON TABLE main.users IS 'Пользователи каршеринга';
COMMENT ON TABLE main.vehicles IS 'Транспортные средства';
COMMENT ON TABLE main.rides IS 'Поездки';
COMMENT ON TABLE main.payments IS 'Платежи за поездки';
COMMENT ON TABLE main.telemetry IS 'Телеметрия транспортных средств';

-- ==========================================
-- СХЕМА ARCHIVE (для Python-DLM worker)
-- ==========================================
CREATE SCHEMA IF NOT EXISTS archive;

-- Таблица архивных поездок
CREATE TABLE archive.rides (
    id NUMERIC PRIMARY KEY,
    user_id NUMERIC NOT NULL,
    car_id NUMERIC NOT NULL,
    status VARCHAR(50) NOT NULL,
    end_reason VARCHAR(50),
    started_at TIMESTAMP NOT NULL,
    finished_at TIMESTAMP,
    total_cost NUMERIC(10, 2),
    archived_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица архивных платежей
CREATE TABLE archive.payments_archive (
    id UUID PRIMARY KEY,
    ride_id UUID NOT NULL,
    user_id UUID NOT NULL,
    amount NUMERIC(10, 2) NOT NULL,
    currency VARCHAR(3) NOT NULL,
    status VARCHAR(20) NOT NULL,
    payment_method VARCHAR(50),
    created_at TIMESTAMP NOT NULL,
    archived_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Индексы для archive schema
CREATE INDEX idx_archive_rides_id ON archive.rides(id);
CREATE INDEX idx_archive_rides_started_at ON archive.rides(started_at);
CREATE INDEX idx_archive_payments_id ON archive.payments_archive(id);
CREATE INDEX idx_archive_payments_created_at ON archive.payments_archive(created_at);

-- Комментарии
COMMENT ON TABLE archive.rides IS 'Архивные поездки';
COMMENT ON TABLE archive.payments_archive IS 'Архивные платежи';

-- ==========================================
-- СХЕМА PUBLIC (справочники для совместимости)
-- ==========================================
-- Справочник цветов автомобилей
CREATE TABLE IF NOT EXISTS public.car_colors (
    id serial PRIMARY KEY,
    name varchar(50) NOT NULL UNIQUE
);

-- Наполнение справочника
INSERT INTO public.car_colors (name) VALUES ('Белый'), ('Черный'), ('Серый'), ('Синий') ON CONFLICT DO NOTHING;
