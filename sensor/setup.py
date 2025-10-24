#!/usr/bin/env python3
"""
Setup script for MacBook Camera Busyness Monitor
This script helps you set up and configure the system
"""

import os
import sys
import subprocess
import json

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 7):
        print("❌ Python 3.7 or higher is required")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    return True

def install_dependencies():
    """Install required Python packages"""
    print("📦 Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def check_camera_access():
    """Check if camera is accessible"""
    print("📷 Checking camera access...")
    try:
        import cv2
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("❌ Camera not accessible. Please check camera permissions.")
            return False
        cap.release()
        print("✅ Camera is accessible")
        return True
    except ImportError:
        print("❌ OpenCV not installed. Run 'pip install -r requirements.txt' first.")
        return False
    except Exception as e:
        print(f"❌ Camera check failed: {e}")
        return False

def create_config_template():
    """Create a configuration template file"""
    config_template = {
        "cloudflare": {
            "api_token": "YOUR_API_TOKEN_HERE",
            "account_id": "YOUR_ACCOUNT_ID_HERE",
            "database_id": "YOUR_DATABASE_ID_HERE"
        },
        "camera": {
            "index": 0,
            "interval": 30
        },
        "logging": {
            "level": "INFO",
            "file": "busyness_monitor.log"
        }
    }
    
    config_path = "config.json"
    if not os.path.exists(config_path):
        with open(config_path, 'w') as f:
            json.dump(config_template, f, indent=2)
        print(f"✅ Configuration template created: {config_path}")
        print("   Please edit the configuration file with your Cloudflare credentials")
    else:
        print(f"✅ Configuration file already exists: {config_path}")
    
    return config_path

def run_tests():
    """Run system tests"""
    print("🧪 Running system tests...")
    try:
        result = subprocess.run([sys.executable, "test_system.py"], 
                              capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            print("✅ All tests passed")
            return True
        else:
            print(f"❌ Tests failed: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("❌ Tests timed out")
        return False
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False

def show_next_steps():
    """Show next steps to the user"""
    print("\n" + "="*60)
    print("🎉 Setup Complete! Next Steps:")
    print("="*60)
    print()
    print("1. 📝 Edit config.json with your Cloudflare credentials:")
    print("   - Get your API token from: https://dash.cloudflare.com/profile/api-tokens")
    print("   - Get your Account ID from: https://dash.cloudflare.com/")
    print("   - Your Database ID is: c934d24d-3b7e-49b8-ba4d-b2c696aa8958")
    print()
    print("2. 🚀 Deploy your Cloudflare Worker:")
    print("   cd ../beezee")
    print("   npx wrangler deploy")
    print()
    print("3. 🧪 Test the system:")
    print("   python test_system.py")
    print()
    print("4. 📊 Run the monitor:")
    print("   # Test run (once):")
    print("   python main.py --api-token YOUR_TOKEN --account-id YOUR_ACCOUNT_ID --database-id c934d24d-3b7e-49b8-ba4d-b2c696aa8958 --once")
    print()
    print("   # Continuous monitoring:")
    print("   python main.py --api-token YOUR_TOKEN --account-id YOUR_ACCOUNT_ID --database-id c934d24d-3b7e-49b8-ba4d-b2c696aa8958")
    print()
    print("5. 🌐 View your data:")
    print("   Visit your deployed worker URL + /busyness")
    print("   Example: https://your-worker.your-subdomain.workers.dev/busyness")
    print()

def main():
    """Main setup function"""
    print("🚀 MacBook Camera Busyness Monitor Setup")
    print("="*50)
    
    steps = [
        ("Checking Python version", check_python_version),
        ("Installing dependencies", install_dependencies),
        ("Checking camera access", check_camera_access),
        ("Creating configuration template", create_config_template),
        ("Running system tests", run_tests)
    ]
    
    for step_name, step_func in steps:
        print(f"\n🔍 {step_name}...")
        if not step_func():
            print(f"❌ Setup failed at: {step_name}")
            return 1
    
    show_next_steps()
    return 0

if __name__ == "__main__":
    exit(main())
