"""
Interactive Health Data Chat with Llama3
Chat with AI about your health data using natural language
"""

import pandas as pd
import subprocess
import sys


def load_health_data(csv_path='smartwatch_data.csv'):
    """Load health data from CSV file."""
    df = pd.read_csv(csv_path)
    return df


def get_data_context(df):
    """Generate a concise data context string for the LLM."""
    
    # Overall statistics
    context = f"""You are a health assistant with data for {df['person_id'].nunique()} people.

DATA SUMMARY:
People: {', '.join(df['person_id'].unique())}
Readings: {len(df)} total

OVERALL AVERAGES:
HR: {df['heart_rate'].mean():.0f}bpm | SpO2: {df['spo2'].mean():.0f}% | Temp: {df['temperature'].mean():.1f}°C | BP: {df['systolic_bp'].mean():.0f}/{df['diastolic_bp'].mean():.0f} | Stress: {df['stress_level'].mean():.1f}/10 | Sleep: {df['sleep_hours'].mean():.1f}hrs

PER PERSON:
"""
    
    # Add per-person statistics (condensed)
    for person in df['person_id'].unique():
        person_data = df[df['person_id'] == person]
        high_hr = len(person_data[person_data['heart_rate'] > 120])
        low_o2 = len(person_data[person_data['spo2'] < 95])
        high_temp = len(person_data[person_data['temperature'] > 37.2])
        high_bp = len(person_data[person_data['systolic_bp'] > 130])
        high_stress = len(person_data[person_data['stress_level'] > 6])
        poor_sleep = len(person_data[person_data['sleep_hours'] < 6.5])
        
        context += f"\n{person}: HR {person_data['heart_rate'].mean():.0f}bpm, SpO2 {person_data['spo2'].mean():.0f}%, Temp {person_data['temperature'].mean():.1f}°C, BP {person_data['systolic_bp'].mean():.0f}/{person_data['diastolic_bp'].mean():.0f}, Sleep {person_data['sleep_hours'].mean():.1f}hrs"
        
        anomalies = []
        if high_hr > 0: anomalies.append(f"HighHR:{high_hr}")
        if low_o2 > 0: anomalies.append(f"LowO2:{low_o2}")
        if high_temp > 0: anomalies.append(f"Fever:{high_temp}")
        if high_bp > 0: anomalies.append(f"HighBP:{high_bp}")
        if high_stress > 0: anomalies.append(f"Stress:{high_stress}")
        if poor_sleep > 0: anomalies.append(f"PoorSleep:{poor_sleep}")
        
        if anomalies:
            context += f" | Issues: {', '.join(anomalies)}"
    
    context += "\n\nAnswer briefly and clearly."
    
    return context


def query_llama3(prompt, model='llama3'):
    """Send prompt to Llama3 via Ollama and get response."""
    try:
        result = subprocess.run(
            ['ollama', 'run', model],
            input=prompt,
            text=True,
            capture_output=True,
            encoding='utf-8'
        )
        
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            return f"Error: {result.stderr}"
    
    except FileNotFoundError:
        return "Error: Ollama not found. Please ensure Ollama is installed and in your PATH."
    except Exception as e:
        return f"Error: {str(e)}"


def chat_loop(data_context, df):
    """Interactive chat loop with the AI."""
    
    print("\n" + "="*60)
    print("INTERACTIVE HEALTH DATA CHAT")
    print("="*60)
    print("\nChat with AI about health data for multiple people!")
    print("Type 'exit' or 'quit' to end the conversation.")
    print("\n" + "="*60 + "\n")
    
    conversation_history = []
    
    while True:
        try:
            user_input = input("You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['exit', 'quit', 'bye', 'goodbye']:
                print("\nAI: Goodbye! Take care of your health!\n")
                break
            
            # Build conversation prompt
            conversation_text = ""
            for entry in conversation_history[-2:]:  # Keep last 2 exchanges only
                conversation_text += f"User: {entry['user']}\nAI: {entry['assistant']}\n"
            
            if conversation_text:
                full_prompt = f"{data_context}\n\nRecent chat:\n{conversation_text}\nUser: {user_input}\nAI:"
            else:
                full_prompt = f"{data_context}\n\nUser: {user_input}\nAI:"
            
            print("\nAI: ", end="", flush=True)
            response = query_llama3(full_prompt)
            print(response + "\n")
            
            # Save to conversation history
            conversation_history.append({
                'user': user_input,
                'assistant': response
            })
            
        except KeyboardInterrupt:
            print("\n\nAI: Goodbye! Take care of your health!\n")
            break
        except Exception as e:
            print(f"\nError: {e}\n")


def main():
    print("Loading health data...")
    df = load_health_data('smartwatch_data.csv')
    
    print(f"Loaded data for {df['person_id'].nunique()} people with {len(df)} total readings")
    
    print("Preparing AI context...")
    data_context = get_data_context(df)
    
    # Start interactive chat
    chat_loop(data_context, df)


if __name__ == "__main__":
    main()


def main():
    print("Loading health data...")
    df = load_health_data('smartwatch_data.csv')
    
    print("Analyzing statistics...")
    stats, df = analyze_data_statistics(df)
    
    print("\n" + "="*60)
    print("HEALTH DATA LOADED")
    print("="*60)
    print(f"✓ Loaded {stats['total_readings']} readings")
    print(f"✓ Time period: {stats['time_span']}")
    print(f"✓ Detected {stats['total_anomalies']} anomalies")
    
    # Start chat loop
    chat_loop(stats, df)


if __name__ == "__main__":
    main()
