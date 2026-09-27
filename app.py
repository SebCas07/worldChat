import os

from flask import Flask

from routes import create_routes_blueprint

app = Flask(__name__)
app.secret_key = os.environ.get("WORLDCHAT_SECRET_KEY", "worldchat-local-development-key")
app.config["JSON_SORT_KEYS"] = False
app.register_blueprint(create_routes_blueprint())


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
