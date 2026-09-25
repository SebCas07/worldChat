from __future__ import annotations

import random
import string
from datetime import datetime, timezone
from uuid import uuid4

from flask import Flask, jsonify, render_template, request, session

app = Flask(__name__)
app.secret_key = "worldchat-dev-secret"
app.config["JSON_SORT_KEYS"] = False

# SESSION_MEMORY acts as the project database for this prototype.
# It preserves user accounts, server metadata, invite codes, and chats in memory
# while the application is running. This meets the requirement to use session memory
# rather than a database like Postgres.
SESSION_MEMORY = {
    "users": {},
    "servers": {},
    "dm_threads": [],
    "suggestions": [],
}


def iso_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def generate_skew_code() -> str:
    adjectives = ["Solar", "Nova", "Pixel", "Drift", "Echo", "Frost", "Cinder", "Orbit"]
    nouns = ["Fox", "Wren", "Falcon", "Drake", "Raven", "Hawk", "Otter", "Bloom"]
    suffix = "".join(random.choice(string.digits) for _ in range(3))
    return f"{random.choice(adjectives)}-{random.choice(nouns)}-{suffix}"


def generate_invite_code() -> str:
    return "".join(random.choice(string.ascii_uppercase + string.digits) for _ in range(8))


def user_payload(user: dict) -> dict:
    return {
        "id": user["id"],
        "name": user["name"],
        "skew_code": user["skew_code"],
        "blocked_users": user.get("blocked_users", []),
        "status": user.get("status", "online"),
    }


def server_payload(server: dict) -> dict:
    return {
        "id": server["id"],
        "name": server["name"],
        "description": server.get("description", ""),
        "owner_id": server["owner_id"],
        "invite_code": server["invite_code"],
        "channels": server.get("channels", ["general"]),
        "members": server.get("members", []),
        "messages": server.get("messages", []),
    }


def seed_demo_data() -> None:
    if SESSION_MEMORY["users"]:
        return

    demo_users = {
        "u-1": {
            "id": "u-1",
            "name": "Ava",
            "skew_code": "Solar-Fox-301",
            "blocked_users": [],
            "status": "online",
        },
        "u-2": {
            "id": "u-2",
            "name": "Leo",
            "skew_code": "Nova-Hawk-882",
            "blocked_users": [],
            "status": "online",
        },
        "u-3": {
            "id": "u-3",
            "name": "Maya",
            "skew_code": "Echo-Raven-147",
            "blocked_users": [],
            "status": "idle",
        },
    }
    SESSION_MEMORY["users"] = demo_users
    SESSION_MEMORY["servers"] = {
        "s-1": {
            "id": "s-1",
            "name": "Pixel Guild",
            "description": "A cozy tech and design hangout.",
            "owner_id": "u-1",
            "invite_code": "PIXEL42",
            "channels": ["general", "announcements", "projects"],
            "members": ["u-1", "u-2", "u-3"],
            "messages": [
                {
                    "id": "m-1",
                    "user_id": "u-1",
                    "user_name": "Ava",
                    "text": "Welcome to Pixel Guild!",
                    "created_at": iso_now(),
                }
            ],
        }
    }
    SESSION_MEMORY["dm_threads"] = [
        {
            "id": "dm-1",
            "participants": ["u-1", "u-2"],
            "messages": [
                {
                    "id": "dm-m-1",
                    "user_id": "u-2",
                    "user_name": "Leo",
                    "text": "Want to meet later for a review session?",
                    "created_at": iso_now(),
                }
            ],
        }
    ]
    SESSION_MEMORY["suggestions"] = [
        {
            "id": "suggest-1",
            "user_id": "u-3",
            "server_id": "s-1",
            "text": "Maybe we can host a game night this Friday.",
        }
    ]


seed_demo_data()


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/state")
def get_state():
    users = [user_payload(user) for user in SESSION_MEMORY["users"].values()]
    servers = [server_payload(server) for server in SESSION_MEMORY["servers"].values()]

    current_user_id = session.get("user_id")
    current_user = SESSION_MEMORY["users"].get(current_user_id)

    return jsonify(
        {
            "current_user": user_payload(current_user) if current_user else None,
            "users": users,
            "servers": servers,
            "dm_threads": SESSION_MEMORY["dm_threads"],
            "suggestions": SESSION_MEMORY["suggestions"],
        }
    )


@app.post("/api/register")
def register_user():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "Name is required."}), 400

    user_id = f"u-{uuid4().hex[:6]}"
    user = {
        "id": user_id,
        "name": name,
        "skew_code": generate_skew_code(),
        "blocked_users": [],
        "status": "online",
    }
    SESSION_MEMORY["users"][user_id] = user
    session["user_id"] = user_id
    return jsonify({"message": "User created.", "user": user_payload(user)})


@app.post("/api/login")
def login_user():
    data = request.get_json(silent=True) or {}
    user_id = data.get("user_id")
    if not user_id or user_id not in SESSION_MEMORY["users"]:
        return jsonify({"error": "Unknown user."}), 400

    session["user_id"] = user_id
    SESSION_MEMORY["users"][user_id]["status"] = "online"
    return jsonify({"message": "Logged in.", "user": user_payload(SESSION_MEMORY["users"][user_id])})


@app.post("/api/logout")
def logout_user():
    current_user_id = session.get("user_id")
    if current_user_id and current_user_id in SESSION_MEMORY["users"]:
        SESSION_MEMORY["users"][current_user_id]["status"] = "offline"
    session.clear()
    return jsonify({"message": "Logged out."})


@app.post("/api/servers")
def create_server():
    current_user_id = session.get("user_id")
    if not current_user_id:
        return jsonify({"error": "Login required."}), 401

    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    description = (data.get("description") or "").strip()
    if not name:
        return jsonify({"error": "Server name is required."}), 400

    server_id = f"s-{uuid4().hex[:6]}"
    server = {
        "id": server_id,
        "name": name,
        "description": description or "A new community space.",
        "owner_id": current_user_id,
        "invite_code": generate_invite_code(),
        "channels": ["general"],
        "members": [current_user_id],
        "messages": [
            {
                "id": f"m-{uuid4().hex[:6]}",
                "user_id": current_user_id,
                "user_name": SESSION_MEMORY["users"][current_user_id]["name"],
                "text": f"{name} has been created.",
                "created_at": iso_now(),
            }
        ],
    }
    SESSION_MEMORY["servers"][server_id] = server
    return jsonify({"message": "Server created.", "server": server_payload(server)})


@app.post("/api/servers/join")
def join_server():
    current_user_id = session.get("user_id")
    if not current_user_id:
        return jsonify({"error": "Login required."}), 401

    data = request.get_json(silent=True) or {}
    invite_code = (data.get("invite_code") or "").strip().upper()
    if not invite_code:
        return jsonify({"error": "Invite code required."}), 400

    target_server = None
    for server in SESSION_MEMORY["servers"].values():
        if server["invite_code"] == invite_code:
            target_server = server
            break

    if not target_server:
        return jsonify({"error": "Invite code not found."}), 404

    if current_user_id in target_server["members"]:
        return jsonify({"message": "Already a member."})

    target_server["members"].append(current_user_id)
    target_server["messages"].append(
        {
            "id": f"m-{uuid4().hex[:6]}",
            "user_id": current_user_id,
            "user_name": SESSION_MEMORY["users"][current_user_id]["name"],
            "text": f"{SESSION_MEMORY['users'][current_user_id]['name']} joined the server.",
            "created_at": iso_now(),
        }
    )
    return jsonify({"message": "Joined server.", "server": server_payload(target_server)})


@app.delete("/api/servers/<server_id>")
def delete_server(server_id):
    current_user_id = session.get("user_id")
    if not current_user_id:
        return jsonify({"error": "Login required."}), 401

    server = SESSION_MEMORY["servers"].get(server_id)
    if not server:
        return jsonify({"error": "Server not found."}), 404

    if server["owner_id"] != current_user_id:
        return jsonify({"error": "Only the owner can delete this server."}), 403

    del SESSION_MEMORY["servers"][server_id]
    return jsonify({"message": "Server deleted."})


@app.post("/api/servers/<server_id>/messages")
def post_server_message(server_id):
    current_user_id = session.get("user_id")
    if not current_user_id:
        return jsonify({"error": "Login required."}), 401

    server = SESSION_MEMORY["servers"].get(server_id)
    if not server:
        return jsonify({"error": "Server not found."}), 404

    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    if not text:
        return jsonify({"error": "Message text is required."}), 400

    if current_user_id not in server["members"]:
        return jsonify({"error": "You must be a member to chat here."}), 403

    message = {
        "id": f"m-{uuid4().hex[:6]}",
        "user_id": current_user_id,
        "user_name": SESSION_MEMORY["users"][current_user_id]["name"],
        "text": text,
        "created_at": iso_now(),
    }
    server["messages"].append(message)
    return jsonify({"message": "Message sent.", "message_item": message})


@app.post("/api/dm")
def create_dm():
    current_user_id = session.get("user_id")
    if not current_user_id:
        return jsonify({"error": "Login required."}), 401

    data = request.get_json(silent=True) or {}
    other_user_id = data.get("user_id")
    if not other_user_id or other_user_id == current_user_id:
        return jsonify({"error": "Choose another user."}), 400

    for thread in SESSION_MEMORY["dm_threads"]:
        members = set(thread["participants"])
        if {current_user_id, other_user_id}.issubset(members):
            return jsonify({"message": "Direct chat already exists.", "thread": thread})

    thread = {
        "id": f"dm-{uuid4().hex[:6]}",
        "participants": [current_user_id, other_user_id],
        "messages": [],
    }
    SESSION_MEMORY["dm_threads"].append(thread)
    return jsonify({"message": "Created direct message thread.", "thread": thread})


@app.post("/api/dm/<thread_id>/messages")
def send_dm_message(thread_id):
    current_user_id = session.get("user_id")
    if not current_user_id:
        return jsonify({"error": "Login required."}), 401

    thread = next((item for item in SESSION_MEMORY["dm_threads"] if item["id"] == thread_id), None)
    if not thread:
        return jsonify({"error": "Conversation not found."}), 404

    if current_user_id not in thread["participants"]:
        return jsonify({"error": "You are not part of this chat."}), 403

    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    if not text:
        return jsonify({"error": "Message text is required."}), 400

    message = {
        "id": f"dm-m-{uuid4().hex[:6]}",
        "user_id": current_user_id,
        "user_name": SESSION_MEMORY["users"][current_user_id]["name"],
        "text": text,
        "created_at": iso_now(),
    }
    thread["messages"].append(message)
    return jsonify({"message": "Direct message sent.", "message_item": message})


@app.post("/api/users/<user_id>/block")
def block_user(user_id):
    current_user_id = session.get("user_id")
    if not current_user_id:
        return jsonify({"error": "Login required."}), 401

    target_user = SESSION_MEMORY["users"].get(user_id)
    if not target_user:
        return jsonify({"error": "User not found."}), 404

    current_user = SESSION_MEMORY["users"][current_user_id]
    if user_id not in current_user.get("blocked_users", []):
        current_user.setdefault("blocked_users", []).append(user_id)
    return jsonify({"message": f"Blocked {target_user['name']}.", "user": user_payload(current_user)})


@app.post("/api/users/<user_id>/unblock")
def unblock_user(user_id):
    current_user_id = session.get("user_id")
    if not current_user_id:
        return jsonify({"error": "Login required."}), 401

    current_user = SESSION_MEMORY["users"].get(current_user_id)
    if not current_user:
        return jsonify({"error": "User not found."}), 404

    current_user["blocked_users"] = [value for value in current_user.get("blocked_users", []) if value != user_id]
    return jsonify({"message": "User unblocked.", "user": user_payload(current_user)})


@app.post("/api/suggestions")
def add_suggestion():
    current_user_id = session.get("user_id")
    if not current_user_id:
        return jsonify({"error": "Login required."}), 401

    data = request.get_json(silent=True) or {}
    server_id = data.get("server_id")
    text = (data.get("text") or "").strip()
    if not server_id or not text:
        return jsonify({"error": "Server and suggestion text are required."}), 400

    suggestion = {
        "id": f"suggest-{uuid4().hex[:6]}",
        "user_id": current_user_id,
        "server_id": server_id,
        "text": text,
    }
    SESSION_MEMORY["suggestions"].append(suggestion)
    return jsonify({"message": "Suggestion saved.", "suggestion": suggestion})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
