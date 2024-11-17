import socket
import threading
from datetime import datetime, timedelta
import json

# Initialize the dictionary to track doctors' availability for each date
doctors_availability = {}

# Initialize the dictionary to track user appointments
user_appointments = {}

# Initialize the dictionary to track user bills
user_bills = {}

# Function to save user bills to a file
def save_user_bills():
    with open('user_bills.json', 'w') as f:
        json.dump(user_bills, f)

# Function to load user bills from a file
def load_user_bills():
    global user_bills
    try:
        with open('user_bills.json', 'r') as f:
            user_bills = json.load(f)
    except FileNotFoundError:
        user_bills = {}

# Function to populate the availability dictionary for the next 7 days
def initialize_availability():
    today = datetime.now()
    for i in range(1, 8):
        date = today + timedelta(days=i)
        date_str = date.strftime('%Y-%m-%d')
        doctors_availability[date_str] = {
            "Dr.Smith": ["10:00AM", "11:00AM", "12:00PM"],
            "Dr.Johnson": ["10:00AM", "11:00AM", "12:00PM"],
            "Dr.Adams": ["10:00AM", "11:00AM", "12:00PM"],
            "Dr.Brown": ["01:00PM", "02:00PM", "03:00PM"],
            "Dr.Miller": ["01:00PM", "02:00PM", "03:00PM"],
            "Dr.Wilson": ["01:00PM", "02:00PM", "03:00PM"],
            "Dr.Jones": ["04:00PM", "05:00PM", "06:00PM"],
            "Dr.Taylor": ["04:00PM", "05:00PM", "06:00PM"],
            "Dr.Anderson": ["04:00PM", "05:00PM", "06:00PM"],
            "Dr.Thomas": ["07:00PM", "08:00PM", "09:00PM"],
            "Dr.Harris": ["07:00PM", "08:00PM", "09:00PM"],
            "Dr.Martin": ["07:00PM", "08:00PM", "09:00PM"]
        }

def get_available_doctors_for_date(date):
    date_str = date.strftime('%Y-%m-%d')
    if date_str in doctors_availability:
        available_doctors = f"Available Doctors and Timings for {date_str}:\n"
        for doctor, times in doctors_availability[date_str].items():
            available_doctors += f"{doctor}: {', '.join(times)}\n"
        return available_doctors
    return "No available doctors for this date."

def handle_client(client_socket):
    try:
        # Ask for a username
        client_socket.send("Enter your username: ".encode())
        username = client_socket.recv(1024).decode().strip()

        if username not in user_appointments:
            user_appointments[username] = {}  # Create entry for new user
        if username not in user_bills:
            user_bills[username] = 0  # Initialize bill for new user

        # Ask for the command (BOOK or CANCEL)
        client_socket.send("Enter the command (BOOK or CANCEL): ".encode())
        command = client_socket.recv(1024).decode().strip().upper()

        if command not in ["BOOK", "CANCEL"]:
            client_socket.send("Invalid command. Please use BOOK or CANCEL.".encode())
            return

        if command == "BOOK":
            # Ask for the date
            client_socket.send("Enter the date for booking (YYYY-MM-DD): ".encode())
            date_input = client_socket.recv(1024).decode().strip()

            try:
                input_date = datetime.strptime(date_input, '%Y-%m-%d')
            except ValueError:
                client_socket.send("Invalid date format. Please use YYYY-MM-DD.".encode())
                return

            today = datetime.now()
            if not (today + timedelta(days=1) <= input_date <= today + timedelta(days=7)):
                client_socket.send("Date must be between tomorrow and 7 days from now.".encode())
                return

            # Send list of available doctors and timings for the given date
            available_doctors_list = get_available_doctors_for_date(input_date)
            client_socket.send(available_doctors_list.encode())

            # Receive user input for doctor and time slot
            client_socket.send("Enter the doctor's name and time slot to book (e.g., Dr.Smith:10:00AM): ".encode())
            booking_request = client_socket.recv(1024).decode().strip()

            parts = booking_request.split(":", 1)
            if len(parts) != 2:
                client_socket.send("Invalid input format. Please use: DOCTOR:TIME_SLOT".encode())
                return

            doctor, time_slot = parts
            date_str = input_date.strftime('%Y-%m-%d')

            if date_str in doctors_availability and doctor in doctors_availability[date_str] and time_slot in doctors_availability[date_str][doctor]:
                # Book the appointment
                if date_str not in user_appointments[username]:
                    user_appointments[username][date_str] = {}
                
                user_appointments[username][date_str][time_slot] = doctor
                doctors_availability[date_str][doctor].remove(time_slot)
                user_bills[username] += 1000  # Add 1000 to the user's bill
                save_user_bills()  # Save updated bills to file
                response = f"Appointment booked with {doctor} at {time_slot} on {date_str} for user {username}\nPending Bill: {user_bills[username]}"
            else:
                response = "Invalid doctor or time slot."

            client_socket.send(response.encode())

        elif command == "CANCEL":
            # Show the user's booked appointments
            if username in user_appointments and user_appointments[username]:
                user_bookings = "Your booked appointments:\n"
                for date, slots in user_appointments[username].items():
                    for time, booked_doctor in slots.items():
                        user_bookings += f"{date} - {booked_doctor} at {time}\n"
                client_socket.send(user_bookings.encode())

                # Ask for the date and time slot to cancel
                client_socket.send("Enter the date and time slot to cancel (e.g., YYYY-MM-DD:10:00AM): ".encode())
                cancel_input = client_socket.recv(1024).decode().strip()

                try:
                    date_str, cancel_time = cancel_input.split(":", 1)
                except ValueError:
                    client_socket.send("Invalid input format. Please use: YYYY-MM-DD:TIME_SLOT".encode())
                    return

                if date_str in user_appointments[username] and cancel_time in user_appointments[username][date_str]:
                    cancelled_doctor = user_appointments[username][date_str][cancel_time]
                    del user_appointments[username][date_str][cancel_time]
                    if not user_appointments[username][date_str]:
                        del user_appointments[username][date_str]
                    if not user_appointments[username]:
                        del user_appointments[username]

                    # Add the time slot back to the doctor's availability
                    doctors_availability[date_str][cancelled_doctor].append(cancel_time)
                    user_bills[username] -= 1000  # Subtract 1000 from the user's bill
                    save_user_bills()  # Save updated bills to file
                    response = f"Appointment with {cancelled_doctor} at {cancel_time} on {date_str} cancelled for user {username}\nPending Bill: {user_bills[username]}"
                else:
                    response = "No booking found at the specified date and time slot."

                client_socket.send(response.encode())
            else:
                client_socket.send("You have no bookings to cancel.".encode())

    finally:
        client_socket.close()

def start_server():
    initialize_availability()  # Initialize availability for the next 7 days
    load_user_bills()  # Load user bills from file
    
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("0.0.0.0", 9999))
    server.listen(5)
    print("Server is listening on port 9999...")
    
    while True:
        client_socket, addr = server.accept()
        print(f"Connection established with {addr}")
        client_handler = threading.Thread(target=handle_client, args=(client_socket,))
        client_handler.start()

if __name__ == "__main__":
    start_server()
