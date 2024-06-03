from flask import Flask, render_template, request, session, redirect, url_for, jsonify
from flask_socketio import join_room, leave_room, send, SocketIO
import random
from string import ascii_uppercase

app = Flask(__name__)
app.config["SECRET_KEY"] = "hjhjsdahhds"
socketio = SocketIO(app)

rooms = {}

def generate_unique_code(length):
    while True:
        code = ""
        for _ in range(length):
            code += random.choice(ascii_uppercase)

        if code not in rooms:
            break

    return code

@app.route("/")
def index():
    return render_template("index.html", public_room_list=get_public_rooms())

def get_public_rooms():
    return [{"code": code, "creator": details["creator"]} for code, details in rooms.items() if details["public"]]

@socketio.on('create')
def handle_create(data):
    name = data.get('name')
    public = data.get('public')

    if not name:
        return {"error": "Please enter a name."}

    room_code = generate_unique_code(4)
    rooms[room_code] = {"members": 0, "messages": [], "public": public, "creator": name}

    session['room'] = room_code
    session['name'] = name

    return {"room": room_code}

@socketio.on('join')
def handle_join(data):
    name = data.get('name')
    room = data.get('code')

    if not name:
        return {"error": "Please enter a name."}

    if room not in rooms:
        return {"error": "Room does not exist."}

    session['room'] = room
    session['name'] = name

    return {}

@socketio.on("message")
def handle_message(data):
    room = session.get("room")
    if room not in rooms:
        return

    content = {
        "name": session.get("name"),
        "message": data["data"]
    }
    send(content, to=room)
    rooms[room]["messages"].append(content)

@socketio.on("connect")
def handle_connect():
    room = session.get("room")
    name = session.get("name")
    if not room or not name:
        return
    if room not in rooms:
        leave_room(room)
        return

    join_room(room)
    send({"name": name, "message": "has entered the room"}, to=room)
    rooms[room]["members"] += 1

@socketio.on("disconnect")
def handle_disconnect():
    room = session.get("room")
    name = session.get("name")
    leave_room(room)

    if room in rooms:
        rooms[room]["members"] -= 1
        if rooms[room]["members"] <= 0:
            del rooms[room]

    send({"name": name, "message": "has left the room"}, to=room)

if __name__ == "__main__":
    socketio.run(app,  host='0.0.0.0', port=5001, debug=True)
