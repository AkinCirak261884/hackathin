"""Vercel entry point for the API (see vercel.json). Locally keep using `uvicorn api.main:app`."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # repo root, so `api` and `analysis` import

from api.main import app  # noqa: E402,F401
