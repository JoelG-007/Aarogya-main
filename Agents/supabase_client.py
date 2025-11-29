"""
Shared Supabase HTTP client for Python agents.

Agents can now access the same Supabase backend as the web app by
providing SUPABASE_URL and SUPABASE_ANON_KEY via environment variables
or a `.env` file at the repo root (loaded with python-dotenv).
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional

import requests

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional dependency
    load_dotenv = None


def _load_env_file() -> None:
    """Best-effort load of a shared .env file."""
    if not load_dotenv:
        return

    # Look for .env at repo root or config/.env
    agents_dir = Path(__file__).resolve().parent
    repo_root = agents_dir.parent
    candidate_files = [
        repo_root / ".env",
        repo_root / "config" / ".env",
        repo_root / "config" / ".env.local",
    ]
    for env_file in candidate_files:
        if env_file.exists():
            load_dotenv(dotenv_path=env_file, override=False)
            break


_load_env_file()

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://rjspcbrdxepjcwuiwaln.supabase.co")
SUPABASE_ANON_KEY = os.getenv(
    "SUPABASE_ANON_KEY",
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJqc3BjYnJkeGVwamN3dWl3YWxuIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQzMzQ5NjksImV4cCI6MjA3OTkxMDk2OX0.ANadVgWIVNrY6k00A7f_-YF8TiusqA56NHlv4MTKmP8",
)

FUNCTION_BASE = f"{SUPABASE_URL}/functions/v1/make-server-51edddfe"


class SupabaseError(Exception):
    """Custom error for Supabase HTTP calls."""


def _headers() -> Dict[str, str]:
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        raise SupabaseError(
            "SUPABASE_URL or SUPABASE_ANON_KEY not configured. "
            "Create a .env file or export env vars before running agents."
        )
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
    }


def _request(
    method: str, path: str, json: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    url = FUNCTION_BASE + path
    resp = requests.request(method, url, headers=_headers(), json=json, timeout=15)
    try:
        data = resp.json()
    except Exception:
        data = {"success": False, "error": f"Non-JSON response: {resp.text}"}
    if not resp.ok or not data.get("success", False):
        raise SupabaseError(data.get("error") or f"HTTP {resp.status_code}")
    return data


def post_health_reading(patient_id: str, reading: Dict[str, Any]) -> Dict[str, Any]:
    """
    Push a smartwatch health reading into Supabase so it shows up
    in the web dashboards.
    """
    # Only send fields the server expects
    payload = {
        "timestamp": reading.get("timestamp"),
        "heart_rate": reading.get("heart_rate"),
        "spo2": reading.get("spo2"),
        "temperature": reading.get("temperature"),
        "systolic_bp": reading.get("systolic_bp"),
        "diastolic_bp": reading.get("diastolic_bp"),
        "steps": reading.get("steps"),
        "stress_level": reading.get("stress_level"),
        "sleep_hours": reading.get("sleep_hours"),
    }
    return _request("POST", f"/patient/{patient_id}/health-data", json=payload)


def generate_access_code(patient_id: str) -> Dict[str, Any]:
    """
    Request a fresh access code for a patient from Supabase.

    Returns dict with:
    - accessCode
    - expiresAt
    """
    return _request("POST", f"/patient/{patient_id}/generate-code")


def verify_access_code(doctor_id: str, access_code: str) -> Dict[str, Any]:
    """
    Verify an access code for a doctor and get minimal patient info.

    Returns dict with:
    - patient: { id, name, age, gender, blood_group }
    """
    body = {"doctor_id": doctor_id, "access_code": access_code}
    return _request("POST", "/doctor/verify-code", json=body)


def get_patient_health_data(patient_id: str, limit: int = 100) -> Dict[str, Any]:
    """
    Fetch recent health data for a patient.
    """
    return _request("GET", f"/patient/{patient_id}/health-data?limit={limit}")


def get_patient_profile(patient_id: str) -> Dict[str, Any]:
    """
    Fetch basic patient profile (demographics).
    """
    return _request("GET", f"/patient/{patient_id}")


