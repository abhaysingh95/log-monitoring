import os
import re
from datetime import datetime, timedelta
from collections import defaultdict

LOG_DIR = "./logs"
TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S,%f"

# More specific error patterns to avoid false positives
ERROR_PATTERNS = {
    "HTTP_400": r'"\s+4\d{2}\s+',  # HTTP status codes like "400", "404"
    "HTTP_504": r'"\s+504\s+',
    "returncode=1": r'returncode\s*[=:]\s*["\']?1',
    "ERROR_999": r'999\s+[Ee]rror|error\s+999',
    "duplicate_key": r'duplicate key value violates unique constraint',
    "failed": r'\bfailed\b',
    "ERROR": r'\bERROR\b',
}

SUCCESS_PATTERNS = {
    "SUCCESS": r'\bSUCCESS\b',
    "returnCode=0": r'"returnCode"\s*:\s*"0"',
    "returncode=0": r'returncode\s*[=:]\s*["\']?0',
    "Response =>": r"Response => '\{\"returnCode\":\"0\"",
    "Finalized Successfully": r"Finalized Successfully",
    "passed": r'\bpassed\b',
}

def parse_timestamp(line):
    try:
        # Try with microseconds
        return datetime.strptime(line[:23], TIMESTAMP_FORMAT)
    except ValueError:
        try:
            # Try without microseconds
            return datetime.strptime(line[:19], "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return None

def detect_error_success(message):
    """
    Detect if line contains error or success.
    Returns: (is_error, error_type) or (is_success, success_type)
    """
    message_lower = message.lower()
    
    # Check for success patterns first (some logs might have both)
    for pattern_name, pattern in SUCCESS_PATTERNS.items():
        if re.search(pattern, message, re.IGNORECASE):
            # But if it's clearly an error despite having "SUCCESS" in text
            if "ERROR:" in message or "failed," in message:
                break
            return (False, "SUCCESS")
    
    # Check for error patterns
    for pattern_name, pattern in ERROR_PATTERNS.items():
        if re.search(pattern, message):
            return (True, pattern_name)
    
    # Check for HTTP status codes in access logs
    http_match = re.search(r'"\s+(\d{3})\s+', message)
    if http_match:
        status = http_match.group(1)
        if status.startswith('4') or status.startswith('5'):
            return (True, f"HTTP_{status}")
        elif status.startswith('2'):
            return (False, "HTTP_SUCCESS")
    
    # Check for returnCode not equal to 0
    returncode_match = re.search(r'"returnCode"\s*:\s*"([^0]\d*)"', message)
    if returncode_match and returncode_match.group(1) != "0":
        return (True, f"returnCode={returncode_match.group(1)}")
    
    return (None, None)

def get_time_window():
    print("\nSelect Time Mode:")
    print("1. Last N hours")
    print("2. Custom time range")

    choice = input("Enter choice (1/2): ").strip()

    if choice == "1":
        hours = int(input("Enter number of hours: "))
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
    else:
        start = input("Enter start time (YYYY-MM-DD HH:MM): ")
        end = input("Enter end time   (YYYY-MM-DD HH:MM): ")
        start_time = datetime.strptime(start, "%Y-%m-%d %H:%M")
        end_time = datetime.strptime(end, "%Y-%m-%d %H:%M")

    return start_time, end_time

def get_log_type():
    print("\nSelect Log Type:")
    print("1. Success only")
    print("2. Error only")
    print("3. Both")

    return input("Enter choice (1/2/3): ").strip()

def main():
    start_time, end_time = get_time_window()
    log_choice = get_log_type()

    specific_error = None
    if log_choice in ["2", "3"]:
        err = input("Enter specific error (or press Enter for ALL): ").strip()
        if err:
            specific_error = err.lower()

    # Data structure: service -> hour -> {success, error, error_types, success_types}
    service_data = defaultdict(lambda: defaultdict(lambda: {
        "success": 0,
        "error": 0,
        "error_types": defaultdict(int),
        "success_types": defaultdict(int)
    }))

    print(f"\nAnalyzing logs from {start_time} to {end_time}...")
    
    for file in sorted(os.listdir(LOG_DIR)):
        path = os.path.join(LOG_DIR, file)
        if not os.path.isfile(path):
            continue

        service = file.replace(".log", "")
        print(f"Processing {service}...")

        with open(path, "r", errors="ignore") as f:
            for line in f:
                ts = parse_timestamp(line)
                if not ts:
                    continue
                    
                if not (start_time <= ts <= end_time):
                    continue

                hour = ts.strftime("%Y-%m-%d %H:00")
                result = detect_error_success(line)
                
                if result[0] is None:
                    continue  # Skip if neither success nor error
                
                is_error, result_type = result
                
                if is_error:
                    if log_choice in ["2", "3"]:
                        if not specific_error or specific_error in result_type.lower():
                            service_data[service][hour]["error"] += 1
                            service_data[service][hour]["error_types"][result_type] += 1
                else:
                    if log_choice in ["1", "3"]:
                        service_data[service][hour]["success"] += 1
                        service_data[service][hour]["success_types"][result_type] += 1

    print("\n" + "="*50 + " LOG ANALYSIS REPORT " + "="*50)

    total_success = 0
    total_errors = 0
    
    for service in sorted(service_data.keys()):
        service_success = 0
        service_errors = 0
        
        print(f"\n{'='*60}")
        print(f"SERVICE: {service}")
        print(f"{'='*60}")
        
        for hour in sorted(service_data[service].keys()):
            data = service_data[service][hour]
            
            if data["success"] == 0 and data["error"] == 0:
                continue
                
            print(f"\n  Hour: {hour}")
            print(f"    Success Logs: {data['success']}")
            print(f"    Error Logs  : {data['error']}")
            
            service_success += data["success"]
            service_errors += data["error"]
            
            if data["error_types"]:
                print("    Error Breakdown:")
                for err_type, count in sorted(data["error_types"].items()):
                    print(f"      - {err_type}: {count}")
            
            # Uncomment if you want to see success types too
            # if data["success_types"]:
            #     print("    Success Breakdown:")
            #     for succ_type, count in sorted(data["success_types"].items()):
            #         print(f"      - {succ_type}: {count}")
        
        if service_success > 0 or service_errors > 0:
            print(f"\n  Service Summary:")
            print(f"    Total Success: {service_success}")
            print(f"    Total Errors : {service_errors}")
            if service_errors > 0:
                error_rate = (service_errors / (service_success + service_errors)) * 100
                print(f"    Error Rate   : {error_rate:.2f}%")
        
        total_success += service_success
        total_errors += service_errors

    print(f"\n{'='*120}")
    print("OVERALL SUMMARY:")
    print(f"{'='*120}")
    print(f"Total Success Logs: {total_success}")
    print(f"Total Error Logs : {total_errors}")
    
    if total_success + total_errors > 0:
        overall_error_rate = (total_errors / (total_success + total_errors)) * 100
        print(f"Overall Error Rate: {overall_error_rate:.2f}%")
    
    print(f"{'='*120}")

if __name__ == "__main__":
    main()
