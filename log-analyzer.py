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
    # Check for error patterns first
    for pattern_name, pattern in ERROR_PATTERNS.items():
        if re.search(pattern, message):
            return (True, pattern_name)
    
    # Check for success patterns
    for pattern_name, pattern in SUCCESS_PATTERNS.items():
        if re.search(pattern, message, re.IGNORECASE):
            # Special case: if line has both ERROR and SUCCESS, prioritize error
            if "ERROR:" in message and "SUCCESS" in message:
                continue
            return (False, pattern_name)
    
    # Check for HTTP status codes in access logs
    http_match = re.search(r'"\s+(\d{3})\s+', message)
    if http_match:
        status = http_match.group(1)
        if status.startswith('4') or status.startswith('5'):
            return (True, f"HTTP_{status}")
        elif status.startswith('2'):
            return (False, f"HTTP_{status}")
    
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

def get_success_detail_level():
    print("\nSuccess Detail Level:")
    print("1. Show success count only")
    print("2. Show success types breakdown")
    
    choice = input("Enter choice (1/2): ").strip()
    return choice == "2"

def get_error_detail_level():
    print("\nError Detail Level:")
    print("1. Show error count only")
    print("2. Show error types breakdown")
    
    choice = input("Enter choice (1/2): ").strip()
    return choice == "2"

def main():
    start_time, end_time = get_time_window()
    log_choice = get_log_type()
    
    show_success_details = False
    show_error_details = False
    
    if log_choice in ["1", "3"]:
        show_success_details = get_success_detail_level()
    
    if log_choice in ["2", "3"]:
        show_error_details = get_error_detail_level()

    specific_error = None
    if log_choice in ["2", "3"]:
        err = input("Enter specific error to filter (or press Enter for ALL): ").strip()
        if err:
            specific_error = err.lower()
    
    specific_success = None
    if log_choice in ["1", "3"]:
        succ = input("Enter specific success type to filter (or press Enter for ALL): ").strip()
        if succ:
            specific_success = succ.lower()

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
                        if not specific_success or specific_success in result_type.lower():
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
            
            # Show success types breakdown if requested
            if show_success_details and data["success_types"]:
                print("    Success Breakdown:")
                for succ_type, count in sorted(data["success_types"].items()):
                    print(f"      ✓ {succ_type}: {count}")
            
            # Show error types breakdown if requested
            if show_error_details and data["error_types"]:
                print("    Error Breakdown:")
                for err_type, count in sorted(data["error_types"].items()):
                    print(f"      ✗ {err_type}: {count}")
        
        if service_success > 0 or service_errors > 0:
            print(f"\n  Service Summary:")
            print(f"    Total Success: {service_success}")
            print(f"    Total Errors : {service_errors}")
            
            # Show success types summary
            if show_success_details:
                success_summary = defaultdict(int)
                for hour_data in service_data[service].values():
                    for succ_type, count in hour_data["success_types"].items():
                        success_summary[succ_type] += count
                
                if success_summary:
                    print("    Success Types Summary:")
                    for succ_type, count in sorted(success_summary.items()):
                        print(f"      ✓ {succ_type}: {count}")
            
            # Show error types summary
            if show_error_details:
                error_summary = defaultdict(int)
                for hour_data in service_data[service].values():
                    for err_type, count in hour_data["error_types"].items():
                        error_summary[err_type] += count
                
                if error_summary:
                    print("    Error Types Summary:")
                    for err_type, count in sorted(error_summary.items()):
                        print(f"      ✗ {err_type}: {count}")
            
            if service_errors > 0:
                error_rate = (service_errors / (service_success + service_errors)) * 100
                print(f"    Error Rate   : {error_rate:.2f}%")
            else:
                print(f"    Success Rate : 100.00%")
        
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
        
        # Overall success types summary
        if show_success_details:
            overall_success_types = defaultdict(int)
            for service in service_data.values():
                for hour_data in service.values():
                    for succ_type, count in hour_data["success_types"].items():
                        overall_success_types[succ_type] += count
            
            if overall_success_types:
                print("\nOverall Success Types:")
                for succ_type, count in sorted(overall_success_types.items()):
                    percentage = (count / total_success * 100) if total_success > 0 else 0
                    print(f"  ✓ {succ_type}: {count} ({percentage:.1f}%)")
        
        # Overall error types summary
        if show_error_details:
            overall_error_types = defaultdict(int)
            for service in service_data.values():
                for hour_data in service.values():
                    for err_type, count in hour_data["error_types"].items():
                        overall_error_types[err_type] += count
            
            if overall_error_types:
                print("\nOverall Error Types:")
                for err_type, count in sorted(overall_error_types.items()):
                    percentage = (count / total_errors * 100) if total_errors > 0 else 0
                    print(f"  ✗ {err_type}: {count} ({percentage:.1f}%)")
    
    print(f"{'='*120}")
    
    # Additional statistics
    if total_success + total_errors > 0:
        print("\nADDITIONAL STATISTICS:")
        print(f"{'='*40}")
        print(f"Total Logs Processed: {total_success + total_errors}")
        print(f"Success Rate: {(total_success/(total_success + total_errors)*100):.2f}%")
        print(f"Error Rate: {(total_errors/(total_success + total_errors)*100):.2f}%")
        print(f"Success to Error Ratio: {total_success}:{total_errors}")
        
        # Count unique services with logs
        active_services = sum(1 for service in service_data.values() 
                            if any(hour_data['success'] > 0 or hour_data['error'] > 0 
                                  for hour_data in service.values()))
        print(f"Active Services: {active_services}")

if __name__ == "__main__":
    main()
