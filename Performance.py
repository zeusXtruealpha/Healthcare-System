import socket
import time
import datetime
import csv
import threading
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

MAIN_SERVER_ADDRESS = ("10.12.81.207", 9999)
BILLING_SERVER_ADDRESS = ("10.12.81.207", 9998)

performance_data = []  # Store performance data for each request

def log_performance(operation, start_time, end_time, rtt):
    latency = end_time - start_time
    data = {
        'timestamp': datetime.datetime.now(),
        'operation': operation,
        'latency': latency,
        'rtt': rtt
    }
    performance_data.append(data)
    logging.debug(f"Logged performance data: {data}")

def simulate_user_input(prompt):
    # Simulates user input for automated testing
    if "username" in prompt.lower():
        return "testuser"
    elif "command" in prompt.lower():
        return "BOOK"
    elif "date" in prompt.lower():
        return "2023-09-20"
    elif "DOCTOR:TIME_SLOT" in prompt:
        return "Dr.Smith:10:00AM"
    elif "insurance" in prompt.lower():
        return "No"
    elif "pay" in prompt.lower():
        return "pay"
    else:
        return ""

def measure_rtt(client, data_to_send):
    start_time = time.time()
    client.send(data_to_send.encode())
    client.recv(4096)  # Adjust buffer size if needed
    return time.time() - start_time

def handle_main_server():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.settimeout(10)  # Timeout to prevent infinite blocking
    try:
        client.connect(MAIN_SERVER_ADDRESS)
        logging.info("Connected to Main Server")

        start_time = time.time()
        total_rtt = 0
        rtt_count = 0

        # Username
        client.recv(1024)
        logging.debug("Received prompt for username")
        rtt = measure_rtt(client, simulate_user_input("username"))
        total_rtt += rtt
        rtt_count += 1

        # Command
        client.recv(1024)
        logging.debug("Received prompt for command")
        rtt = measure_rtt(client, simulate_user_input("command"))
        total_rtt += rtt
        rtt_count += 1

        # Date
        client.recv(1024)
        logging.debug("Received prompt for date")
        rtt = measure_rtt(client, simulate_user_input("date"))
        total_rtt += rtt
        rtt_count += 1

        # Available doctors
        client.recv(4096)
        logging.debug("Received list of available doctors")

        # Booking request
        rtt = measure_rtt(client, simulate_user_input("DOCTOR:TIME_SLOT"))
        total_rtt += rtt
        rtt_count += 1

        end_time = time.time()
        avg_rtt = total_rtt / rtt_count if rtt_count > 0 else 0
        log_performance("Main Server - Book Appointment", start_time, end_time, avg_rtt)

    except socket.timeout:
        logging.error("Timeout occurred during communication with Main Server")
    except Exception as e:
        logging.error(f"Error in handle_main_server: {e}")
    finally:
        client.close()

def handle_billing_server():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.settimeout(10)  # Timeout to prevent infinite blocking
    try:
        client.connect(BILLING_SERVER_ADDRESS)
        logging.info("Connected to Billing Server")

        start_time = time.time()
        total_rtt = 0
        rtt_count = 0

        # Username
        client.recv(1024)
        logging.debug("Received prompt for username")
        rtt = measure_rtt(client, simulate_user_input("username"))
        total_rtt += rtt
        rtt_count += 1

        # Bill info and insurance prompt
        bill_info = client.recv(1024).decode()
        logging.debug(f"Received bill info: {bill_info}")

        if "No pending bills" not in bill_info:
            rtt = measure_rtt(client, simulate_user_input("insurance"))
            total_rtt += rtt
            rtt_count += 1

            pay_prompt = client.recv(1024).decode()
            logging.debug(f"Received pay prompt: {pay_prompt}")
            if "Type 'pay'" in pay_prompt:
                rtt = measure_rtt(client, simulate_user_input("pay"))
                total_rtt += rtt
                rtt_count += 1

            # Final bill
            client.recv(1024)
            logging.debug("Received final bill")

        end_time = time.time()
        avg_rtt = total_rtt / rtt_count if rtt_count > 0 else 0
        log_performance("Billing Server - Check Bill", start_time, end_time, avg_rtt)

    except socket.timeout:
        logging.error("Timeout occurred during communication with Billing Server")
    except Exception as e:
        logging.error(f"Error in handle_billing_server: {e}")
    finally:
        client.close()

def make_requests():
    while True:
        try:
            handle_main_server()
            handle_billing_server()
            
            # Save after each cycle
            save_performance_data()
            
            # Sleep interval to simulate periodic requests
            time.sleep(60)
        
        except Exception as e:
            logging.error(f"Error in make_requests: {e}")
            time.sleep(10)  # Wait before retrying if there's an error

def save_performance_data():
    try:
        with open('performance_metrics.csv', 'w', newline='') as csvfile:
            fieldnames = ['timestamp', 'operation', 'latency', 'rtt']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for data in performance_data:
                writer.writerow(data)
        logging.info(f"Saved {len(performance_data)} records to performance_metrics.csv")
    except Exception as e:
        logging.error(f"Error saving performance data: {e}")

if __name__ == "__main__":
    try:
        make_requests()
    except KeyboardInterrupt:
        logging.info("Program interrupted by user. Saving final performance data...")
        save_performance_data()
