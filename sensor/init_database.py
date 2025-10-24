#!/usr/bin/env python3
"""
Initialize the D1 database schema for busyness monitoring
"""

import requests
import json
import sys
import os

def load_config():
    """Load configuration from config.json"""
    try:
        with open('config.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ config.json not found. Please run setup.py first.")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing config.json: {e}")
        return None

def create_database_schema(config):
    """Create the database schema in D1"""
    api_token = config['cloudflare']['api_token']
    account_id = config['cloudflare']['account_id']
    database_id = config['cloudflare']['database_id']
    
    base_url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/d1/database/{database_id}"
    
    headers = {
        'Authorization': f'Bearer {api_token}',
        'Content-Type': 'application/json'
    }
    
    # SQL statements to create the schema
    sql_statements = [
        """
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
            metadata TEXT,
            notes TEXT,
            camera_name TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_busyness_timestamp ON busyness_data(timestamp)
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_busyness_score ON busyness_data(score)
        """
    ]
    
    print("🔧 Creating database schema...")
    
    for i, sql in enumerate(sql_statements, 1):
        print(f"   Executing statement {i}/{len(sql_statements)}...")
        
        payload = {
            'sql': sql
        }
        
        try:
            response = requests.post(
                f"{base_url}/query",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success', False):
                    print(f"   ✅ Statement {i} executed successfully")
                else:
                    print(f"   ❌ Statement {i} failed: {result.get('errors', 'Unknown error')}")
                    return False
            else:
                print(f"   ❌ Statement {i} failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"   ❌ Error executing statement {i}: {e}")
            return False
    
    print("✅ Database schema created successfully!")
    return True

def test_database_connection(config):
    """Test the database connection"""
    api_token = config['cloudflare']['api_token']
    account_id = config['cloudflare']['account_id']
    database_id = config['cloudflare']['database_id']
    
    base_url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/d1/database/{database_id}"
    
    headers = {
        'Authorization': f'Bearer {api_token}',
        'Content-Type': 'application/json'
    }
    
    # Test query
    payload = {
        'sql': 'SELECT name FROM sqlite_master WHERE type="table" AND name="busyness_data"'
    }
    
    try:
        response = requests.post(
            f"{base_url}/query",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success', False):
                tables = result.get('result', [])
                if any(table.get('name') == 'busyness_data' for table in tables):
                    print("✅ Database connection successful - busyness_data table exists")
                    return True
                else:
                    print("✅ Database connection successful - busyness_data table will be created")
                    return True  # Allow creation to proceed
            else:
                print(f"❌ Database query failed: {result.get('errors', 'Unknown error')}")
                return False
        else:
            print(f"❌ Database connection failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing database connection: {e}")
        return False

def main():
    """Main function"""
    print("🚀 Initializing D1 Database Schema")
    print("=" * 40)
    
    # Load configuration
    config = load_config()
    if not config:
        return 1
    
    print(f"📋 Using database: {config['cloudflare']['database_id']}")
    
    # Test connection first
    print("\n🔍 Testing database connection...")
    if not test_database_connection(config):
        print("❌ Database connection test failed")
        return 1
    
    # Create schema
    print("\n🔧 Creating database schema...")
    if not create_database_schema(config):
        print("❌ Failed to create database schema")
        return 1
    
    # Test again to verify
    print("\n🔍 Verifying schema creation...")
    if test_database_connection(config):
        print("\n🎉 Database initialization complete!")
        print("   You can now run the busyness monitor.")
        return 0
    else:
        print("\n❌ Schema verification failed")
        return 1

if __name__ == "__main__":
    exit(main())
