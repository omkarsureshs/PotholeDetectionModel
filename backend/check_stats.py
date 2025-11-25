import sqlite3

conn = sqlite3.connect('pothole_data.db')
cur = conn.cursor()

# Get tables
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cur.fetchall()]
print('Tables:', tables)

# Check user_statistics
print('\n--- user_statistics table ---')
try:
    cur.execute('SELECT * FROM user_statistics LIMIT 10')
    cols = [desc[0] for desc in cur.description]
    print('Columns:', cols)
    rows = cur.fetchall()
    print(f'Total rows: {len(rows)}')
    for row in rows:
        print(row)
except Exception as e:
    print(f'Error: {e}')

# Check potholes count per user
print('\n--- Potholes per user_id ---')
cur.execute('SELECT user_id, COUNT(*) as count FROM potholes GROUP BY user_id ORDER BY count DESC LIMIT 10')
for row in cur.fetchall():
    print(f"User {row[0][:8]}...: {row[1]} potholes")

conn.close()
