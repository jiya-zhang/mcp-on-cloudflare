-- Database schema for busyness monitoring data
-- Run this in your Cloudflare D1 database

CREATE TABLE IF NOT EXISTS busyness_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    score INTEGER NOT NULL CHECK (score >= 1 AND score <= 10),
    motion_ratio REAL,
    edge_ratio REAL,
    color_variance REAL,
    texture_variance REAL,
    contour_count INTEGER,
    combined_raw REAL,
    metadata TEXT, -- JSON string with additional metadata
    notes TEXT, -- User-provided notes/context
    camera_name TEXT, -- Camera identifier/name
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Create index for efficient querying by timestamp
CREATE INDEX IF NOT EXISTS idx_busyness_timestamp ON busyness_data(timestamp);

-- Create index for efficient querying by score
CREATE INDEX IF NOT EXISTS idx_busyness_score ON busyness_data(score);
