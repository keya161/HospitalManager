import socket
import ssl


def connect_to_server():
    try:
        
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        #ssl
        context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        context.load_verify_locations("server.crt")
        secure_socket = context.wrap_socket(client_socket,
                                            server_hostname="localhost")

        secure_socket.connect(("localhost", 8080))

        secure_socket.send("Receptionist".encode())

        return secure_socket
    except Exception as e:
        print(f"Error connecting to server: {e}")
        return None


def quit_client(secure_socket):
    try:
        send_message(secure_socket, "Quit")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        secure_socket.close()


def send_message(secure_socket, message):
    try:
        print("Sending message to server:", message)
        secure_socket.send(message.encode())
        response = secure_socket.recv(1024)
        if response:
            print(f"Received response from server: {response.decode()}")
            return response.decode()
    except Exception as e:
        print(f"Error sending/receiving message to/from server: {e}")
        return None


def check_room_availability_and_assign_patient(secure_socket):
    patient_name = input("Enter patient name: ")
    patient_disease = input("Enter patient disease: ")
    try:
        response = send_message(
            secure_socket,
            f"Check room availability for {patient_name} {patient_disease}")
        if response:
            if response.startswith("Added to"):
                print(response)
            else:
                print("Available rooms:", response)
                room_name = str(input("Enter room name to assign patient: "))
                message = f"Assign room {room_name} to {patient_name} with disease {patient_disease}"
                response = send_message(secure_socket, message)
    except Exception as e:
        print(f"Error: {e}")


def visitor(secure_socket):
    try:
        patient_name = input("Enter patient name: ")
        message = f"Find room for {patient_name}"
        response = send_message(secure_socket, message)
        if response:
            print(response)
    except Exception as e:
        print(f"Exception occured: {e}")
        return None


if __name__ == "__main__":
    try:
        secure_socket = connect_to_server()
        if secure_socket:
            while True:
                print("Are you a visitor or a patient?")
                user_type = input("Enter 'visitor' or 'patient': ").lower()
                if user_type == 'patient':
                    check_room_availability_and_assign_patient(secure_socket)
                elif user_type == 'visitor':
                    visitor(secure_socket)
                else:
                    print(
                        "Invalid choice. Please enter 'visitor' or 'patient'.")
    except KeyboardInterrupt:
        pass
    finally:
        quit_client(secure_socket)
