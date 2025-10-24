# MacBook Camera Busyness Monitor

A Python program that captures images from your MacBook camera every 30 seconds, evaluates how "busy" the scene is using computer vision techniques, and uploads the data to a Cloudflare D1 database.

## Features

- **Automatic Camera Capture**: Captures images every 30 seconds (configurable)
- **Intelligent Busyness Analysis**: Uses multiple computer vision techniques:
  - Motion detection using background subtraction
  - Edge density analysis
  - Color variance analysis
  - Texture analysis
  - Object contour detection
- **Cloudflare D1 Integration**: Automatically uploads data to your D1 database
- **Comprehensive Logging**: Detailed logging for monitoring and debugging
- **Configurable**: Customizable camera, interval, and database settings

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Set up your Cloudflare credentials:
   - Get your Cloudflare API token from the dashboard
   - Get your Account ID from the dashboard
   - Get your D1 Database ID from the wrangler.jsonc file

## Database Setup

1. Run the database schema in your Cloudflare D1 database:
```sql
-- Copy and paste the contents of database_schema.sql into your D1 database
```

## Usage

### Basic Usage (Continuous Monitoring)
```bash
python main.py --api-token YOUR_API_TOKEN --account-id YOUR_ACCOUNT_ID --database-id YOUR_DATABASE_ID
```

### Run Once (Test Mode)
```bash
python main.py --api-token YOUR_API_TOKEN --account-id YOUR_ACCOUNT_ID --database-id YOUR_DATABASE_ID --once
```

### Advanced Options
```bash
python main.py \
  --api-token YOUR_API_TOKEN \
  --account-id YOUR_ACCOUNT_ID \
  --database-id YOUR_DATABASE_ID \
  --camera 1 \
  --interval 60
```

## Command Line Arguments

- `--api-token`: Your Cloudflare API token (required)
- `--account-id`: Your Cloudflare Account ID (required)
- `--database-id`: Your D1 Database ID (required)
- `--camera`: Camera index (default: 0)
- `--interval`: Capture interval in seconds (default: 30)
- `--once`: Run once instead of continuously

## Busyness Scoring Algorithm

The program uses a sophisticated algorithm that combines multiple factors:

1. **Motion Detection (30% weight)**: Detects moving objects using background subtraction
2. **Edge Density (20% weight)**: Analyzes edge density using Canny edge detection
3. **Color Variance (20% weight)**: Measures color variation in the image
4. **Texture Analysis (15% weight)**: Uses Laplacian variance for texture analysis
5. **Object Contours (15% weight)**: Counts and analyzes object contours

The final score is scaled to 1-10, where:
- 1-3: Very quiet/static scene
- 4-6: Moderate activity
- 7-10: Very busy/dynamic scene

## Database Schema

The program stores data in a table with the following structure:

```sql
CREATE TABLE busyness_data (
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
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

## Logging

The program creates detailed logs in `busyness_monitor.log` and outputs to console. Logs include:
- Capture timestamps
- Analysis results
- Upload status
- Error messages

## Troubleshooting

### Camera Issues
- Make sure your camera is not being used by other applications
- Try different camera indices (0, 1, 2, etc.)
- Check camera permissions in System Preferences

### Database Issues
- Verify your API token has D1 permissions
- Check that the database schema is properly set up
- Ensure your Account ID and Database ID are correct

### Performance Issues
- Reduce capture frequency by increasing the interval
- Close other applications using the camera
- Check available disk space for logs

## Security Notes

- Store your API token securely
- Consider using environment variables for sensitive data
- The program captures images but doesn't store them locally
- All data is processed in memory and only metadata is stored

## Example Output

```
2024-01-15 10:30:00 - INFO - Camera 0 initialized successfully
2024-01-15 10:30:00 - INFO - Starting continuous monitoring (interval: 30s)
2024-01-15 10:30:00 - INFO - Starting monitoring cycle...
2024-01-15 10:30:01 - INFO - Analysis complete: Score=7, Timestamp=2024-01-15T10:30:01.123456
2024-01-15 10:30:01 - INFO - Successfully uploaded data: score=7, timestamp=2024-01-15T10:30:01.123456
2024-01-15 10:30:01 - INFO - Cycle completed successfully
```
