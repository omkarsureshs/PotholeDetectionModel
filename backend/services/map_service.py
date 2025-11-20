import json
import os
from datetime import datetime
import sqlite3
from typing import List, Dict, Any

class PotholeMapService:
    def __init__(self, db_path='pothole_data.db'):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize SQLite database for storing pothole locations"""
        os.makedirs('data', exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS potholes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                severity TEXT NOT NULL,
                confidence REAL NOT NULL,
                size REAL NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                image_path TEXT,
                address TEXT,
                road_condition TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS detection_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE NOT NULL,
                total_potholes INTEGER DEFAULT 0,
                avg_severity REAL DEFAULT 0,
                area_coverage TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_pothole_data(self, detection_data: Dict[str, Any], session_id: str = None):
        """Save pothole detection data to database"""
        if not session_id:
            session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Save session info
        cursor.execute('''
            INSERT OR REPLACE INTO detection_sessions 
            (session_id, total_potholes, avg_severity, area_coverage)
            VALUES (?, ?, ?, ?)
        ''', (session_id, len(detection_data.get('detections', [])), 0.5, 'Unknown'))
        
        # Save individual potholes
        for detection in detection_data.get('detections', []):
            location = detection.get('location') or detection_data.get('location')
            severity = detection.get('severity', {})
            
            if location and 'latitude' in location and 'longitude' in location:
                cursor.execute('''
                    INSERT INTO potholes 
                    (latitude, longitude, severity, confidence, size, timestamp, image_path)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    location['latitude'],
                    location['longitude'],
                    severity.get('level', 'medium'),
                    detection.get('confidence', 0.5),
                    detection.get('bbox', [0, 0, 100, 100])[2] * detection.get('bbox', [0, 0, 100, 100])[3],
                    datetime.now().isoformat(),
                    f"detection_{session_id}.jpg"
                ))
        
        conn.commit()
        conn.close()
        return session_id
    
    def get_potholes_by_area(self, ne_lat: float, ne_lng: float, sw_lat: float, sw_lng: float):
        """Get potholes within a bounding box"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                id, latitude, longitude, severity, confidence, size, timestamp,
                CASE 
                    WHEN severity = 'high' THEN 3
                    WHEN severity = 'medium' THEN 2
                    ELSE 1
                END as severity_weight
            FROM potholes 
            WHERE latitude BETWEEN ? AND ? 
            AND longitude BETWEEN ? AND ?
            ORDER BY timestamp DESC
        ''', (sw_lat, ne_lat, sw_lng, ne_lng))
        
        potholes = []
        for row in cursor.fetchall():
            potholes.append({
                'id': row[0],
                'latitude': row[1],
                'longitude': row[2],
                'severity': row[3],
                'confidence': row[4],
                'size': row[5],
                'timestamp': row[6],
                'severity_weight': row[7]
            })
        
        conn.close()
        return potholes
    
    def get_heatmap_data(self):
        """Get data formatted for heatmap visualization"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                latitude, 
                longitude,
                CASE 
                    WHEN severity = 'high' THEN 0.8
                    WHEN severity = 'medium' THEN 0.5
                    ELSE 0.3
                END as weight
            FROM potholes
        ''')
        
        heatmap_data = []
        for row in cursor.fetchall():
            heatmap_data.append({
                'location': {'lat': row[0], 'lng': row[1]},
                'weight': row[2]
            })
        
        conn.close()
        return heatmap_data
    
    def get_statistics(self):
        """Get overall pothole statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                COUNT(*) as total_potholes,
                AVG(CASE 
                    WHEN severity = 'high' THEN 3
                    WHEN severity = 'medium' THEN 2
                    ELSE 1
                END) as avg_severity,
                SUM(CASE WHEN severity = 'high' THEN 1 ELSE 0 END) as high_severity,
                SUM(CASE WHEN severity = 'medium' THEN 1 ELSE 0 END) as medium_severity,
                SUM(CASE WHEN severity = 'low' THEN 1 ELSE 0 END) as low_severity
            FROM potholes
        ''')
        
        stats = cursor.fetchone()
        conn.close()
        
        return {
            'total_potholes': stats[0] if stats else 0,
            'avg_severity': round(stats[1], 2) if stats and stats[1] else 0,
            'high_severity': stats[2] if stats else 0,
            'medium_severity': stats[3] if stats else 0,
            'low_severity': stats[4] if stats else 0
        }

# Global instance
map_service = PotholeMapService()