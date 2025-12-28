# Log Monitoring and Analysis Project

## Overview
This project is created for monitoring and analyzing application logs.
It includes log generation scripts, real-time log files, and log analysis scripts
to count success logs, error logs, and error types within a given time frame.

---

## Project Structure
log-monitoring/
├── generators/ # Scripts to generate service-wise logs
├── logs/ # Generated log files for each service
├── log-analyzer.py # Updated log analysis script
└── start-all-logs.py # Script to start all log generators


---

## Functionality
- Generates logs similar to real production logs
- Analyzes logs based on a user-defined time window
- Counts total success and error logs
- Identifies and counts different error types
- Provides service-wise log analysis

---

## How to Run

### Start log generation

python3 start-all-logs.py

### Run log analysis

python3 log-analyzer.py

### Output

Total success log count

Total error log count

Error-type summary

Time-frame based analysis
