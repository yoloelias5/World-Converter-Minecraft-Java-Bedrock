from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

BRIDGER_BIN = os.getenv("BRIDGER_BIN", "bridger")
MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", str(512 * 1024 * 1024)))
CONVERSION_TIMEOUT = int(os.getenv("CONVERSION_TIMEOUT", "900"))
ALLOWED_ORIGINS = [x.strip() for x in os.getenv("ALLOWED_ORIGINS", "*").split(",") if x.strip()]

app = FastAPI(title="WorldBridge API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS if ALLOWED_ORIGINS != ["*"] else ["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
    expose_headers=["X-WorldBridge-Report"],
)


def find_java_world(root: Path) -> Path:
    candidates = [root] + [p for p in root.rglob("level.dat") if p.is_file()]
    for candidate in candidates:
        world_dir = candidate.parent if candidate.name == "level.dat" else candidate
        if (world_dir / "level.dat").is_file() and (world_dir / "region").is_dir():
            return world_dir
    raise HTTPException(
        status_code=400,
        detail="No Java world found. ZIP the world folder that contains level.dat and region/.",
    )


def safe_extract(archive: Path, destination: Path) -> None:
    root = destination.resolve()
    with zipfile.ZipFile(archive) as zf:
        entries = zf.infolist()
        if len(entries) > 20000:
            raise HTTPException(status_code=413, detail="The ZIP contains too many files.")
        expanded_size = 0
        for item in entries:
            target = (destination / item.filename).resolve()
            if target != root and root not in target.parents:
                raise HTTPException(status_code=400, detail="The ZIP contains an unsafe file path.")
            expanded_size += item.file_size
            if expanded_size > MAX_UPLOAD_BYTES:
                raise HTTPException(status_code=413, detail="The extracted world exceeds the 512 MB limit.")
        zf.extractall(destination)


@app.get("/health")
def health():
    ready = shutil.which(BRIDGER_BIN) is not None or Path(BRIDGER_BIN).is_file()
    return {"ok": True, "converter_ready": ready, "engine": "Bridger CLI"}


@app.post("/convert/java-to-bedrock")
async def convert_java_to_bedrock(world: UploadFile = File(...)):
    filename = world.filename or "java-world.zip"
    if not filename.lower().endswith(".zip"):
        raise HTTPException(status_code=400, detail="Upload a ZIP file containing your Java world.")

    with tempfile.TemporaryDirectory(prefix="worldbridge-") as temp:
        work = Path(temp)
        archive = work / "upload.zip"
        extracted = work / "input"
        extracted.mkdir()
        total = 0
        try:
            with archive.open("wb") as output:
                while chunk := await world.read(1024 * 1024):
                    total += len(chunk)
                    if total > MAX_UPLOAD_BYTES:
                        raise HTTPException(status_code=413, detail="World ZIP exceeds the 512 MB upload limit.")
                    output.write(chunk)
        finally:
            await world.close()

        try:
            safe_extract(archive, extracted)
        except zipfile.BadZipFile:
            raise HTTPException(status_code=400, detail="That file is not a valid ZIP archive.")

        input_world = find_java_world(extracted)
        output_world = work / "converted.mcworld"
        report_file = work / "conversion-report.json"
        command = [
            BRIDGER_BIN, "convert", str(input_world), str(output_world),
            "--report", str(report_file), "--entities", "all",
        ]
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=CONVERSION_TIMEOUT,
                check=False,
            )
        except FileNotFoundError:
            raise HTTPException(status_code=503, detail="Bridger CLI is not installed on the conversion server.")
        except subprocess.TimeoutExpired:
            raise HTTPException(status_code=408, detail="Conversion timed out. Try a smaller world.")

        if result.returncode != 0 or not output_world.is_file():
            detail = (result.stderr or result.stdout or "The conversion engine could not convert this world.")[-3000:]
            raise HTTPException(status_code=422, detail=detail)

        report_summary = "Conversion completed."
        if report_file.is_file():
            try:
                report = json.loads(report_file.read_text(encoding="utf-8"))
                report_summary = json.dumps(report, separators=(",", ":"))[:6000]
            except (OSError, json.JSONDecodeError):
                pass

        safe_name = Path(filename).stem[:70] or "world"
        # FileResponse reads the file after this function returns; copy it outside
        # TemporaryDirectory and remove it only after the response has completed.
        final_dir = Path(tempfile.mkdtemp(prefix="worldbridge-download-"))
        final_file = final_dir / f"{safe_name}-Bedrock.mcworld"
        shutil.copy2(output_world, final_file)

    def cleanup():
        shutil.rmtree(final_dir, ignore_errors=True)

    return FileResponse(
        final_file,
        media_type="application/octet-stream",
        filename=final_file.name,
        headers={"X-WorldBridge-Report": report_summary},
        background=BackgroundTask(cleanup),
    )
