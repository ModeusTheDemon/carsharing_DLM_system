-- ==========================================
-- 1. СОЗДАНИЕ СТИЛЕЙ, ТИПОВ И СПРАВОЧНИКОВ
-- ==========================================

-- Причины завершения поездки
CREATE TYPE ride_end_reason AS ENUM ('REGULAR', 'VIOLATION', 'ACCIDENT', 'TECHNICAL_ISSUE');

-- Справочник цветов автомобилей
CREATE TABLE public.car_colors (
                                   id serial PRIMARY KEY,
                                   name varchar(50) NOT NULL UNIQUE
);

-- Наполнение справочника цветов первичными данными
INSERT INTO public.car_colors (name) VALUES ('Белый'), ('Черный'), ('Серый'), ('Синий');

-- ==========================================
-- 2. ОСНОВНЫЕ ТАБЛИЦЫ (СХЕМА PUBLIC)
-- ==========================================

-- Таблица пользователей
CREATE TABLE public.users (
                              id bigserial PRIMARY KEY,
                              name varchar(255) NOT NULL,
                              email varchar(255) NOT NULL UNIQUE,
                              password_hash varchar(255) NOT NULL,
                              rating numeric(3, 2) NOT NULL DEFAULT 5.00,
                              status varchar(50) NOT NULL DEFAULT 'ACTIVE', -- ACTIVE, BLOCKED, DELETED
                              registration_date timestamp with time zone NOT NULL DEFAULT now()
);

-- Таблица документов пользователей
CREATE TABLE public.user_documents (
                                       id bigserial PRIMARY KEY,
                                       user_id bigint NOT NULL,
                                       document_type varchar(50) NOT NULL, -- PASSPORT, DRIVERS_LICENSE
                                       document_number varchar(100) NOT NULL,
                                       issued_at date NOT NULL,
                                       is_verified boolean NOT NULL DEFAULT false,
                                       updated_at timestamp with time zone NOT NULL DEFAULT now(),
                                       CONSTRAINT fk_documents_user FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE
);

-- Таблица банковских карт
CREATE TABLE public.user_cards (
                                   id bigserial PRIMARY KEY,
                                   user_id bigint NOT NULL,
                                   card_token varchar(255) NOT NULL,
                                   masked_pan varchar(19) NOT NULL,
                                   is_main boolean NOT NULL DEFAULT false,
                                   created_at timestamp with time zone NOT NULL DEFAULT now(),
                                   CONSTRAINT fk_cards_user FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE
);

-- Таблица автомобилей
CREATE TABLE public.cars (
                             id bigserial PRIMARY KEY,
                             brand varchar(100) NOT NULL,
                             model varchar(100) NOT NULL,
                             plate_number varchar(20) NOT NULL UNIQUE,
                             color_id integer NOT NULL,
                             status varchar(50) NOT NULL DEFAULT 'AVAILABLE', -- AVAILABLE, RENTED, MAINTENANCE
                             CONSTRAINT fk_cars_color FOREIGN KEY (color_id) REFERENCES public.car_colors(id)
);

-- Таблица поездок
CREATE TABLE public.rides (
                              id bigserial PRIMARY KEY,
                              user_id bigint NOT NULL,
                              car_id bigint NOT NULL,
                              status varchar(50) NOT NULL DEFAULT 'STARTED', -- STARTED, COMPLETED, CANCELED
                              end_reason ride_end_reason,                   -- Заполняется только при завершении
                              started_at timestamp with time zone NOT NULL DEFAULT now(),
                              finished_at timestamp with time zone,
                              total_cost numeric(10, 2) DEFAULT 0.00,
                              CONSTRAINT fk_rides_user FOREIGN KEY (user_id) REFERENCES public.users(id),
                              CONSTRAINT fk_rides_car FOREIGN KEY (car_id) REFERENCES public.cars(id)
);

-- Таблица телеметрии
CREATE TABLE public.car_telemetry (
                                      id bigserial PRIMARY KEY,
                                      car_id bigint NOT NULL,
                                      latitude numeric(9, 6) NOT NULL,
                                      longitude numeric(9, 6) NOT NULL,
                                      speed integer NOT NULL,
                                      fuel_level integer NOT NULL,
                                      created_at timestamp with time zone NOT NULL DEFAULT now()
);

-- ==========================================
-- 3. АРХИВНАЯ СХЕМА (ДЛЯ PYTHON DLM)
-- ==========================================
CREATE SCHEMA IF NOT EXISTS archive;

CREATE TABLE archive.rides (
                               id bigint PRIMARY KEY, -- Без serial, переносим оригинальный ID
                               user_id bigint NOT NULL,
                               car_id bigint NOT NULL,
                               status varchar(50) NOT NULL,
                               end_reason varchar(50),
                               started_at timestamp with time zone NOT NULL,
                               finished_at timestamp with time zone,
                               total_cost numeric(10, 2),
                               archived_at timestamp with time zone NOT NULL DEFAULT now()
);