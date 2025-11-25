import sqlite3
from datetime import datetime

conn = sqlite3.connect('pothole_data.db')
cur = conn.cursor()

# Get demo user ID
cur.execute("SELECT user_id FROM users WHERE username = 'demo'")
demo_user_id = cur.fetchone()[0]
print(f"Reassigning potholes to demo user: {demo_user_id}")

# Get first 15 pothole IDs
cur.execute("SELECT id FROM potholes ORDER BY id LIMIT 15")
pothole_ids = [row[0] for row in cur.fetchall()]

# Update them
placeholders = ','.join('?' * len(pothole_ids))
cur.execute(f"UPDATE potholes SET user_id = ? WHERE id IN ({placeholders})", [demo_user_id] + pothole_ids)
updated = cur.rowcount
print(f"✅ Updated {updated} potholes to demo user")

# Verify
cur.execute("SELECT COUNT(*) FROM potholes WHERE user_id = ?", (demo_user_id,))
new_count = cur.fetchone()[0]
print(f"Demo user now has {new_count} potholes")

# Get breakdown
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

conn.commit()
conn.close()
