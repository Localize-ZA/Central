# Data Generator

A small Python utility to generate mock payment messages and optionally send them via HTTP.

## Features
- Generate payload types:
   - `c2b`: Citizen-to-Business purchase event (simple dict)
   - `iso8583`: Simplified ISO 8583-like JSON
   - `iso20022`: Simplified ISO 20022 pain.001-like JSON
   - `CitizenToBusiness`: Pydantic-model JSON for CitizenToBusiness
   - `BusinessToBusiness`: Pydantic-model JSON for BusinessToBusiness
   - `random`: Randomly chooses one of the legacy three each iteration (iso8583/iso20022/c2b)
- Send to `MOCK_DATA_URL` from `.env`, or print with `--dry-run`
- Runs indefinitely until KeyboardInterrupt (Ctrl+C) or use `--count` for a finite number
- Control interval between messages

## Setup

1. Create a virtual environment (optional but recommended)

   PowerShell (Windows):
   ```powershell
   python -m venv .venv; . .venv\Scripts\Activate.ps1
   ```

2. Install dependencies
   ```powershell
   pip install -r requirements.txt
   ```

3. Configure environment
   ```powershell
   Copy-Item .env.example .env
   # Edit .env and set MOCK_DATA_URL
   ```

## Usage

From the `01_Data_Gen` folder:

```powershell
# Print random payloads continuously (omit --format to use mod-3 selection)
python .\main.py --dry-run --pretty

# Send ISO8583-like messages, 0.5s apart, until Ctrl+C
python .\main.py --format iso8583 -i 0.5

# Send ISO20022 messages without pretty printing
python .\main.py --format iso20022

# Generate JSON using Pydantic models
python .\main.py --format CitizenToBusiness --dry-run --count 3
python .\main.py --format BusinessToBusiness --dry-run --pretty --count 2

Behavior when --format is omitted:
- The script generates a random number and uses `number % 3` to decide:
   - 0 => iso8583
   - 1 => iso20022
   - 2 => c2b

Tips:
- `--dry-run` can also be written as `--dry_run`.
- Use `--count N` (or `-n N`) to send exactly N messages and exit.

Press Ctrl+C to stop at any time.
```

If `MOCK_DATA_URL` is not set, the script will skip sending and print a message.
