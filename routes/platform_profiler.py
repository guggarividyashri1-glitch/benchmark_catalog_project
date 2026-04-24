from fastapi import APIRouter, UploadFile, File, HTTPException
import zipfile, os, shutil, json
from datetime import datetime
from config.database import benchmark_collection
from utils.response import success, failed 
router = APIRouter(prefix="/platform_provider", tags=["Platform Provider"])

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
@router.post("/upload")
async def upload_zip(file: UploadFile = File(...)):
    try:
        if not file.filename.endswith(".zip"):
            raise HTTPException(status_code=400, detail="Only ZIP allowed")

        benchmark_name = file.filename.replace(".zip", "")

        zip_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(zip_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        extract_path = os.path.join(UPLOAD_DIR, benchmark_name)
        os.makedirs(extract_path, exist_ok=True)

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_path)

        validate_structure(extract_path)

        platform_path = os.path.join(
            extract_path, "platform_profiler", "platform_profiler.json"
        )
        with open(platform_path) as f:
            platform_data = json.load(f)

        validate_platform_fields(platform_data)

        workload_path = os.path.join(
            extract_path, "workload_profiler", "workload_profiler.json"
        )
        results_path = os.path.join(extract_path, "resultsfolder")
        log_file = [f for f in os.listdir(results_path) if f.endswith(".log")][0]
        log_path = os.path.join(results_path, log_file)

        with open(log_path) as f:
            log_content = f.read()
        metric_info = {}
        for line in log_content.splitlines():
            if "=" in line:
                key, value = line.split("=")
                metric_info[key.strip()] = int(value.strip())

        document = {
            "benchmark_name": benchmark_name,
            "platform_profiler": platform_data,
            "workload_profiler": {
                "file_path": workload_path
            },
            "result_info": {
                "metric_info": metric_info
            },
            "created_at": datetime.utcnow()
        }

        benchmark_collection.insert_one(document)

        return success(
            message="ZIP processed successfully",
            data={"benchmark_name": benchmark_name},
            code=200
        )
    except zipfile.BadZipFile:
        return failed(message="Invalid ZIP file", code=400)

    except Exception as e:
        return failed(message=str(e), code=500)
def validate_structure(base_path):
    required = [
        "platform_profiler/platform_profiler.json",
        "platform_profiler/platform_profiler.html",
        "workload_profiler/workload_profiler.json",
        "workload_profiler/workload_profiler.html",
        "resultsfolder"
    ]

    for path in required:
        if not os.path.exists(os.path.join(base_path, path)):
            raise HTTPException(status_code=400, detail=f"Missing {path}")

    results_path = os.path.join(base_path, "resultsfolder")
    logs = [f for f in os.listdir(results_path) if f.endswith(".log")]

    if not logs:
        raise HTTPException(status_code=400, detail="No log file found")
    
def validate_platform_fields(platform_data):
    required_fields = ["bios", "cpu_usage", "os", "manufacturer"]

    missing_fields = [
        field for field in required_fields 
        if field not in platform_data or not platform_data[field]
    ]

    if missing_fields:
        raise ValueError(
            f"Missing fields in platform_profiler.json: {', '.join(missing_fields)}"
        )