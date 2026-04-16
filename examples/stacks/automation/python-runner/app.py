from __future__ import annotations

from pathlib import Path
from typing import List, Optional
import subprocess

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field


SCRIPTS_DIR = Path("/scripts")


class RunRequest(BaseModel):
    script: str = Field(..., description="Script filename in /scripts")
    args: List[str] = Field(default_factory=list)
    stdin: Optional[str] = None
    timeout_sec: int = 120


class RunResponse(BaseModel):
    returncode: int
    stdout: str
    stderr: str


app = FastAPI()


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/run", response_model=RunResponse)
def run_script(req: RunRequest) -> RunResponse:
    if "/" in req.script or ".." in req.script:
        raise HTTPException(status_code=400, detail="Invalid script path")

    script_path = (SCRIPTS_DIR / req.script).resolve()
    if not script_path.exists() or script_path.is_dir():
        raise HTTPException(status_code=404, detail="Script not found")

    try:
        # NOTE: req.args are passed directly to the subprocess.
        # This service is intended for trusted LAN use only.
        result = subprocess.run(
            ["python3", str(script_path), *req.args],
            input=req.stdin,
            text=True,
            capture_output=True,
            timeout=req.timeout_sec,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise HTTPException(status_code=504, detail=f"Timeout after {exc.timeout}s")

    return RunResponse(
        returncode=result.returncode,
        stdout=result.stdout,
        stderr=result.stderr,
    )
