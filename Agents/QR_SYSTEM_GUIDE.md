# Patient QR Code System - Quick Start Guide

## Overview
This system generates QR codes for each patient and allows doctors to access individual patient data through an AI chat interface.

## Generated Files

### QR Codes Directory: `patient_qr_codes/`
- `Person_1_qr_code.png` - QR code for Person 1
- `Person_2_qr_code.png` - QR code for Person 2
- `Person_3_qr_code.png` - QR code for Person 3
- `Person_4_qr_code.png` - QR code for Person 4
- `Person_5_qr_code.png` - QR code for Person 5
- `Person_6_qr_code.png` - QR code for Person 6
- `patient_access_codes.json` - Access code mapping

## Access Codes

| Patient | Access Code |
|---------|-------------|
| Person_1 | PATIENT_Person_1 |
| Person_2 | PATIENT_Person_2 |
| Person_3 | PATIENT_Person_3 |
| Person_4 | PATIENT_Person_4 |
| Person_5 | PATIENT_Person_5 |
| Person_6 | PATIENT_Person_6 |

## Usage

### Step 1: Generate Patient Data (if not already done)
```powershell
C:/Users/manis/Downloads/watch/.venv/Scripts/python.exe smartwatch_health_data_generator.py
```

### Step 2: Generate QR Codes
```powershell
C:/Users/manis/Downloads/watch/.venv/Scripts/python.exe generate_patient_qr.py
```

### Step 3: Start Doctor Interface
```powershell
C:/Users/manis/Downloads/watch/.venv/Scripts/python.exe doctor_chat.py
```

## How It Works

1. **Doctor accesses the system** - Runs `doctor_chat.py`
2. **Scans patient QR code** or enters access code (e.g., `PATIENT_Person_1`)
3. **System loads that patient's data only**
4. **AI assistant provides patient-specific information**
5. **Doctor can ask questions** about that specific patient:
   - "What's this patient's average heart rate?"
   - "Are there any concerning anomalies?"
   - "How is their stress level?"
   - "Should I be worried about their blood pressure?"
   - "Give me an overall health assessment"

## Example Session

```
Select option (1-3): 1
Enter patient access code from QR: PATIENT_Person_3

✓ Access granted for Person_3

Doctor: What's this patient's overall condition?
AI: [Provides analysis specific to Person_3 only]

Doctor: Any concerning anomalies?
AI: [Lists Person_3's specific health issues]

Doctor: new
[Returns to main menu to select another patient]
```

## Features

✅ **Individual patient access** - Each QR code links to one patient
✅ **Privacy focused** - Only selected patient's data is shared with AI
✅ **Professional medical interface** - Designed for doctor-patient consultations
✅ **Contextual chat** - AI remembers conversation within a session
✅ **Multiple consultations** - Type 'new' to switch patients

## QR Code Distribution

The QR codes in `patient_qr_codes/` can be:
- Printed on patient cards
- Sent to patients via email/app
- Embedded in patient wristbands
- Used in hospital management systems

When scanned, the QR code contains the access code (e.g., "PATIENT_Person_1") which the doctor enters into the system.
