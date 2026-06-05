from database import fetch_one

user = fetch_one(
    "SELECT * FROM users LIMIT 1"
)

print(user)
print(type(user))