from database import fetch_one

def login_user(username, password):
    # ambil user berdasarkan username
    user = fetch_one(
        "SELECT * FROM users WHERE username = ?",
        (username,)
    )

    # cek apakah user ada dan password cocok
    if user and user["password"] == password:
        return user
    else:
        return None