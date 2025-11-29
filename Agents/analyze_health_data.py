"""
Health Data Analyzer using Llama3 via Ollama
Analyzes smart watch health data and provides insights using LLM
"""

import pandas as pd
import json
import subprocess


def load_health_data(csv_path='smartwatch_data.csv'):
    """Load health data from CSV file."""
    df = pd.read_csv(csv_path)
    return df


def analyze_data_statistics(df):
    """Calculate basic statistics from the health data."""
    stats = {
        'total_readings': len(df),
        'time_span': f"{df['timestamp'].iloc[0]} to {df['timestamp'].iloc[-1]}",
        'heart_rate': {
            'avg': round(df['heart_rate'].mean(), 1),
            'min': df['heart_rate'].min(),
            'max': df['heart_rate'].max(),
            'std': round(df['heart_rate'].std(), 1)
        },
        'spo2': {
            'avg': round(df['spo2'].mean(), 1),
            'min': round(df['spo2'].min(), 1),
            'max': round(df['spo2'].max(), 1)
        },
        'temperature': {
            'avg': round(df['temperature'].mean(), 1),
            'min': round(df['temperature'].min(), 1),
            'max': round(df['temperature'].max(), 1)
        },
        'blood_pressure': {
            'systolic_avg': round(df['systolic_bp'].mean(), 1),
            'diastolic_avg': round(df['diastolic_bp'].mean(), 1),
            'systolic_range': f"{df['systolic_bp'].min()}-{df['systolic_bp'].max()}",
            'diastolic_range': f"{df['diastolic_bp'].min()}-{df['diastolic_bp'].max()}"
        },
        'stress_level': {
            'avg': round(df['stress_level'].mean(), 1),
            'max': df['stress_level'].max()
        },
        'total_steps': df['steps'].sum()
    }
    
    # Identify anomalies
    anomalies = {
        'high_heart_rate': len(df[df['heart_rate'] > 120]),
        'low_heart_rate': len(df[df['heart_rate'] < 60]),
        'low_oxygen': len(df[df['spo2'] < 95]),
        'high_temp': len(df[df['temperature'] > 37.2]),
        'low_temp': len(df[df['temperature'] < 36.1]),
        'high_bp': len(df[df['systolic_bp'] > 130]),
        'low_bp': len(df[df['systolic_bp'] < 110]),
        'high_stress': len(df[df['stress_level'] > 6])
    }
    
    stats['anomalies'] = anomalies
    stats['total_anomalies'] = sum(anomalies.values())
    
    return stats


def create_llm_prompt(stats, df):
    """Create a prompt for the LLM with health data context."""
    
    # Get some sample readings with anomalies
    anomaly_samples = []
    
    if stats['anomalies']['high_heart_rate'] > 0:
        sample = df[df['heart_rate'] > 120].iloc[0]
        anomaly_samples.append(f"High heart rate: {sample['heart_rate']} bpm at {sample['timestamp']}")
    
    if stats['anomalies']['low_oxygen'] > 0:
        sample = df[df['spo2'] < 95].iloc[0]
        anomaly_samples.append(f"Low oxygen: {sample['spo2']}% at {sample['timestamp']}")
    
    if stats['anomalies']['high_temp'] > 0:
        sample = df[df['temperature'] > 37.2].iloc[0]
        anomaly_samples.append(f"High temperature: {sample['temperature']}°C at {sample['timestamp']}")
    
    prompt = f"""You are a health data analyst. Analyze the following smart watch health monitoring data and provide insights:

MONITORING PERIOD:
- Total readings: {stats['total_readings']}
- Time span: {stats['time_span']}

VITAL SIGNS SUMMARY:
Heart Rate:
- Average: {stats['heart_rate']['avg']} bpm
- Range: {stats['heart_rate']['min']}-{stats['heart_rate']['max']} bpm
- Standard deviation: {stats['heart_rate']['std']}

Blood Oxygen (SpO2):
- Average: {stats['spo2']['avg']}%
- Range: {stats['spo2']['min']}-{stats['spo2']['max']}%

Body Temperature:
- Average: {stats['temperature']['avg']}°C
- Range: {stats['temperature']['min']}-{stats['temperature']['max']}°C

Blood Pressure:
- Average: {stats['blood_pressure']['systolic_avg']}/{stats['blood_pressure']['diastolic_avg']} mmHg
- Systolic range: {stats['blood_pressure']['systolic_range']} mmHg
- Diastolic range: {stats['blood_pressure']['diastolic_range']} mmHg

Stress Level:
- Average: {stats['stress_level']['avg']}/10
- Maximum: {stats['stress_level']['max']}/10

Activity:
- Total steps: {stats['total_steps']}

DETECTED ANOMALIES ({stats['total_anomalies']} total):
- High heart rate events: {stats['anomalies']['high_heart_rate']}
- Low heart rate events: {stats['anomalies']['low_heart_rate']}
- Low oxygen saturation: {stats['anomalies']['low_oxygen']}
- High temperature events: {stats['anomalies']['high_temp']}
- Low temperature events: {stats['anomalies']['low_temp']}
- High blood pressure: {stats['anomalies']['high_bp']}
- Low blood pressure: {stats['anomalies']['low_bp']}
- High stress levels: {stats['anomalies']['high_stress']}

EXAMPLE ANOMALIES:
{chr(10).join(anomaly_samples[:3])}

Please provide:
1. Overall health assessment
2. Key concerns or patterns
3. Recommendations for the user
4. Any correlations you notice between different metrics
"""
    
    return prompt


def query_llama3(prompt, model='llama3'):
    """Send prompt to Llama3 via Ollama and get response."""
    try:
        # Use ollama run command
        result = subprocess.run(
            ['ollama', 'run', model],
            input=prompt,
            text=True,
            capture_output=True,
            encoding='utf-8'
        )
        
        if result.returncode == 0:
            return result.stdout
        else:
            return f"Error: {result.stderr}"
    
    except FileNotFoundError:
        return "Error: Ollama not found. Please ensure Ollama is installed and in your PATH."
    except Exception as e:
        return f"Error: {str(e)}"


def main():
    print("Loading health data...")
    df = load_health_data('smartwatch_data.csv')
    
    print("Analyzing statistics...")
    stats = analyze_data_statistics(df)
    
    print("\n" + "="*60)
    print("HEALTH DATA STATISTICS")
    print("="*60)
    print(f"\nTotal Readings: {stats['total_readings']}")
    print(f"Period: {stats['time_span']}")
    print(f"\nHeart Rate: {stats['heart_rate']['avg']} bpm (avg)")
    print(f"Blood Oxygen: {stats['spo2']['avg']}% (avg)")
    print(f"Temperature: {stats['temperature']['avg']}°C (avg)")
    print(f"Blood Pressure: {stats['blood_pressure']['systolic_avg']}/{stats['blood_pressure']['diastolic_avg']} mmHg (avg)")
    print(f"Stress Level: {stats['stress_level']['avg']}/10 (avg)")
    print(f"Total Steps: {stats['total_steps']}")
    print(f"\nTotal Anomalies Detected: {stats['total_anomalies']}")
    
    print("\n" + "="*60)
    print("QUERYING LLAMA3 FOR HEALTH INSIGHTS...")
    print("="*60)
    
    prompt = create_llm_prompt(stats, df)
    
    print("\nGenerating analysis (this may take a moment)...\n")
    response = query_llama3(prompt)
    
    print("="*60)
    print("LLAMA3 HEALTH ANALYSIS")
    print("="*60)
    print(response)
    
    # Save analysis to file
    with open('health_analysis.txt', 'w', encoding='utf-8') as f:
        f.write("HEALTH DATA STATISTICS\n")
        f.write("="*60 + "\n\n")
        f.write(f"Total Readings: {stats['total_readings']}\n")
        f.write(f"Period: {stats['time_span']}\n\n")
        f.write(f"Heart Rate: {stats['heart_rate']['avg']} bpm (avg)\n")
        f.write(f"Blood Oxygen: {stats['spo2']['avg']}% (avg)\n")
        f.write(f"Temperature: {stats['temperature']['avg']}°C (avg)\n")
        f.write(f"Blood Pressure: {stats['blood_pressure']['systolic_avg']}/{stats['blood_pressure']['diastolic_avg']} mmHg (avg)\n")
        f.write(f"Stress Level: {stats['stress_level']['avg']}/10 (avg)\n")
        f.write(f"Total Steps: {stats['total_steps']}\n")
        f.write(f"Total Anomalies: {stats['total_anomalies']}\n")
        f.write("\n\n" + "="*60 + "\n")
        f.write("LLAMA3 HEALTH ANALYSIS\n")
        f.write("="*60 + "\n\n")
        f.write(response)
    
    print("\n" + "="*60)
    print("Analysis saved to: health_analysis.txt")
    print("="*60)


if __name__ == "__main__":
    main()
