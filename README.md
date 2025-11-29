# Aarogya Monorepo

This repository now functions as a single project with two apps that
share the same Supabase backend:

- `Site/` – Vite/React front-end plus Supabase edge functions.
- `Agents/` – Python utilities (QR generator, smartwatch importer,
  doctor chat) that feed and consume the same data.

## Quick start

1. **Supabase env** – Create `config/.env` (or `.env` at the repo root)
   with:
   ```
   SUPABASE_URL=https://<your-project-id>.supabase.co
   SUPABASE_PROJECT_ID=<your-project-id>
   SUPABASE_ANON_KEY=<public-anon-key>
   ```
2. **Frontend (`Site/`)**
   ```powershell
   cd Site
   cp .env.example .env   # create this file with VITE_* vars
   npm install
   npm run dev
   ```
3. **Python agents (`Agents/`)**
   ```powershell
   cd Agents
   pip install -r requirements.txt
   python generate_patient_qr.py
   python smartwatch_health_data_generator.py
   python doctor_chat.py
   ```

## Shared configuration

- `Site/src/utils/supabase/info.tsx` now reads from `import.meta.env`
  so the front-end gets its keys from `Site/.env`.
- `Agents/supabase_client.py` loads the shared `.env` via
  `python-dotenv`, keeping credentials in one place.

Refer to `Site/README.md` and `Agents/README.md` for app-specific
details, deployment steps, and troubleshooting tips.

