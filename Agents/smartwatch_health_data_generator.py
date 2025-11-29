"""
Smart Watch Health Data Generator
Generates realistic health monitoring data with occasional anomalies
indicating potential health concerns.
"""

import random
import json
from datetime import datetime, timedelta
import csv
from typing import Optional

from supabase_client import post_health_reading, SupabaseError


class SmartWatchDataGenerator:
    """Generate realistic smart watch health data with anomalies."""
    
    def __init__(self):
        # Normal ranges for health metrics
        self.normal_ranges = {
            'heart_rate': (60, 100),
            'spo2': (95, 100),
            'temperature': (36.1, 37.2),
            'systolic_bp': (110, 130),
            'diastolic_bp': (70, 85),
            'steps': (0, 150),  # per minute
            'stress_level': (1, 5),  # 1-10 scale
            'sleep_hours': (6.5, 9.0)  # hours per day
        }
        
        # Abnormal conditions (anomalies)
        self.anomaly_types = {
            'high_heart_rate': {'heart_rate': (120, 180), 'probability': 0.05},
            'low_heart_rate': {'heart_rate': (40, 55), 'probability': 0.03},
            'low_oxygen': {'spo2': (85, 94), 'probability': 0.04},
            'high_temperature': {'temperature': (37.5, 39.5), 'probability': 0.03},
            'low_temperature': {'temperature': (35.0, 36.0), 'probability': 0.02},
            'high_bp': {'systolic_bp': (140, 180), 'diastolic_bp': (90, 110), 'probability': 0.04},
            'low_bp': {'systolic_bp': (80, 100), 'diastolic_bp': (50, 65), 'probability': 0.03},
            'high_stress': {'stress_level': (7, 10), 'probability': 0.06},
            'poor_sleep': {'sleep_hours': (3.0, 5.5), 'probability': 0.04},
            'excessive_sleep': {'sleep_hours': (10.0, 12.0), 'probability': 0.02}
        }
    
    def _should_trigger_anomaly(self):
        """Determine if an anomaly should occur."""
        return random.random() < 0.15  # 15% chance of any anomaly
    
    def _select_anomaly(self):
        """Select which type of anomaly to trigger."""
        anomalies = list(self.anomaly_types.keys())
        weights = [self.anomaly_types[a]['probability'] for a in anomalies]
        return random.choices(anomalies, weights=weights)[0]
    
    def generate_reading(self, timestamp=None, force_anomaly=None):
        """
        Generate a single health data reading.
        
        Args:
            timestamp: datetime object for the reading (default: now)
            force_anomaly: string to force a specific anomaly type
        
        Returns:
            dict with health metrics and metadata
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        # Determine if this reading should be anomalous
        is_anomaly = force_anomaly is not None or self._should_trigger_anomaly()
        anomaly_type = force_anomaly if force_anomaly else (
            self._select_anomaly() if is_anomaly else None
        )
        
        # Generate base readings
        data = {
            'timestamp': timestamp.isoformat(),
            'heart_rate': random.randint(*self.normal_ranges['heart_rate']),
            'spo2': round(random.uniform(*self.normal_ranges['spo2']), 1),
            'temperature': round(random.uniform(*self.normal_ranges['temperature']), 1),
            'systolic_bp': random.randint(*self.normal_ranges['systolic_bp']),
            'diastolic_bp': random.randint(*self.normal_ranges['diastolic_bp']),
            'steps': random.randint(*self.normal_ranges['steps']),
            'stress_level': random.randint(*self.normal_ranges['stress_level']),
            'sleep_hours': round(random.uniform(*self.normal_ranges['sleep_hours']), 1)
        }
        
        # Apply anomaly if needed
        if is_anomaly and anomaly_type:
            anomaly_config = self.anomaly_types[anomaly_type]
            
            for metric, value_range in anomaly_config.items():
                if metric != 'probability':
                    if isinstance(value_range[0], int):
                        data[metric] = random.randint(*value_range)
                    else:
                        data[metric] = round(random.uniform(*value_range), 1)
        
        return data
    
    def generate_time_series(self, duration_minutes=60, interval_minutes=1):
        """
        Generate a time series of health data.
        
        Args:
            duration_minutes: Total duration to simulate
            interval_minutes: Time between readings
        
        Returns:
            list of health data readings
        """
        readings = []
        start_time = datetime.now()
        
        num_readings = duration_minutes // interval_minutes
        
        for i in range(num_readings):
            timestamp = start_time + timedelta(minutes=i * interval_minutes)
            reading = self.generate_reading(timestamp)
            readings.append(reading)
        
        return readings
    
    def save_to_json(self, readings, filename='health_data.json'):
        """Save readings to a JSON file."""
        with open(filename, 'w') as f:
            json.dump(readings, f, indent=2)
    
    def save_to_csv(self, readings, filename='health_data.csv'):
        """Save readings to a CSV file."""
        if not readings:
            return
        
        fieldnames = readings[0].keys()
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(readings)
    
def main(patient_id: Optional[str] = None, push_to_supabase: bool = True):
    """
    Main function to generate data for demo patients.

    If `push_to_supabase` is True and `patient_id` is provided, readings for
    that logical patient will be pushed into Supabase so they appear in the
    web dashboards.
    """
    generator = SmartWatchDataGenerator()

    # Default demo people (used for local CSV/JSON and, optionally, mapping
    # to real Supabase patient IDs if you choose to)
    people = ['Person_1', 'Person_2', 'Person_3', 'Person_4', 'Person_5', 'Person_6']

    all_readings = []

    for person in people:
        readings = generator.generate_time_series(
            duration_minutes=24 * 60,   # 24 hours
            interval_minutes=5 * 60     # 5 hours = 300 minutes
        )

        for reading in readings:
            reading['person_id'] = person
            all_readings.append(reading)

            # Optionally push to Supabase for a single mapped patient
            if push_to_supabase and patient_id:
                try:
                    post_health_reading(patient_id, reading)
                except SupabaseError as e:
                    # Fail gracefully but keep generating local data
                    print(f"[Supabase error] {e}")
                    push_to_supabase = False  # avoid spamming on repeated failure

    # Always keep local files for offline analysis
    generator.save_to_json(all_readings, 'smartwatch_data.json')
    generator.save_to_csv(all_readings, 'smartwatch_data.csv')


if __name__ == "__main__":
    # For quick testing you can hard-code a Supabase patient ID here, e.g. the
    # seeded demo patient. Otherwise, pass None to only generate local files.
    demo_patient_id = None  # replace with real Supabase patient ID when ready
    main(patient_id=demo_patient_id, push_to_supabase=bool(demo_patient_id))
