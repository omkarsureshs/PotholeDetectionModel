import sqlite3

conn = sqlite3.connect('pothole_data.db')
cur = conn.cursor()

# Get demo user ID
cur.execute("SELECT user_id FROM users WHERE username = 'demo'")
demo_user_id = cur.fetchone()[0]
print(f"Demo user ID: {demo_user_id}")

# Count potholes for this user
cur.execute("SELECT COUNT(*) FROM potholes WHERE user_id = ?", (demo_user_id,))
count = cur.fetchone()[0]
print(f"Potholes for demo user: {count}")

# Get severity breakdown
cur.execute("""
    SELECT 
        SUM(CASE WHEN severity = 'high' THEN 1 ELSE 0 END) as high,
        SUM(CASE WHEN severity = 'medium' THEN 1 ELSE 0 END) as medium,
        SUM(CASE WHEN severity = 'low' THEN 1 ELSE 0 END) as low
    FROM potholes
    WHERE user_id = ?
""", (demo_user_id,))
h, m, l = cur.fetchone()
print(f"Breakdown: {h or 0}H, {m or 0}M, {l or 0}L")

conn.close()
