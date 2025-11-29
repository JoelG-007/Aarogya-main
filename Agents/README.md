# Smart Watch Health Data Generator

## Supabase-integrated agent suite

All Python utilities in `Agents/` now share the same Supabase backend as
the web app (in `Site/`). This lets QR codes, smartwatch data, and the
doctor chat experience operate on live patient data instead of isolated
CSV/JSON files.

### One-time setup

1. **Create a shared `.env` file** (either at the repo root or inside
   `config/.env`) with your Supabase project details:
   ```
   SUPABASE_URL=https://<your-project-id>.supabase.co
   SUPABASE_PROJECT_ID=<your-project-id>
   SUPABASE_ANON_KEY=<your-public-anon-key>
   ```
2. **Install Python dependencies** (ideally inside a virtualenv):
   ```powershell
   cd Agents
   pip install -r requirements.txt
   ```
3. **Optional:** Map logical demo IDs (`Person_1`, etc.) to real
   Supabase patient IDs inside `generate_patient_qr.py` so QR codes
   produce real access tokens.

From this point on, the agents automatically pick up the Supabase
credentials via `python-dotenv` and use the same API routes that the
React app calls.

---
# Smart Watch Health Data Generator

A Python script that generates realistic mock health data from a smart watch, including oxygen saturation (SpO2), heart rate, temperature, blood pressure, steps, and stress levels. The data includes occasional anomalies that simulate health condition deterioration.

## Features

- **Realistic Health Metrics:**
  - Heart Rate (60-100 bpm normal)
  - Blood Oxygen/SpO2 (95-100% normal)
  - Body Temperature (36.1-37.2°C normal)
  - Blood Pressure (110-130/70-85 mmHg normal)
  - Steps per minute
  - Stress Level (1-10 scale)

- **Health Anomalies (15% of readings):**
  - High/Low heart rate
  - Low oxygen saturation
  - High/Low temperature
  - High/Low blood pressure
  - High stress levels

- **Output Formats:**
  - JSON file with detailed readings
  - CSV file for spreadsheet analysis
  - Console summary with alerts

## Usage

### Basic Usage

Run the script to generate 24 hours of health data (readings every 5 minutes):

```powershell
python smartwatch_health_data_generator.py
```

This will create two files:
- `smartwatch_data.json` - JSON format with all readings
- `smartwatch_data.csv` - CSV format for Excel/analysis

### Advanced Usage

You can customize the generator in your own script:

```python
from smartwatch_health_data_generator import SmartWatchDataGenerator

# Create generator
generator = SmartWatchDataGenerator()

# Generate a single reading
reading = generator.generate_reading()
print(reading)

# Generate time series data
# 1 hour of data, reading every minute
readings = generator.generate_time_series(
    duration_minutes=60,
    interval_minutes=1
)

# Generate 7 days of data, reading every 10 minutes
readings = generator.generate_time_series(
    duration_minutes=7*24*60,
    interval_minutes=10
)

# Save data
generator.save_to_json(readings, 'my_data.json')
generator.save_to_csv(readings, 'my_data.csv')

# Print summary
generator.print_summary(readings)
```

### Force Specific Anomalies

```python
# Force a specific anomaly type
reading = generator.generate_reading(force_anomaly='high_heart_rate')
reading = generator.generate_reading(force_anomaly='low_oxygen')
```

Available anomaly types:
- `high_heart_rate`
- `low_heart_rate`
- `low_oxygen`
- `high_temperature`
- `low_temperature`
- `high_bp`
- `low_bp`
- `high_stress`

## Sample Output

```
Smart Watch Health Data Generator
============================================================

Generating 24 hours of health data (every 5 minutes)...

============================================================
Health Data Summary
============================================================
Total readings: 288
Normal readings: 252
Warning readings: 36 (12.5%)

============================================================
Alerts:
============================================================
3. 2025-11-28T19:27:50 - ⚠️ High stress level: 10/10
11. 2025-11-28T20:07:50 - ⚠️ Low temperature: 35.6°C
29. 2025-11-28T21:37:50 - ⚠️ Elevated temperature: 39.3°C
...
```

## Data Structure

Each reading contains:

```json
{
  "timestamp": "2025-11-28T19:17:50",
  "heart_rate": 96,
  "spo2": 97.1,
  "temperature": 36.9,
  "systolic_bp": 114,
  "diastolic_bp": 85,
  "steps": 51,
  "stress_level": 3,
  "status": "normal",
  "alert": null
}
```

When an anomaly is detected:
- `status` changes to `"warning"`
- `alert` contains a descriptive message
- Relevant metrics show abnormal values

## Requirements

- Python 3.10+
- `pip install -r requirements.txt` (installs `pandas`, `qrcode[pil]`, `requests`, `python-dotenv`)

## Use Cases

- Testing health monitoring applications
- Demonstrating data visualization dashboards
- Training machine learning models for health anomaly detection
- Prototyping smart watch apps
- Creating demo datasets for presentations
