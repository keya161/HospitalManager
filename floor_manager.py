import socket
import ssl
import json


def connect_to_server():
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        #ssl
        context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        context.load_verify_locations("server.crt")
        secure_socket = context.wrap_socket(client_socket,
                                            server_hostname="localhost")

        secure_socket.connect(("localhost", 8080))

        secure_socket.send("Floor Manager".encode())

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


def waiting_room(room_num, secure_socket):
    try:
        with open(r"waiting.json", "r") as w:
            val = json.load(w)
            for patient_name, patient_data in val.items():
                if room_num in patient_data["rooms"]:
                    disease = patient_data["disease"]
                    print(
                        f"Patient {patient_name} with disease {disease} is waiting in room {room_num}"
                    )
                    message = f"Patient {patient_name} with disease {disease} waiting in room {room_num}"
                    send_message(secure_socket, message)
                    updated_waiting_list = {
                        name: data
                        for name, data in val.items() if name != patient_name
                    }
                    with open("waiting.json", "w") as file:
                        json.dump(updated_waiting_list, file, indent=4)
                    print(f"Patient {patient_name} removed from waiting list.")
                    return True
            return False
    except Exception as e:
        print(f"Error in waiting_room function: {e}")


def send_message(secure_socket, message):
    try:
        secure_socket.send(message.encode())
        response = secure_socket.recv(1024)
        if response:
            print(f"Received response from server: {response.decode()}")
    except Exception as e:
        print(f"Error sending message to server: {e}")


def update_room_availability(secure_socket):
    try:
        room_number = input("Enter room number : ")

        if room_number:
            message = f"Room {room_number} is free"
            if (waiting_room(room_number, secure_socket)):
                return None
            
            send_message(secure_socket, message)
        else:
            print("Invalid room number.")

        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    try:
        secure_socket = connect_to_server()
        if secure_socket:
            update_room_availability(secure_socket)
    except KeyboardInterrupt:
        pass
    finally:
        quit_client(secure_socket)
