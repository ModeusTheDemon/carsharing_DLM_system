-- ==========================================
-- Add archive.payments_archive table for DLM worker
-- ==========================================

CREATE TABLE IF NOT EXISTS archive.payments_archive (
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
