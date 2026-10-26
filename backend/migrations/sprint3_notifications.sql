CREATE TABLE IF NOT EXISTS app_auth.notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES app_auth.users(id),
    message TEXT NOT NULL,
    type VARCHAR(50),
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
