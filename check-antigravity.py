import sqlite3

path = r"C:\Users\Gayatri\.gemini\antigravity\conversations\928c0394-f433-4347-9568-8c339decf19e"

connection = sqlite3.connect(path)

tables = connection.execute(
    "SELECT name FROM sqlite_master WHERE type='table'"
).fetchall()

print("Tables found:")
for table in tables:
    print(table)

connection.close()