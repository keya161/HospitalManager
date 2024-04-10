import socket
import ssl
import json


def load_room_availability():
    try:
        with open("room_availability.json", "r") as json_file:
            return json.load(json_file)
    except Exception as e:
        print(f"Error loading room availability: {e}")
        return None


def save_room_availability(availability):
    try:
        with open("room_availability.json", "w") as json_file:
            json.dump(availability, json_file, indent=4)
    except Exception as e:
        print(f"Error saving room availability: {e}")


def find_room_for_patient(patient_name, room_availability):
    for room, info in room_availability["rooms"].items():
        if info["patient_name"] == patient_name:
            return room
    return "Patient not found"


def handle_client_connection(client_socket, client_type):
    try:
        room_availability = load_room_availability()
        if room_availability is None:
            raise Exception("Failed to load room availability")

        while True:
            data = client_socket.recv(1024)
            if data:
                message = data.decode()
                print(f"Received message from {client_type}: {message}")

                if message.strip().lower() == "quit":
                    print(
                        f"{client_type} {client_socket.getpeername()} has terminated the connection."
                    )
                    break
                #floor manager
                elif client_type == "Floor Manager":

                    if message.startswith("Room"):
                        room_number, status = parse_message(message)

                        if room_number:
                            room_name = room_number
                            room_availability["rooms"][room_name][
                                "availability"] = status
                            if not status:
                                room_availability["rooms"][room_name][
                                    "patient_name"] = ""
                                room_availability["rooms"][room_name][
                                    "patient_disease"] = ""
                            print(
                                f"{room_name} is marked as {'occupied' if status else 'free'}."
                            )
                            client_socket.send(
                                f"{room_name} availability updated.".encode())

                            save_room_availability(room_availability)
                        else:
                            client_socket.send(
                                b"Invalid room number."
                            )
                    elif (message.startswith("Patient")):
                        msg = message.strip().split()
                        name = msg[1].capitalize()
                        room_num = msg[-1].capitalize()
                        disease = msg[4].capitalize()
                        room_availability["rooms"][room_num] = {
                            "patient_name": name,
                            "patient_disease": disease,
                            "availability": 1
                        }

                        save_room_availability(room_availability)
                        client_socket.send(
                            f"Patient {name} assigned to {room_num} with disease {disease}."
                            .encode())

                #receptionist
                elif client_type == "Receptionist":

                    if message.lower().strip().startswith(
                            "check room availability"):
                        print("checking")
                        msg = message.strip().split()
                        disease = msg[-1].capitalize()
                        name = msg[-2].capitalize()
                        rooms = []
                        with open("doctor_diseases.json", "r") as f:
                            data = json.load(f)
                            a = 0
                            for i in data:
                                if disease in data[i]["diseases"]:
                                    rooms = data[i]["rooms"]
                                    a = 1
                            if a == 0:
                                rooms = data["General"]["rooms"]
                        available_rooms = []
                        with open("room_availability.json", "r") as f:
                            data = json.load(f)
                            for i in rooms:
                                if data["rooms"][i]["availability"] == 0:
                                    available_rooms.append(i)
                        if available_rooms:
                            response = ", ".join(available_rooms)
                            client_socket.send(response.encode())
                        else:
                            with open("waiting.json", "r") as f:
                                data = json.load(f)
                            with open("waiting.json", "w") as f:
                                elem = {"rooms":rooms, "disease":disease}
                                data[name] = elem
                                print(data)
                                json.dump(data, f, indent=4)
                            client_socket.send(b"Added to wait list.")
                    elif message.startswith("Find room for"):
                        parts = message.strip().split(maxsplit=3)
                        if len(parts) == 4 and parts[0] == "Find" and parts[
                                1] == "room" and parts[2] == "for":
                            patient_name = parts[3]

                            room = find_room_for_patient(
                                patient_name, room_availability)
                            client_socket.send(
                                f"{patient_name} is in room: {room}".encode())
                        else:
                            client_socket.send(
                                b"Invalid command or message format.")
                    elif message.startswith("Assign room"):
                        parts = message.strip().split()
                        room_name = parts[
                            2]
                        if room_name in room_availability["rooms"]:
                            if room_availability["rooms"][room_name][
                                    "availability"] == 0:
                                patient_name = parts[4]
                                patient_disease = parts[7]
                                room_availability["rooms"][room_name][
                                    "patient_name"] = patient_name
                                room_availability["rooms"][room_name][
                                    "patient_disease"] = patient_disease
                                room_availability["rooms"][room_name][
                                    "availability"] = 1
                                save_room_availability(room_availability)
                                client_socket.send(
                                    f"Patient {patient_name} assigned to {room_name} with disease {patient_disease}."
                                    .encode())
                            else:
                                print("Room is occupied.")
                                client_socket.send(
                                    f"Room is occupied.".encode())
                        else:
                            client_socket.send(b"Invalid room name.")
                    else:
                        client_socket.send(
                            b"Invalid command or message format.")
                else:
                    client_socket.send(b"Invalid client type.")
    except Exception as e:
        print(f"Error handling client connection: {e}")
    finally:
        client_socket.close()


def parse_message(message):
    try:
        parts = message.strip().split(maxsplit=3)
        room_number = parts[1]
        status = 1 if parts[3].lower().startswith("not free") else 0
        return room_number, status
    except Exception as e:
        print(f"Error parsing message: {e}")
        return None, None


def start_server():
    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind(('localhost', 8080))
        server_socket.listen(5)

        #load ssl certificate and key
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        context.load_cert_chain(certfile="server.crt", keyfile="server.key")
        

        with context.wrap_socket(server_socket,
                                 server_side=True) as secure_socket:
            print("The hospital system is secure after the use of SSL ")
            print("Server is listening for connections...")
            while True:
                client_socket, client_address = secure_socket.accept()
                print(f"Connection established with {client_address}")


                data = client_socket.recv(1024)
                if data:
                    client_type = data.decode()
                    print(f"{client_type} connected.")
                    handle_client_connection(client_socket, client_type)
    except Exception as e:
        print(f"Error starting server: {e}")



if __name__ == "__main__":
    start_server()
