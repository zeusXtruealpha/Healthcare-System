import socket
import threading
import json

# Function to load user bills from a file
def load_user_bills():
    try:
        with open('user_bills.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

# Function to save user bills to a file
def save_user_bills(bills):
    with open('user_bills.json', 'w') as f:
        json.dump(bills, f)

def handle_billing_client(client_socket):
    try:
        # Ask for a username
        client_socket.send("Enter your username: ".encode())
        username = client_socket.recv(1024).decode().strip()

        user_bills = load_user_bills()

        if username not in user_bills or user_bills[username] == 0:
            client_socket.send("No pending bills.".encode())
            return

        pending_bill = user_bills[username]
        client_socket.send(f"Pending Bill: {pending_bill}\nDo you have insurance? (Yes/No): ".encode())
        insurance_response = client_socket.recv(1024).decode().strip().lower()

        if insurance_response == "yes":
            generate_paid_bill(client_socket, username, pending_bill, True)
        else:
            client_socket.send("Type 'pay' to proceed with payment: ".encode())
            pay_response = client_socket.recv(1024).decode().strip().lower()
            if pay_response == "pay":
                generate_paid_bill(client_socket, username, pending_bill, False)
            else:
                client_socket.send("Payment cancelled.".encode())

    finally:
        client_socket.close()

def generate_paid_bill(client_socket, username, amount, insurance):
    bill = f"Billing Name: {username}\n"
    bill += f"Insurance: {'Yes' if insurance else 'No'}\n"
    bill += f"Amount: {amount}\n"
    bill += "Paid\n"
    if insurance:
        bill += "Insurance claimed"

    client_socket.send(bill.encode())

    # Clear the pending bill
    user_bills = load_user_bills()
    user_bills[username] = 0
    save_user_bills(user_bills)

def start_billing_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("0.0.0.0", 9998))
    server.listen(5)
    print("Billing Server is listening on port 9998...")
    
    while True:
        client_socket, addr = server.accept()
        print(f"Billing connection established with {addr}")
        billing_handler = threading.Thread(target=handle_billing_client, args=(client_socket,))
        billing_handler.start()

if __name__ == "__main__":
    start_billing_server()
