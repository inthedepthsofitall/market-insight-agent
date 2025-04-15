# Market AI Agent - Scheduling and Usage Guide

This document provides instructions for setting up and scheduling the Market AI Agent to run daily before market open.

## Prerequisites

- Python 3.10 or higher
- Required Python packages (install using `pip install -r requirements.txt`)
- Internet connection for fetching market data
- (Optional) Email account for report delivery

## Basic Usage

The Market AI Agent can be run manually using the following command:

```bash
python main.py --config config.json
```

### Command Line Arguments

- `--config`: Path to configuration file (default: looks for config.json in the current directory)
- `--module`: Specific module to run (choices: "news", "macro", "cme", "sentiment", "report", "all")

Example to run only the news sentiment module:

```bash
python main.py --config config.json --module news
```

## Scheduling Options

### Option 1: Using Cron (Linux/macOS)

To schedule the Market AI Agent to run daily at 7:00 AM EST (adjust time as needed):

1. Open your crontab file:
   ```bash
   crontab -e
   ```

2. Add the following line to run the script at 7:00 AM EST (adjust the path to your installation):
   ```
   0 7 * * 1-5 cd /path/to/market_ai_agent && python main.py --config config.json >> logs/cron_run.log 2>&1
   ```

   Note: The `1-5` indicates Monday through Friday. Adjust if you want to include weekends.

3. Save and exit the editor.

### Option 2: Using Windows Task Scheduler

1. Open Task Scheduler (search for "Task Scheduler" in the Start menu)
2. Click "Create Basic Task"
3. Enter a name (e.g., "Market AI Agent") and description
4. Select "Daily" for the trigger
5. Set the start time to 7:00 AM and select "Recur every 1 days"
6. Select "Start a program" for the action
7. Browse to select your Python executable (e.g., `C:\Python310\python.exe`)
8. In "Add arguments", enter: `main.py --config config.json`
9. In "Start in", enter the full path to your Market AI Agent directory
10. Complete the wizard and check "Open the Properties dialog" before finishing
11. In the Properties dialog, go to the "Conditions" tab and adjust as needed
12. Go to the "Settings" tab and adjust as needed
13. Click "OK" to save the task

### Option 3: Using APScheduler (Python-based scheduling)

You can create a Python script to schedule the Market AI Agent using APScheduler:

1. Create a file named `schedule_runner.py` with the following content:

```python
import sys
import time
import logging
import subprocess
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/scheduler.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("scheduler")

def run_market_ai_agent():
    """Run the Market AI Agent"""
    try:
        logger.info("Starting scheduled Market AI Agent run...")
        result = subprocess.run(
            ["python", "main.py", "--config", "config.json"],
            capture_output=True,
            text=True,
            check=True
        )
        logger.info("Market AI Agent run completed successfully")
        logger.info(f"Output: {result.stdout}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running Market AI Agent: {e}")
        logger.error(f"Error output: {e.stderr}")

if __name__ == "__main__":
    scheduler = BlockingScheduler()
    
    # Schedule to run at 7:00 AM EST on weekdays (Monday=0, Sunday=6)
    scheduler.add_job(
        run_market_ai_agent,
        CronTrigger(hour=7, minute=0, day_of_week='0-4', timezone='America/New_York'),
        id='market_ai_daily_run',
        name='Daily Market AI Agent Run'
    )
    
    logger.info("Scheduler started. Press Ctrl+C to exit.")
    
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped.")
```

2. Install APScheduler:
   ```bash
   pip install apscheduler
   ```

3. Run the scheduler:
   ```bash
   python schedule_runner.py
   ```

   Note: This script needs to be kept running for the scheduler to work. Consider using a process manager like `systemd`, `supervisor`, or `pm2` to keep it running.

## Configuration

The `config.json` file contains all settings for the Market AI Agent. Key sections include:

### General Settings
- `data_dir`: Directory for storing data files
- `reports_dir`: Directory for storing generated reports
- `use_mock_data`: Set to `false` for production use with real data

### Module-Specific Settings
Each module has its own configuration section:

#### News & Sentiment Module
- `enabled`: Enable/disable the module
- `max_articles_per_source`: Maximum number of articles to fetch per source
- `sources`: URLs for news sources
- `watchlist`: Tickers and sectors to monitor

#### Macro Sentiment Analyzer
- `enabled`: Enable/disable the module
- `indicators`: Configuration for VIX thresholds, treasury yields, etc.

#### CME Volume/Open Interest Tracker
- `enabled`: Enable/disable the module
- `contracts`: Futures contracts to track
- `thresholds`: Settings for detecting volume spikes and OI changes

#### Sentiment Cross-check Module
- `enabled`: Enable/disable the module
- `sources`: Configuration for Reddit, Twitter, etc.

#### Report Generator
- `enabled`: Enable/disable the module
- `format`: Output format (html or markdown)
- `include_charts`: Whether to include charts in the report
- `email`: Email delivery settings

## Email Setup

To enable email delivery of reports:

1. Edit `config.json` and set `modules.report_generator.email.enabled` to `true`
2. Configure the SMTP settings:
   - `smtp_server`: Your email provider's SMTP server
   - `smtp_port`: SMTP port (usually 587 for TLS)
   - `sender_email`: Your email address
   - `sender_password`: Your email password or app password
   - `recipient_email`: Email address to receive reports

Note: For Gmail, you'll need to create an "App Password" instead of using your regular password. See [Google Account Help](https://support.google.com/accounts/answer/185833) for instructions.

## Troubleshooting

### Common Issues

1. **Module not running**: Check the logs in the `logs` directory for error messages.

2. **Email delivery failing**: Verify your SMTP settings and ensure your email provider allows SMTP access.

3. **No data being fetched**: If `use_mock_data` is set to `false`, ensure you have proper API keys configured.

4. **Scheduling not working**: Check system logs for cron or Task Scheduler errors.

### Logs

Log files are stored in the `logs` directory:
- `market_ai.log`: Main application logs
- `scheduler.log`: Scheduler logs (if using APScheduler)
- `cron_run.log`: Output from cron jobs (if using cron)

## Production Considerations

For production use:

1. Set `use_mock_data` to `false` in `config.json`
2. Obtain and configure necessary API keys
3. Use a dedicated machine or cloud instance for reliability
4. Consider using a process manager to ensure the scheduler stays running
5. Set up monitoring to alert you if the system fails
6. Regularly back up your configuration and data directories
