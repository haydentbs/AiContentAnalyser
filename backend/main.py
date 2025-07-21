
import sys
sys.path.append('..')

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, Any, Generic, TypeVar
import os

from core.config.settings import load_app_config, save_app_config
from core.config.models import AppConfig, EvaluationResult, UpdateSettingsRequest, TestConnectionRequest, Sample
from core.storage.guidelines import load_guidelines
from core.storage.reports import ReportStorage
from core.storage.samples import SampleStorage
from core.agents.llm_client import create_llm_client
from core.agents.coordinator_agent import CoordinatorAgent

app = FastAPI()

T = TypeVar('T')

class ApiResponse(BaseModel, Generic[T]):
    success: bool
    data: Optional[T] = None
    error: Optional[str] = None
    message: Optional[str] = None

class EvaluationRequest(BaseModel):
    content: str
    llm: Optional[dict] = None  # Optional LLM configuration for this evaluation

@app.post("/api/evaluate", response_model=ApiResponse[EvaluationResult])
async def evaluate_content(request: EvaluationRequest):
    try:
        config = load_app_config("config.toml")
        guidelines = load_guidelines(config.guidelines_path)
        
        # Use custom LLM config if provided, otherwise use default config
        if request.llm:
            from core.config.models import LLMConfig
            llm_config = LLMConfig(**request.llm)
            llm_client = create_llm_client(llm_config)
        else:
            llm_client = create_llm_client(config.llm)
            
        coordinator = CoordinatorAgent(llm_client)

        result = await coordinator.evaluate_content(request.content, guidelines)
        
        # Save report to file system
        report_storage = ReportStorage(config.reports_dir)
        report_storage.save_all_formats(result)

        return ApiResponse(success=True, data=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/reports/{report_id}", response_model=ApiResponse[EvaluationResult])
async def get_report(report_id: str):
    try:
        config = load_app_config("config.toml")
        report_storage = ReportStorage(config.reports_dir)
        
        # Try to find the report by content hash
        report = report_storage.load_report_by_content_hash(report_id)
        if not report:
            raise HTTPException(status_code=404, detail=f"Report file not found: {report_id}")
        return ApiResponse(success=True, data=report)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Report file not found: {report_id}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/reports/{report_id}/export")
async def export_report(report_id: str, format: str):
    try:
        config = load_app_config("config.toml")
        report_storage = ReportStorage(config.reports_dir)
        
        if format == "json":
            file_path = report_storage.get_report_path(report_id, "json")
            if not file_path or not os.path.exists(file_path):
                raise HTTPException(status_code=404, detail="JSON report not found")
            return FileResponse(file_path, media_type="application/json", filename=f"{report_id}.json")
        elif format == "markdown":
            file_path = report_storage.get_report_path(report_id, "md")
            if not file_path or not os.path.exists(file_path):
                raise HTTPException(status_code=404, detail="Markdown report not found")
            return FileResponse(file_path, media_type="text/markdown", filename=f"{report_id}.md")
        else:
            raise HTTPException(status_code=400, detail="Invalid export format. Supported formats: json, markdown")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/settings", response_model=ApiResponse[AppConfig])
async def get_settings():
    try:
        config = load_app_config("config.toml")
        return ApiResponse(success=True, data=config)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/settings", response_model=ApiResponse[AppConfig])
async def update_settings(settings: UpdateSettingsRequest):
    try:
        config = load_app_config("config.toml")
        config.llm = settings.llm
        save_app_config(config, "config.toml")
        return ApiResponse(success=True, data=config)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/settings/test", response_model=ApiResponse[Any])
async def test_connection(request: TestConnectionRequest):
    try:
        llm_client = create_llm_client(request.llm)
        result = await llm_client.test_connection()
        return ApiResponse(success=True, data=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/samples", response_model=ApiResponse[List[Sample]])
async def get_all_samples():
    try:
        sample_storage = SampleStorage()
        samples = sample_storage.get_all_samples()
        return ApiResponse(success=True, data=samples)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/samples/{sample_id}", response_model=ApiResponse[Sample])
async def get_sample(sample_id: str):
    try:
        sample_storage = SampleStorage()
        sample = sample_storage.get_sample_by_id(sample_id)
        if not sample:
            raise HTTPException(status_code=404, detail="Sample not found")
        return ApiResponse(success=True, data=sample)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api")
def read_root():
    return {"message": "Content Scorecard API is running"}
