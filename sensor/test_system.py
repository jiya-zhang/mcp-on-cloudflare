#!/usr/bin/env python3
"""
Test script for the busyness monitoring system
This script tests the camera capture and busyness evaluation without uploading to database
"""

import cv2
import numpy as np
import time
import sys
import os

# Add the current directory to the path so we can import from main.py
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import BusynessEvaluator, CameraCapture

def test_camera_capture():
    """Test camera capture functionality"""
    print("Testing camera capture...")
    
    camera = CameraCapture(0)
    if not camera.initialize_camera():
        print("❌ Failed to initialize camera")
        return False
    
    # Capture a test image
    image = camera.capture_image()
    if image is None:
        print("❌ Failed to capture image")
        camera.release_camera()
        return False
    
    print(f"✅ Successfully captured image: {image.shape}")
    camera.release_camera()
    return True

def test_busyness_evaluation():
    """Test busyness evaluation with a test image"""
    print("Testing busyness evaluation...")
    
    # Create a test image with some activity
    test_image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    
    # Add some edges and patterns to make it more "busy"
    cv2.rectangle(test_image, (100, 100), (200, 200), (255, 255, 255), -1)
    cv2.circle(test_image, (400, 300), 50, (128, 128, 128), -1)
    
    evaluator = BusynessEvaluator()
    score, metadata = evaluator.calculate_busyness_score(test_image)
    
    print(f"✅ Busyness evaluation completed:")
    print(f"   Score: {score}/10")
    print(f"   Motion ratio: {metadata.get('motion_ratio', 0):.3f}")
    print(f"   Edge ratio: {metadata.get('edge_ratio', 0):.3f}")
    print(f"   Color variance: {metadata.get('color_variance', 0):.1f}")
    print(f"   Contour count: {metadata.get('contour_count', 0)}")
    
    return True

def test_full_cycle():
    """Test a complete capture and analysis cycle"""
    print("Testing full capture and analysis cycle...")
    
    camera = CameraCapture(0)
    evaluator = BusynessEvaluator()
    
    try:
        if not camera.initialize_camera():
            print("❌ Failed to initialize camera")
            return False
        
        # Capture image
        image = camera.capture_image()
        if image is None:
            print("❌ Failed to capture image")
            return False
        
        print(f"✅ Captured image: {image.shape}")
        
        # Analyze busyness
        score, metadata = evaluator.calculate_busyness_score(image)
        
        print(f"✅ Analysis complete:")
        print(f"   Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   Busyness Score: {score}/10")
        print(f"   Metadata: {metadata}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in full cycle test: {e}")
        return False
    finally:
        camera.release_camera()

def main():
    """Run all tests"""
    print("🧪 Testing MacBook Camera Busyness Monitor System")
    print("=" * 50)
    
    tests = [
        ("Camera Capture", test_camera_capture),
        ("Busyness Evaluation", test_busyness_evaluation),
        ("Full Cycle", test_full_cycle)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 Running {test_name} test...")
        try:
            if test_func():
                print(f"✅ {test_name} test passed")
                passed += 1
            else:
                print(f"❌ {test_name} test failed")
        except Exception as e:
            print(f"❌ {test_name} test failed with error: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your system is ready to use.")
        print("\nNext steps:")
        print("1. Set up your Cloudflare credentials")
        print("2. Run: python main.py --api-token YOUR_TOKEN --account-id YOUR_ACCOUNT_ID --database-id YOUR_DATABASE_ID --once")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    exit(main())
