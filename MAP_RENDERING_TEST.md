# Quick Test Guide - Map Rendering Fix

## Changes Made

1. ✅ **Initial Map Location**: Changed from New York [40.7128, -74.0060] to Bangalore [13.3752, 77.0967] where potholes are located
2. ✅ **Improved Logging**: Added detailed console logs to track GeoJSON loading and marker creation
3. ✅ **Severity Handling**: Made severity parsing more robust (lowercase + trim)
4. ✅ **Confidence Display**: Fixed to show as percentage (multiply by 100)

---

## How to Test

### Step 1: Start Backend (if not already running)
```powershell
cd "d:\final Pot\backend"
.\potfinal\Scripts\Activate.ps1
python app.py
```

### Step 2: Start Frontend
```powershell
cd "d:\final Pot\frontend"
npm start
```

This will open `http://localhost:3000` in your browser.

### Step 3: Open Browser Developer Tools
Press **F12** → Go to **Console** tab

### Step 4: Verify Console Logs

You should see logs like:
```
Loading statistics...
Statistics loaded: {total_potholes: 13, high_severity: 2, ...}
Fetching GeoJSON from http://localhost:5000/api/map/geojson
GeoJSON loaded with 13 features
Marker created: {id: 15, severity: "medium", lat: 13.375, lng: 77.096, ...}
Marker created: {id: 13, severity: "high", lat: 13.375, lng: 77.097, ...}
...
✅ GeoJSON layer successfully added with 13 markers
```

### Step 5: Check Network Tab
Click **Network** tab and verify:
- ✅ `localhost:5000/api/map/geojson` returns 200 OK with 13 features
- ✅ `localhost:5000/api/map/statistics` returns 200 OK with stats
- ✅ `localhost:5000/api/user/location` returns 200 OK with coordinates

### Step 6: Verify Map Display

Look for:
- ✅ **Map canvas** with OpenStreetMap tiles centered on Bangalore
- ✅ **Colored markers** showing potholes:
  - 🔴 Red markers = High severity
  - 🟠 Orange markers = Medium severity
  - 🟢 Green markers = Low severity
- ✅ **Statistics panel** (top-left) showing:
  - Total Potholes: 13
  - High Severity: 2
  - Medium Severity: 4
  - Low Severity: 7
- ✅ **Control buttons** (top-left):
  - 📍 My Location
  - 🔄 Refresh
  - 👥 All/My Potholes filter
  - 🔍 Show Heatmap toggle
- ✅ **Map legend** (bottom-left) with severity colors
- ✅ **Blue marker** showing user location (if geolocation enabled)

### Step 7: Interact with Markers

Click any colored marker:
- Should show **popup** with:
  - Severity level (HIGH/MEDIUM/LOW)
  - Confidence percentage (e.g., 92.1%)
  - Date & time reported

### Step 8: Test Controls

1. **"My Location" Button**
   - Map should center on user's location
   - Blue marker should appear

2. **"Refresh" Button**
   - Should reload all data from backend
   - Markers should stay in place
   - Statistics should update

3. **"All Potholes" / "My Potholes Only" Toggle**
   - Toggles between showing all potholes vs. user's own
   - Should update marker count if user has reported any

4. **"Show Heatmap" / "Show Markers" Toggle**
   - Toggles view mode (currently just shows/hides markers)

---

## Troubleshooting

### Issue: Still No Markers Showing

**Check 1:** Console shows errors?
- Look for red error messages in F12 Console
- Common issues:
  - `Failed to fetch from localhost:5000` → Backend not running
  - `Cannot read property 'addTo' of undefined` → Map not initialized

**Check 2:** Network requests successful?
- F12 → Network tab
- Filter for `api/map` requests
- Should all show **200 OK** status
- Response should contain `"type": "FeatureCollection"` and `"features": [...]`

**Check 3:** GeoJSON response valid?
Run in PowerShell to check:
```powershell
$response = Invoke-WebRequest -Uri "http://localhost:5000/api/map/geojson?limit=1" -UseBasicParsing
$response.Content | ConvertFrom-Json | ConvertTo-Json
```

Should show structure like:
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Point",
        "coordinates": [77.096, 13.375]
      },
      "properties": {
        "severity": "high",
        "confidence": 0.92,
        ...
      }
    }
  ]
}
```

**Check 3:** Map container visible?
- Right-click map area → Inspect Element
- Should see `<div ref="mapRef" className="pothole-map-leaflet"></div>`
- Should have height: 600px, width: 100%
- Leaflet tiles should load from openstreetmap.org

**Check 4:** Leaflet CSS loaded?
- F12 → Network tab
- Search for `leaflet.css`
- Should show **200 OK** status

---

## Expected Data

From backend, should have:

**Potholes Distribution:**
- Total: 13 potholes
- High severity: 2 (coordinates ~13.375°N, 77.096°E)
- Medium severity: 4
- Low severity: 7

**Marker Colors:**
- High: `#ff4444` (bright red)
- Medium: `#ffaa00` (orange)
- Low: `#44ff44` (bright green)

**Sample Pothole:**
```json
{
  "id": 13,
  "severity": "high",
  "confidence": 0.9197,
  "timestamp": "2025-11-24T15:09:02",
  "latitude": 13.375,
  "longitude": 77.096,
  "size": 1500,
  "color": "#ff4444"
}
```

---

## Performance Expected

- Map loads: **<2 seconds**
- Markers appear: **<1 second** after GeoJSON loads
- Click marker popup: **instant**
- Refresh data: **<1 second**

---

## If Still Not Working

1. **Restart everything:**
   ```powershell
   # Kill frontend
   Stop-Process -Name node
   
   # Kill backend
   Stop-Process -Name python
   
   # Restart backend first
   cd "d:\final Pot\backend"
   .\potfinal\Scripts\Activate.ps1
   python app.py
   
   # Wait 2 seconds, then start frontend
   cd "d:\final Pot\frontend"
   npm start
   ```

2. **Clear browser cache:**
   - F12 → Application tab → Clear Site Data
   - Reload page

3. **Check database has data:**
   ```powershell
   $response = Invoke-WebRequest -Uri "http://localhost:5000/api/map/statistics" -UseBasicParsing
   $response.Content | ConvertFrom-Json | Format-Table
   ```

4. **Check backend logs** for errors in terminal running Flask

---

## Success Criteria ✅

You'll know it's working when you see:
1. ✅ Map canvas loads with OpenStreetMap tiles
2. ✅ Potholes appear as colored circles
3. ✅ Statistics panel shows correct counts
4. ✅ Clicking markers shows popups
5. ✅ "My Location" button centers map
6. ✅ "Refresh" button reloads data
7. ✅ Filter toggle works
8. ✅ No red errors in F12 Console
9. ✅ All API calls show 200 OK in Network tab
10. ✅ Map is interactive (can pan, zoom, click)

---

**Expected Time:** ~3 seconds from page load to all markers visible

**Next Steps After Verification:**
1. Test detection upload → Save to Map workflow
2. Test PDF report generation
3. Test user authentication (register, login, logout)
4. Test multi-user filtering (if multiple users have reported)
