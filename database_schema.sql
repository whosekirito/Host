-- Database schema for Oppai Xd file hosting platform

-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(20) UNIQUE NOT NULL,
    username VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    plan VARCHAR(20) DEFAULT 'free',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Files table
CREATE TABLE files (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(20) NOT NULL,
    original_name VARCHAR(255) NOT NULL,
    stored_name VARCHAR(255) NOT NULL,
    file_size BIGINT NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Plans table (for admin to manage pricing)
CREATE TABLE plans (
    id SERIAL PRIMARY KEY,
    plan_name VARCHAR(20) UNIQUE NOT NULL,
    price INTEGER NOT NULL, -- in paise (Indian currency)
    max_files INTEGER NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Insert default plans
INSERT INTO plans (plan_name, price, max_files, description) VALUES
('free', 0, 1, 'Free plan with 1 file upload'),
('basic', 29900, 10, 'Basic plan with 10 file uploads'),
('premium', 79900, 50, 'Premium plan with 50 file uploads'),
('pro', 199900, 200, 'Pro plan with 200 file uploads');

-- Create indexes for better performance
CREATE INDEX idx_users_user_id ON users(user_id);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_files_user_id ON files(user_id);
CREATE INDEX idx_files_created_at ON files(created_at);