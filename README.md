# worldChat

A browser-based communication platform inspired by Discord, built with HTML, CSS, JavaScript, and Python Flask. The application models a lightweight social ecosystem where users can create accounts, join servers, send direct messages, block users, and add community suggestions. The project intentionally uses session-based in-memory storage instead of PostgreSQL to satisfy the requested architecture constraints.

## Overview

worldChat includes:

- Direct messaging between users
- Group chat-style DM threads
- Server creation and ownership rules
- Invite-code based server membership
- User blocking and unblocking
- Custom user profile skew codes
- Suggestion boxes for community ideas
- Responsive layout for desktop, tablet, and mobile browsing

## Tech Stack

- Frontend: HTML, CSS, vanilla JavaScript
- Backend: Python, Flask
- Persistence: in-memory session storage using Python dictionaries
- Security: no API keys required for default operation

## Project Structure

```text
worldChat/
├── app.py                 # Flask application and in-memory data model
├── requirements.txt       # Python dependencies
├── .gitignore             # Secret and cache exclusions
├── README.md              # Project documentation
├── static/
│   ├── app.js             # Frontend logic and interactions
│   └── styles.css         # Application styling
├── templates/
│   └── index.html         # Application shell and UI layout
└── .env                   # Optional environment file for local secrets
```

## Why the Data Model Is Structured This Way

The application uses a top-level `SESSION_MEMORY` dictionary in `app.py` to simulate a lightweight database. That dictionary contains separate collections for users, servers, DM threads, and suggestions. This approach keeps the application simple and operational without needing PostgreSQL while still reflecting the same high-level data organization a real backend would use.

### Data model snapshot

```python
SESSION_MEMORY = {
    "users": {},
    "servers": {},
    "dm_threads": [],
    "suggestions": [],
}
```

This is intentionally clear and extensible:

- `users` stores account metadata such as user ID, display name, skew code, and blocked users.
- `servers` stores community details, ownership, invite codes, member IDs, and message history.
- `dm_threads` contains direct-message conversation records with participant IDs and message arrays.
- `suggestions` keeps community ideas tied to the user who posted them and the server they target.

## Installation

1. Open a terminal in the project folder.
2. Create and activate a virtual environment if desired.
3. Install dependencies:

```bash
python -m pip install -r requirements.txt
```

## Run the App

Start the Flask server:

```bash
python app.py
```

Then open:

```text
http://127.0.0.1:5000/
```

## How to Use the App

1. Create a user account from the left panel.
2. Choose a user from the login dropdown and sign in.
3. Create a server or join one using a valid invite code.
4. Open a server chat and send messages.
5. Start a direct message from a user card.
6. Block or unblock another user from the community panel.
7. Add suggestions to a server in the right panel.

## Backend Notes

The Flask routes in `app.py` handle the communication logic, including:

- user registration and login
- server creation and deletion
- server join flow with invite codes
- message posting to servers and DM threads
- user blocking logic
- suggestion submission

Each route reads from or updates `SESSION_MEMORY` and responds with JSON so the frontend can re-render the live interface without full page reloads.

## Frontend Notes

The JavaScript file in `static/app.js` keeps the UI synchronized with the backend by calling `/api/state` after each action. This ensures the server list, active chat, user list, DM list, and suggestions are refreshed immediately after events like login, message send, or invite join.

## Requirements and Constraints

This project satisfies the requested constraints:

- No API keys are required for the default local version.
- The app is browser-based and designed to work across desktop and mobile-sized screens.
- Sensitive information is excluded through `.gitignore` and optional `.env` support.
- Code comments explain the data structure and route behavior inside `app.py`.
- Application logic is kept in a simple, readable structure suitable for iterative improvements.

## Important Notes

- This is a prototype built for local development and demo use.
- The in-memory store resets when the Flask process stops.
- The project does not push code to a remote repository unless explicitly authorized.

## Future Enhancements

Potential next steps include:

- persistent file-based storage with JSON backup
- explicit role management for server moderators
- richer channel system with multiple room tabs
- better mobile-first navigation
- real authentication and authorization
- websocket-based instant updates

## License

This project is intended for local educational and prototype development use.
