#!/usr/bin/env python3
"""
MacBook Camera Busyness Monitor
Captures images every 30 seconds, evaluates busyness (1-10), and uploads to Cloudflare D1
"""

import cv2
import numpy as np
import time
import requests
import json
import os
from datetime import datetime
import logging
from typing import Tuple, Optional
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('busyness_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class BusynessEvaluator:
    """Evaluates how 'busy' a scene is using computer vision techniques"""
    
    def __init__(self):
        # Initialize background subtractor for motion detection
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            detectShadows=True, 
            varThreshold=50
        )
        
    def calculate_busyness_score(self, image: np.ndarray) -> Tuple[int, dict]:
        """
        Calculate busyness score (1-10) based on multiple factors:
        - Motion detection
        - Edge density
        - Color variance
        - Object detection (if available)
        
        Returns: (score, metadata)
        """
        try:
            # Convert to grayscale for analysis
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # 1. Motion detection using background subtraction
            motion_mask = self.bg_subtractor.apply(image)
            motion_pixels = np.sum(motion_mask > 0)
            motion_ratio = motion_pixels / (image.shape[0] * image.shape[1])
            
            # 2. Edge density (Canny edge detection)
            edges = cv2.Canny(gray, 50, 150)
            edge_pixels = np.sum(edges > 0)
            edge_ratio = edge_pixels / (image.shape[0] * image.shape[1])
            
            # 3. Color variance (higher variance = more activity)
            color_variance = np.var(image)
            normalized_variance = min(color_variance / 10000, 1.0)  # Normalize to 0-1
            
            # 4. Texture analysis using Laplacian variance
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            normalized_laplacian = min(laplacian_var / 1000, 1.0)
            
            # 5. Contour detection for object counting
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            contour_count = len([c for c in contours if cv2.contourArea(c) > 100])
            normalized_contours = min(contour_count / 20, 1.0)  # Normalize to 0-1
            
            # Combine factors with weights
            weights = {
                'motion': 0.3,
                'edges': 0.2,
                'variance': 0.2,
                'texture': 0.15,
                'contours': 0.15
            }
            
            combined_score = (
                weights['motion'] * motion_ratio +
                weights['edges'] * edge_ratio +
                weights['variance'] * normalized_variance +
                weights['texture'] * normalized_laplacian +
                weights['contours'] * normalized_contours
            )
            
            # Convert to 1-10 scale
            busyness_score = max(1, min(10, int(combined_score * 9 + 1)))
            
            metadata = {
                'motion_ratio': float(motion_ratio),
                'edge_ratio': float(edge_ratio),
                'color_variance': float(color_variance),
                'texture_variance': float(laplacian_var),
                'contour_count': int(contour_count),
                'combined_raw': float(combined_score)
            }
            
            return busyness_score, metadata
            
        except Exception as e:
            logger.error(f"Error calculating busyness score: {e}")
            return 5, {'error': str(e)}  # Default middle score on error

class CameraCapture:
    """Handles camera capture and image processing"""
    
    def __init__(self, camera_index: int = 0):
        self.camera_index = camera_index
        self.cap = None
        
    def initialize_camera(self) -> bool:
        """Initialize camera connection"""
        try:
            self.cap = cv2.VideoCapture(self.camera_index)
            if not self.cap.isOpened():
                logger.error(f"Could not open camera {self.camera_index}")
                return False
            
            # Set camera properties for better quality
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            
            logger.info(f"Camera {self.camera_index} initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing camera: {e}")
            return False
    
    def capture_image(self) -> Optional[np.ndarray]:
        """Capture a single image from camera"""
        try:
            if not self.cap or not self.cap.isOpened():
                logger.error("Camera not initialized")
                return None
            
            ret, frame = self.cap.read()
            if not ret:
                logger.error("Failed to capture image")
                return None
            
            return frame
            
        except Exception as e:
            logger.error(f"Error capturing image: {e}")
            return None
    
    def release_camera(self):
        """Release camera resources"""
        if self.cap:
            self.cap.release()
            logger.info("Camera released")

class CloudflareUploader:
    """Handles uploading data to Cloudflare D1 database"""
    
    def __init__(self, api_token: str, account_id: str, database_id: str):
        self.api_token = api_token
        self.account_id = account_id
        self.database_id = database_id
        self.base_url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/d1/database/{database_id}"
        
    def upload_busyness_data(self, score: int, metadata: dict, timestamp: str, notes: str = "", camera_name: str = "") -> bool:
        """Upload busyness data to D1 database"""
        try:
            # Prepare the SQL query
            sql_query = """
            INSERT INTO busyness_data (timestamp, score, motion_ratio, edge_ratio, 
                                     color_variance, texture_variance, contour_count, 
                                     combined_raw, metadata, notes, camera_name)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            # Prepare parameters
            params = [
                timestamp,
                score,
                metadata.get('motion_ratio', 0),
                metadata.get('edge_ratio', 0),
                metadata.get('color_variance', 0),
                metadata.get('texture_variance', 0),
                metadata.get('contour_count', 0),
                metadata.get('combined_raw', 0),
                json.dumps(metadata),
                notes,
                camera_name
            ]
            
            # Make API request
            headers = {
                'Authorization': f'Bearer {self.api_token}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'sql': sql_query,
                'params': params
            }
            
            response = requests.post(
                f"{self.base_url}/query",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success', False):
                    logger.info(f"Successfully uploaded data: score={score}, timestamp={timestamp}")
                    return True
                else:
                    logger.error(f"Database query failed: {result.get('errors', 'Unknown error')}")
                    return False
            else:
                logger.error(f"API request failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error uploading to database: {e}")
            return False

class BusynessMonitor:
    """Main class that orchestrates the entire monitoring process"""
    
    def __init__(self, api_token: str, account_id: str, database_id: str, 
                 camera_index: int = 0, interval: int = 5, notes: str = "", camera_name: str = ""):
        self.camera = CameraCapture(camera_index)
        self.evaluator = BusynessEvaluator()
        self.uploader = CloudflareUploader(api_token, account_id, database_id)
        self.interval = interval
        self.notes = notes
        self.camera_name = camera_name
        self.running = False
        
    def initialize(self) -> bool:
        """Initialize all components"""
        logger.info("Initializing Busyness Monitor...")
        
        if not self.camera.initialize_camera():
            logger.error("Failed to initialize camera")
            return False
        
        logger.info("Busyness Monitor initialized successfully")
        return True
    
    def capture_and_analyze(self) -> Optional[dict]:
        """Capture image and analyze busyness"""
        try:
            # Capture image
            image = self.camera.capture_image()
            if image is None:
                logger.error("Failed to capture image")
                return None
            
            # Analyze busyness
            score, metadata = self.evaluator.calculate_busyness_score(image)
            
            # Prepare data
            timestamp = datetime.now().isoformat()
            data = {
                'timestamp': timestamp,
                'score': score,
                'metadata': metadata
            }
            
            logger.info(f"Analysis complete: Score={score}, Timestamp={timestamp}")
            return data
            
        except Exception as e:
            logger.error(f"Error in capture and analyze: {e}")
            return None
    
    def upload_data(self, data: dict) -> bool:
        """Upload data to Cloudflare D1"""
        return self.uploader.upload_busyness_data(
            data['score'],
            data['metadata'],
            data['timestamp'],
            self.notes,
            self.camera_name
        )
    
    def run_once(self) -> bool:
        """Run one complete cycle: capture, analyze, upload"""
        try:
            logger.info("Starting monitoring cycle...")
            
            # Capture and analyze
            data = self.capture_and_analyze()
            if not data:
                logger.error("Failed to capture and analyze")
                return False
            
            # Upload to database
            if self.upload_data(data):
                logger.info("Cycle completed successfully")
                return True
            else:
                logger.error("Failed to upload data")
                return False
                
        except Exception as e:
            logger.error(f"Error in monitoring cycle: {e}")
            return False
    
    def run_continuous(self):
        """Run continuous monitoring"""
        self.running = True
        logger.info(f"Starting continuous monitoring (interval: {self.interval}s)")
        
        try:
            while self.running:
                self.run_once()
                logger.info(f"Waiting {self.interval} seconds until next capture...")
                time.sleep(self.interval)
                
        except KeyboardInterrupt:
            logger.info("Monitoring stopped by user")
        except Exception as e:
            logger.error(f"Error in continuous monitoring: {e}")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up resources"""
        self.running = False
        self.camera.release_camera()
        logger.info("Cleanup completed")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='MacBook Camera Busyness Monitor')
    parser.add_argument('--api-token', required=True, help='Cloudflare API token')
    parser.add_argument('--account-id', required=True, help='Cloudflare Account ID')
    parser.add_argument('--database-id', required=True, help='Cloudflare D1 Database ID')
    parser.add_argument('--camera', type=int, default=0, help='Camera index (default: 0)')
    parser.add_argument('--camera-name', type=str, default='MacBook Camera', help='Camera name/identifier (default: MacBook Camera)')
    parser.add_argument('--interval', type=int, default=5, help='Capture interval in seconds (default: 5)')
    parser.add_argument('--notes', type=str, default='', help='Notes/context for this monitoring session')
    parser.add_argument('--once', action='store_true', help='Run once instead of continuously')
    
    args = parser.parse_args()
    
    # Create monitor instance
    monitor = BusynessMonitor(
        api_token=args.api_token,
        account_id=args.account_id,
        database_id=args.database_id,
        camera_index=args.camera,
        interval=args.interval,
        notes=args.notes,
        camera_name=args.camera_name
    )
    
    # Initialize
    if not monitor.initialize():
        logger.error("Failed to initialize monitor")
        return 1
    
    try:
        if args.once:
            # Run once
            success = monitor.run_once()
            return 0 if success else 1
        else:
            # Run continuously
            monitor.run_continuous()
            return 0
            
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        return 1
    finally:
        monitor.cleanup()

if __name__ == "__main__":
    exit(main())
