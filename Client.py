import socket

def get_user_input(prompt):
    return input(prompt).strip()

def handle_main_server():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(("192.168.182.223", 9999))

    try:
        # Receive the prompt for username
        username_prompt = client.recv(1024).decode()
        print(username_prompt)
        username = get_user_input("")

        # Send the username to the server
        client.send(username.encode())

        # Receive the command prompt from the server
        command_prompt = client.recv(1024).decode()
        print(command_prompt)
        command = get_user_input("Enter the command (BOOK or CANCEL): ").upper()

        # Send the command to the server
        client.send(command.encode())

        if command == "BOOK":
            # Receive the date prompt
            date_prompt = client.recv(1024).decode()
            print(date_prompt)
            date_input = get_user_input("Enter the date (YYYY-MM-DD): ")

            # Send the date to the server
            client.send(date_input.encode())

            # Receive the available doctors and timings
            available_doctors = client.recv(4096).decode()
            print(available_doctors)

            # Receive input for doctor and time slot
            booking_request_prompt = "Enter the booking request in format DOCTOR:TIME_SLOT: "
            booking_request = get_user_input(booking_request_prompt)

            # Send the booking request to the server
            client.send(booking_request.encode())

            # Receive the response from the server
            response = client.recv(1024).decode()
            print(response)

        elif command == "CANCEL":
            # Receive the list of booked appointments
            booked_appointments = client.recv(4096).decode()
            print(booked_appointments)

            # Receive input for the cancellation date and time slot
            cancel_prompt = "Enter the cancellation request in format DATE:TIME_SLOT: "
            cancel_input = get_user_input(cancel_prompt)

            # Send the cancellation request to the server
            client.send(cancel_input.encode())

            # Receive the response from the server
            response = client.recv(1024).decode()
            print(response)

        else:
            print("Invalid command. Please use BOOK or CANCEL.")

    finally:
        client.close()

def handle_billing_server():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(("192.168.182.223", 9998))

    try:
        # Receive the prompt for username
        username_prompt = client.recv(1024).decode()
        print(username_prompt)
        username = get_user_input("")

        # Send the username to the server
        client.send(username.encode())

        # Receive the pending bill information and insurance prompt
        bill_info = client.recv(1024).decode()
        print(bill_info)

        if "No pending bills" in bill_info:
            return

        insurance_response = get_user_input("")
        client.send(insurance_response.encode())

        if insurance_response.lower() == "no":
            pay_prompt = client.recv(1024).decode()
            print(pay_prompt)
            pay_response = get_user_input("")
            client.send(pay_response.encode())

        # Receive the final bill
        final_bill = client.recv(1024).decode()
        print(final_bill)

    finally:
        client.close()

def main():
    while True:
        print("\nChoose an operation:")
        print("1. Book/Cancel Appointment")
        print("2. Check Bill")
        print("3. Exit")
        choice = get_user_input("Enter your choice (1/2/3): ")

        if choice == "1":
            handle_main_server()
        elif choice == "2":
            handle_billing_server()
        elif choice == "3":
            print("Exiting the program. Goodbye!")
            break
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")

if __name__ == "__main__":
    main()
