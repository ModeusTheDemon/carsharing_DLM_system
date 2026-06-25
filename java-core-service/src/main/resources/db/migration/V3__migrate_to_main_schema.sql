-- ==========================================
-- Миграция данных из схемы public в схему main
-- ==========================================

-- 1. Создаем схему main, если она не существует
CREATE SCHEMA IF NOT EXISTS main;

-- 2. Создаем таблицу users в схеме main (если не существует)
CREATE TABLE IF NOT EXISTS main.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(20),
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Создаем таблицу vehicles в схеме main (если не существует)
CREATE TABLE IF NOT EXISTS main.vehicles (
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

-- 4. Создаем таблицу rides в схеме main (если не существует)
CREATE TABLE IF NOT EXISTS main.rides (
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

-- 5. Создаем таблицу payments в схеме main (если не существует) - ЭТО ГЛАВНАЯ ТАБЛИЦА, КОТОРОЙ НЕ ХВАТАЕТ!
CREATE TABLE IF NOT EXISTS main.payments (
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

-- 6. Создаем таблицу telemetry в схеме main (если не существует)
CREATE TABLE IF NOT EXISTS main.telemetry (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ride_id UUID NOT NULL,
    vehicle_id UUID NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    data TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 7. Создаем внешние ключи для таблицы rides
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_rides_user' AND table_schema = 'main' AND table_name = 'rides'
    ) THEN
        ALTER TABLE main.rides ADD CONSTRAINT fk_rides_user FOREIGN KEY (user_id) REFERENCES main.users(id);
    END IF;
    
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_rides_vehicle' AND table_schema = 'main' AND table_name = 'rides'
    ) THEN
        ALTER TABLE main.rides ADD CONSTRAINT fk_rides_vehicle FOREIGN KEY (vehicle_id) REFERENCES main.vehicles(id);
    END IF;
END $$;

-- 8. Создаем внешние ключи для таблицы payments
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_payments_ride' AND table_schema = 'main' AND table_name = 'payments'
    ) THEN
        ALTER TABLE main.payments ADD CONSTRAINT fk_payments_ride FOREIGN KEY (ride_id) REFERENCES main.rides(id);
    END IF;
    
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_payments_user' AND table_schema = 'main' AND table_name = 'payments'
    ) THEN
        ALTER TABLE main.payments ADD CONSTRAINT fk_payments_user FOREIGN KEY (user_id) REFERENCES main.users(id);
    END IF;
END $$;

-- 9. Создаем внешние ключи для таблицы telemetry
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_telemetry_ride' AND table_schema = 'main' AND table_name = 'telemetry'
    ) THEN
        ALTER TABLE main.telemetry ADD CONSTRAINT fk_telemetry_ride FOREIGN KEY (ride_id) REFERENCES main.rides(id);
    END IF;
    
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_telemetry_vehicle' AND table_schema = 'main' AND table_name = 'telemetry'
    ) THEN
        ALTER TABLE main.telemetry ADD CONSTRAINT fk_telemetry_vehicle FOREIGN KEY (vehicle_id) REFERENCES main.vehicles(id);
    END IF;
END $$;

-- 10. Создаем индексы для улучшения производительности
CREATE INDEX IF NOT EXISTS idx_users_email ON main.users(email);
CREATE INDEX IF NOT EXISTS idx_users_is_deleted ON main.users(is_deleted);

CREATE INDEX IF NOT EXISTS idx_vehicles_plate_number ON main.vehicles(plate_number);
CREATE INDEX IF NOT EXISTS idx_vehicles_status ON main.vehicles(status);

CREATE INDEX IF NOT EXISTS idx_rides_user_id ON main.rides(user_id);
CREATE INDEX IF NOT EXISTS idx_rides_vehicle_id ON main.rides(vehicle_id);
CREATE INDEX IF NOT EXISTS idx_rides_status ON main.rides(status);
CREATE INDEX IF NOT EXISTS idx_rides_created_at ON main.rides(created_at);

CREATE INDEX IF NOT EXISTS idx_payments_ride_id ON main.payments(ride_id);
CREATE INDEX IF NOT EXISTS idx_payments_user_id ON main.payments(user_id);
CREATE INDEX IF NOT EXISTS idx_payments_status ON main.payments(status);
CREATE INDEX IF NOT EXISTS idx_payments_created_at ON main.payments(created_at);

CREATE INDEX IF NOT EXISTS idx_telemetry_ride_id ON main.telemetry(ride_id);
CREATE INDEX IF NOT EXISTS idx_telemetry_vehicle_id ON main.telemetry(vehicle_id);
CREATE INDEX IF NOT EXISTS idx_telemetry_timestamp ON main.telemetry(timestamp);

-- 11. Комментарии к таблицам
COMMENT ON TABLE main.users IS 'Пользователи каршеринга';
COMMENT ON TABLE main.vehicles IS 'Транспортные средства';
COMMENT ON TABLE main.rides IS 'Поездки';
COMMENT ON TABLE main.payments IS 'Платежи за поездки';
COMMENT ON TABLE main.telemetry IS 'Телеметрия транспортных средств';

-- 12. Если в схеме public есть таблицы с данными, можно их перенести
-- (пока пропускаем, так как это тестовая среда)