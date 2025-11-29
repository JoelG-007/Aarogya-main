"""
Generate QR codes for each patient with their unique data access code
"""

import qrcode
import pandas as pd
import json
import os
from datetime import datetime

from supabase_client import generate_access_code, SupabaseError


def load_patient_id_map(path: str = "patient_id_map.json") -> dict | None:
    """
    Load mapping from logical IDs (e.g. 'Person_1') to Supabase patient IDs.

    Example file structure (patient_id_map.json):
    {
      "Person_1": "supabase-patient-uuid-1",
      "Person_2": "supabase-patient-uuid-2"
    }
    """
    if not os.path.exists(path):
        print(f"No mapping file '{path}' found; generating LOCAL_ONLY demo codes.")
        return None

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            print(f"Mapping file '{path}' is not a JSON object; ignoring.")
            return None
        return data
    except Exception as e:
        print(f"Failed to load '{path}': {e}")
        return None


def generate_patient_qr_codes(
    csv_path: str = "smartwatch_data.csv",
    output_dir: str = "patient_qr_codes",
    patient_id_map: dict | None = None,
):
    """
    Generate QR codes for each logical patient.

    If `patient_id_map` is provided, it should map the local `person_id`
    (e.g. 'Person_1') to a real Supabase `patient.id`. If a mapping exists,
    a fresh Supabase access code is created for that patient and encoded
    in the QR. Otherwise, a QR is still generated but without a Supabase
    access record (local/demo only).
    """

    # Load data
    df = pd.read_csv(csv_path)

    # Create output directory
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    patients = df["person_id"].unique()

    print(f"Generating QR codes for {len(patients)} patients...\n")

    patient_codes: dict[str, dict] = {}

    for person in patients:
        supabase_patient_id = (
            patient_id_map.get(person) if patient_id_map is not None else None
        )

        if supabase_patient_id:
            # Ask Supabase for a real access code
            try:
                result = generate_access_code(supabase_patient_id)
                access_code = result["accessCode"]
                expires_at = result["expiresAt"]
            except SupabaseError as e:
                print(f"[Supabase error] Could not generate code for {person}: {e}")
                access_code = f"{person}_LOCAL_ONLY"
                expires_at = None
        else:
            # Fallback: demo-only code that web app won't recognize
            access_code = f"{person}_LOCAL_ONLY"
            expires_at = None

        # Generate QR code that encodes the access code string
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(access_code)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        filename = f"{output_dir}/{person}_qr_code.png"
        img.save(filename)

        patient_codes[access_code] = {
            "patient_id": person,
            "supabase_patient_id": supabase_patient_id,
            "generated_at": datetime.now().isoformat(),
            "expires_at": expires_at,
        }

        print(f"✓ Generated QR code for {person}: {filename}")
        print(f"  Access Code: {access_code}")
        if expires_at:
            print(f"  Expires at: {expires_at}")
        else:
            print("  Note: LOCAL_ONLY demo code (not registered in Supabase)")


if __name__ == "__main__":
    # Load optional mapping from Person_X to Supabase patient IDs.
    mapping = load_patient_id_map()
    generate_patient_qr_codes(patient_id_map=mapping)
