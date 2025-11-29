"""
Doctor Chat Interface - Access patient data via QR code
"""

import pandas as pd
import subprocess
import sys
import os
import json
from datetime import datetime
from typing import Optional

from upload_medical_documents import MedicalDocumentProcessor
from supabase_client import (
    SupabaseError,
    verify_access_code,
    get_patient_health_data,
    get_patient_profile,
)


def load_health_data(csv_path='smartwatch_data.csv'):
    """Load health data from CSV file."""
    df = pd.read_csv(csv_path)
    return df


def load_patient_codes(codes_path='patient_qr_codes/patient_access_codes.json'):
    """Load patient access codes."""
    try:
        with open(codes_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return None


def get_patient_from_code(access_code: str, patient_codes: dict) -> tuple[Optional[str], Optional[str]]:
    """
    Extract local patient ID from access code and validate expiry.

    This is kept for backwards compatibility with locally generated
    (non-Supabase) access codes. Supabase-backed flows should use
    `verify_access_code` instead.
    """
    if access_code not in patient_codes:
        return None, "Invalid access code"

    code_data = patient_codes[access_code]

    expires_at = code_data.get("expires_at")
    if expires_at:
        try:
            exp = datetime.fromisoformat(expires_at)
            if datetime.now() > exp:
                return None, "Access code has expired"
        except Exception:
            pass

    return code_data.get("patient_id"), None


def get_patient_context(df, patient_id, doc_processor=None):
    """Generate context for a specific patient using local CSV data."""

    patient_data = df[df["person_id"] == patient_id]
    
    if len(patient_data) == 0:
        return None
    
    # Calculate statistics
    high_hr = len(patient_data[patient_data['heart_rate'] > 120])
    low_hr = len(patient_data[patient_data['heart_rate'] < 60])
    low_o2 = len(patient_data[patient_data['spo2'] < 95])
    high_temp = len(patient_data[patient_data['temperature'] > 37.2])
    low_temp = len(patient_data[patient_data['temperature'] < 36.1])
    high_bp = len(patient_data[patient_data['systolic_bp'] > 130])
    low_bp = len(patient_data[patient_data['systolic_bp'] < 110])
    high_stress = len(patient_data[patient_data['stress_level'] > 6])
    poor_sleep = len(patient_data[patient_data['sleep_hours'] < 6.5])
    excessive_sleep = len(patient_data[patient_data['sleep_hours'] > 9.0])
    
    context = f"""You are a medical assistant analyzing patient health data.

PATIENT: {patient_id}
Monitoring Period: {patient_data['timestamp'].iloc[0]} to {patient_data['timestamp'].iloc[-1]}
Total Readings: {len(patient_data)}

VITAL SIGNS:
Heart Rate: Average {patient_data['heart_rate'].mean():.1f} bpm (range: {patient_data['heart_rate'].min()}-{patient_data['heart_rate'].max()})
Blood Oxygen: Average {patient_data['spo2'].mean():.1f}% (range: {patient_data['spo2'].min():.1f}-{patient_data['spo2'].max():.1f}%)
Temperature: Average {patient_data['temperature'].mean():.1f}°C (range: {patient_data['temperature'].min():.1f}-{patient_data['temperature'].max():.1f}°C)
Blood Pressure: Average {patient_data['systolic_bp'].mean():.1f}/{patient_data['diastolic_bp'].mean():.1f} mmHg
  Systolic range: {patient_data['systolic_bp'].min()}-{patient_data['systolic_bp'].max()}
  Diastolic range: {patient_data['diastolic_bp'].min()}-{patient_data['diastolic_bp'].max()}
Stress Level: Average {patient_data['stress_level'].mean():.1f}/10 (max: {patient_data['stress_level'].max()}/10)
Sleep Hours: Average {patient_data['sleep_hours'].mean():.1f} hrs (range: {patient_data['sleep_hours'].min():.1f}-{patient_data['sleep_hours'].max():.1f})
Activity: Total {patient_data['steps'].sum()} steps

DETECTED ANOMALIES:
- High heart rate events (>120 bpm): {high_hr}
- Low heart rate events (<60 bpm): {low_hr}
- Low oxygen saturation (<95%): {low_o2}
- High temperature (>37.2°C): {high_temp}
- Low temperature (<36.1°C): {low_temp}
- High blood pressure (>130 systolic): {high_bp}
- Low blood pressure (<110 systolic): {low_bp}
- High stress levels (>6/10): {high_stress}
- Poor sleep (<6.5 hours): {poor_sleep}
- Excessive sleep (>9 hours): {excessive_sleep}
"""
    
    # Add medical documents if available
    if doc_processor:
        docs = doc_processor.get_patient_documents(patient_id)
        if docs:
            context += f"\nMEDICAL DOCUMENTS ({len(docs)}):\n"
            for doc in docs:
                context += f"- {doc['document_type']} ({doc['upload_date'][:10]})\n"
                # Get full document text
                doc_text = doc_processor.get_document_text(patient_id, doc['document_id'])
                if doc_text:
                    # Add document content (limited to prevent token overflow)
                    context += f"  Content preview: {doc_text[:500]}...\n"
    
    context += "\nAnswer doctor's questions about this patient professionally and concisely."
    
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


def doctor_chat(patient_context, patient_id):
    """Interactive chat for doctor with patient data."""
    
    print("\n" + "="*60)
    print(f"PATIENT CONSULTATION - {patient_id}")
    print("="*60)
    print("\nAsk questions about this patient's health data.")
    print("Type 'exit' to end consultation or 'new' for new patient.")
    print("="*60 + "\n")
    
    conversation_history = []
    
    while True:
        try:
            user_input = input("Doctor: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['exit', 'quit']:
                print("\nEnding consultation.\n")
                break
            
            if user_input.lower() == 'new':
                return 'new'
            
            # Build conversation prompt
            conversation_text = ""
            for entry in conversation_history[-2:]:
                conversation_text += f"Doctor: {entry['user']}\nAI: {entry['assistant']}\n"
            
            if conversation_text:
                full_prompt = f"{patient_context}\n\nRecent conversation:\n{conversation_text}\nDoctor: {user_input}\nAI:"
            else:
                full_prompt = f"{patient_context}\n\nDoctor: {user_input}\nAI:"
            
            print("\nAI: ", end="", flush=True)
            response = query_llama3(full_prompt)
            print(response + "\n")
            
            # Save to conversation history
            conversation_history.append({
                'user': user_input,
                'assistant': response
            })
            
        except KeyboardInterrupt:
            print("\n\nEnding consultation.\n")
            break
        except Exception as e:
            print(f"\nError: {e}\n")
    
    return None


def main():
    print("="*60)
    print("DOCTOR PATIENT DATA ACCESS SYSTEM")
    print("="*60)
    
    # Load local CSV data for legacy/offline analysis
    print("\nLoading local smartwatch data (for legacy mode)...")
    try:
        df = load_health_data("smartwatch_data.csv")
        print(f"✓ Local CSV loaded with {df['person_id'].nunique()} patients")
    except FileNotFoundError:
        df = None
        print("⚠️  No local smartwatch_data.csv found; Supabase-only data will be used if available.")

    # Load local QR/access-code mapping (optional / legacy)
    patient_codes = load_patient_codes()

    # Initialize document processor
    doc_processor = MedicalDocumentProcessor()

    print("✓ Medical document system initialized\n")
    
    while True:
        print("="*60)
        print("PATIENT ACCESS")
        print("="*60)
        print("\nOptions:")
        print("1. Scan QR code (enter access code)")
        print("2. List all patients")
        print("3. Upload medical document")
        print("4. View patient documents")
        print("5. Exit")
        
        choice = input("\nSelect option (1-5): ").strip()
        
        if choice == '1':
            access_code = input("\nEnter patient access code from QR: ").strip()

            # Ask whether to verify via Supabase (recommended) or legacy local mapping
            mode = input("Use Supabase for verification? (Y/n): ").strip().lower()
            use_supabase = mode != "n"

            if use_supabase:
                doctor_id = input("Enter your Supabase doctor ID (from web app): ").strip()
                try:
                    verify_result = verify_access_code(doctor_id, access_code)
                except SupabaseError as e:
                    print(f"\n❌ Supabase verification failed: {e}")
                    continue

                patient = verify_result.get("patient") or {}
                patient_id = patient.get("id")
                if not patient_id:
                    print("\n❌ Could not resolve patient from Supabase response.")
                    continue

                print(f"\n✓ Supabase access granted for {patient.get('name', patient_id)}")

                # Fetch latest health data from Supabase
                try:
                    health_result = get_patient_health_data(patient_id, limit=200)
                    health_data = health_result.get("healthData", [])
                except SupabaseError as e:
                    print(f"\n❌ Failed to fetch health data from Supabase: {e}")
                    health_data = []

                # If we have Supabase health data, temporarily build a DataFrame
                if health_data:
                    supabase_df = pd.DataFrame(health_data)
                    supabase_df["person_id"] = patient_id
                    context_df = supabase_df
                elif df is not None:
                    # Fallback to local CSV if available
                    context_df = df
                else:
                    print("\n❌ No health data available for this patient.")
                    continue

                patient_context = get_patient_context(context_df, patient_id, doc_processor)

            else:
                # Legacy/local mode using JSON mapping
                if not patient_codes:
                    print("\n❌ No local patient access codes found. "
                          "Run 'generate_patient_qr.py' or use Supabase mode.")
                    continue

                patient_id, error = get_patient_from_code(access_code, patient_codes)

                if error:
                    print(f"\n❌ {error}")
                    if "expired" in error:
                        print("Please generate new QR codes using 'generate_patient_qr.py'")
                    continue

                print(f"\n✓ Local access granted for {patient_id}")

                if df is None:
                    print("\n❌ Local smartwatch_data.csv is missing; cannot build context.")
                    continue

                patient_context = get_patient_context(df, patient_id, doc_processor)

            if not patient_context:
                print(f"\n❌ No data found for {patient_id}")
                continue

            # Start consultation
            result = doctor_chat(patient_context, patient_id)

            if result == "new":
                continue
        
        elif choice == '2':
            print("\n" + "="*60)
            print("REGISTERED PATIENTS")
            print("="*60)
            
            # Group codes by patient
            patients_list = {}
            for code, data in patient_codes.items():
                patient_id = data['patient_id']
                if patient_id not in patients_list:
                    patients_list[patient_id] = []
                patients_list[patient_id].append({
                    'code': code,
                    'expires': data['expires_at'],
                    'generated': data['generated_at']
                })
            
            for patient_id in sorted(patients_list.keys()):
                doc_count = len(doc_processor.get_patient_documents(patient_id))
                print(f"\n{patient_id}")
                print(f"  Medical Documents: {doc_count}")
                
                for code_info in patients_list[patient_id]:
                    expires_at = datetime.fromisoformat(code_info['expires'])
                    is_expired = datetime.now() > expires_at
                    status = "❌ EXPIRED" if is_expired else "✓ Valid"
                    
                    print(f"  Access Code: {code_info['code']} [{status}]")
                    print(f"  Expires: {expires_at.strftime('%Y-%m-%d %H:%M:%S')}")
                    print(f"  QR Code: patient_qr_codes/{patient_id}_qr_code.png")
            
            print("\n" + "="*60)
        
        elif choice == '3':
            patient_id = input("\nEnter Patient ID (e.g., Person_1): ").strip()
            file_path = input("Enter file path (PDF or image): ").strip()
            
            doc_types = ['medical_report', 'prescription', 'lab_result', 'diagnosis', 'xray', 'scan']
            print("\nDocument types:", ', '.join(doc_types))
            doc_type = input("Enter document type: ").strip() or 'medical_report'
            
            result = doc_processor.upload_document(file_path, patient_id, doc_type)
            
            if result['status'] == 'success':
                print(f"\n✓ Document uploaded successfully!")
                print(f"Document ID: {result['document_id']}")
            else:
                print(f"\n❌ Error: {result['message']}")
        
        elif choice == '4':
            patient_id = input("\nEnter Patient ID: ").strip()
            docs = doc_processor.get_patient_documents(patient_id)
            
            if docs:
                print(f"\n{len(docs)} document(s) for {patient_id}:")
                for i, doc in enumerate(docs, 1):
                    print(f"\n{i}. Document ID: {doc['document_id']}")
                    print(f"   Type: {doc['document_type']}")
                    print(f"   File: {doc['original_file']}")
                    print(f"   Date: {doc['upload_date']}")
                    print(f"   Preview: {doc['text_preview']}")
            else:
                print(f"\nNo documents found for {patient_id}")
        
        elif choice == '5':
            print("\nGoodbye!\n")
            break
        
        else:
            print("\n❌ Invalid option. Please select 1-5.")


if __name__ == "__main__":
    main()
