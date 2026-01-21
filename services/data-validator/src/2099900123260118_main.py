# doc_id: DOC-SERVICE-0131
# DOC_ID: DOC-SERVICE-0049
"""
Data Validator Service

Main FastAPI service for comprehensive data pipeline validation,
schema verification, and data quality monitoring.
"""

import asyncio
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path

import structlog
from fastapi import FastAPI, HTTPException, File, UploadFile
from pydantic import BaseModel

from .config import Settings
from .validator import DataValidator, ValidationStatus
from .metrics import MetricsCollector
from .health import HealthChecker

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer() if __debug__ else structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


class DataValidationRequest(BaseModel):
    """Request to validate data."""
    
    data: Dict[str, Any]
    schema: str
    data_source: Optional[str] = None


class SchemaValidationRequest(BaseModel):
    """Request to validate data against specific schema."""
    
    data: Dict[str, Any]
    schema: str


class PipelineValidationRequest(BaseModel):
    """Request to validate pipeline data flow."""
    
    pipeline_name: str
    input_data: Dict[str, Any]
    output_data: Dict[str, Any]
    processing_time_ms: Optional[float] = None


class DataValidatorService:
    """Core data validator service."""
    
    def __init__(self, settings: Settings, metrics: MetricsCollector, health_checker: HealthChecker):
        self.settings = settings
        self.metrics = metrics
        self.health_checker = health_checker
        
        self.validator = DataValidator(settings, metrics)
        
        self.running = False
    
    async def start(self) -> None:
        """Start the data validator service."""
        if self.running:
            return
        
        logger.info("Starting Data Validator Service", port=self.settings.service_port)
        
        # Start validator
        await self.validator.start()
        
        self.running = True
        self.metrics.increment_counter("service_starts")
        
        logger.info("Data Validator Service started successfully")
    
    async def stop(self) -> None:
        """Stop the data validator service."""
        if not self.running:
            return
        
        logger.info("Stopping Data Validator Service")
        
        # Stop validator
        await self.validator.stop()
        
        self.running = False
        logger.info("Data Validator Service stopped")
    
    async def validate_data(self, data: Dict[str, Any], schema: str, 
                           data_source: Optional[str] = None) -> Dict[str, Any]:
        """Validate data and return results."""
        report = await self.validator.validate_data(data, schema, data_source)
        return report.to_dict()
    
    async def validate_csv_file(self, file_path: Path) -> Dict[str, Any]:
        """Validate CSV file."""
        report = await self.validator.validate_csv_file(file_path)
        return report.to_dict()
    
    async def get_validation_reports(self, limit: int = 100, schema: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get validation reports."""
        return await self.validator.get_validation_reports(limit, schema)
    
    async def get_validation_summary(self) -> Dict[str, Any]:
        """Get validation summary."""
        return await self.validator.get_validation_summary()
    
    async def get_validator_status(self) -> Dict[str, Any]:
        """Get comprehensive validator status."""
        validator_status = await self.validator.get_status()
        validation_summary = await self.get_validation_summary()
        
        return {
            "service": "data-validator",
            "running": self.running,
            "validator": validator_status,
            "validation_summary": validation_summary,
            "configuration": {
                "schemas_monitored": len(self.settings.validation_rules),
                "pipelines_monitored": len(self.settings.pipeline_validation_rules),
                "data_sources_monitored": len(self.settings.monitored_data_sources)
            }
        }


# Global service instance
service_instance: Optional[DataValidatorService] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage service lifecycle."""
    global service_instance
    
    # Startup
    settings = Settings()
    metrics = MetricsCollector()
    health_checker = HealthChecker(settings, metrics)
    
    service_instance = DataValidatorService(settings, metrics, health_checker)
    
    try:
        await service_instance.start()
        yield
    finally:
        # Shutdown
        if service_instance:
            await service_instance.stop()


# Create FastAPI application
app = FastAPI(
    title="Data Validator Service",
    description="Comprehensive data pipeline validation and quality monitoring",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/healthz")
async def health_check():
    """Liveness probe endpoint."""
    if not service_instance or not service_instance.running:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    return {"status": "healthy", "service": "data-validator"}


@app.get("/readyz")
async def readiness_check():
    """Readiness probe endpoint."""
    if not service_instance:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    health_status = await service_instance.health_checker.get_health_status()
    
    if health_status["overall_status"] != "healthy":
        raise HTTPException(status_code=503, detail="Service not ready")
    
    return health_status


@app.get("/metrics")
async def get_metrics():
    """Prometheus metrics endpoint."""
    if not service_instance:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    return service_instance.metrics.get_metrics_summary()


@app.get("/validator/status")
async def get_validator_status():
    """Get comprehensive validator status."""
    if not service_instance:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    return await service_instance.get_validator_status()


@app.post("/validate/data")
async def validate_data(request: DataValidationRequest):
    """Validate data against schema and quality rules."""
    if not service_instance:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        result = await service_instance.validate_data(
            request.data,
            request.schema,
            request.data_source
        )
        return result
        
    except Exception as e:
        logger.error("Data validation failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")


@app.post("/validate/schema")
async def validate_schema(request: SchemaValidationRequest):
    """Validate data against schema rules only."""
    if not service_instance:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        # Create a temporary settings with only schema validation enabled
        temp_settings = service_instance.settings
        original_quality = temp_settings.data_quality_checks_enabled
        
        temp_settings.data_quality_checks_enabled = False
        
        result = await service_instance.validate_data(request.data, request.schema)
        
        # Restore original settings
        temp_settings.data_quality_checks_enabled = original_quality
        
        return result
        
    except Exception as e:
        logger.error("Schema validation failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Schema validation failed: {str(e)}")


@app.post("/validate/csv")
async def validate_csv_upload(file: UploadFile = File(...)):
    """Validate uploaded CSV file."""
    if not service_instance:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    if not file.filename or not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV file")
    
    try:
        # Save uploaded file temporarily
        output_dir = service_instance.settings.get_output_path()
        output_dir.mkdir(parents=True, exist_ok=True)
        
        temp_file_path = output_dir / f"temp_{file.filename}"
        
        with open(temp_file_path, 'wb') as f:
            content = await file.read()
            f.write(content)
        
        # Validate the CSV file
        result = await service_instance.validate_csv_file(temp_file_path)
        
        # Clean up temporary file
        temp_file_path.unlink()
        
        return result
        
    except Exception as e:
        logger.error("CSV validation failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"CSV validation failed: {str(e)}")


@app.get("/validation/reports")
async def get_validation_reports(limit: int = 100, schema: Optional[str] = None):
    """Get validation reports."""
    if not service_instance:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    if limit <= 0 or limit > 1000:
        raise HTTPException(status_code=400, detail="Limit must be between 1 and 1000")
    
    return await service_instance.get_validation_reports(limit, schema)


@app.get("/validation/summary")
async def get_validation_summary():
    """Get validation summary statistics."""
    if not service_instance:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    return await service_instance.get_validation_summary()


@app.get("/validation/rules")
async def get_validation_rules():
    """Get all validation rules configuration."""
    if not service_instance:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    return {
        "validation_rules": service_instance.settings.validation_rules,
        "pipeline_validation_rules": service_instance.settings.pipeline_validation_rules
    }


@app.get("/validation/rules/{schema}")
async def get_schema_validation_rules(schema: str):
    """Get validation rules for a specific schema."""
    if not service_instance:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    rules = service_instance.settings.get_validation_rules(schema)
    if not rules:
        raise HTTPException(status_code=404, detail=f"No validation rules found for schema: {schema}")
    
    return {"schema": schema, "rules": rules}


@app.get("/validation/schemas")
async def get_monitored_schemas():
    """Get all monitored schemas."""
    if not service_instance:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    schemas = service_instance.settings.get_all_monitored_schemas()
    
    return {
        "monitored_schemas": list(schemas),
        "total_schemas": len(schemas),
        "data_sources": service_instance.settings.monitored_data_sources
    }


@app.get("/validation/data-sources")
async def get_data_sources():
    """Get monitored data sources configuration."""
    if not service_instance:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    return service_instance.settings.monitored_data_sources


@app.get("/validation/pipelines")
async def get_pipeline_validation_rules():
    """Get pipeline validation rules."""
    if not service_instance:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    return service_instance.settings.pipeline_validation_rules


@app.get("/dashboard")
async def get_validator_dashboard():
    """Get validator dashboard data."""
    if not service_instance:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    status = await service_instance.get_validator_status()
    recent_reports = await service_instance.get_validation_reports(20)
    validation_summary = await service_instance.get_validation_summary()
    
    # Calculate quality trends
    quality_scores = [r.get("quality_score", 0) for r in recent_reports[-10:]]
    avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
    
    return {
        "dashboard": {
            "timestamp": datetime.utcnow().isoformat(),
            "status": status,
            "recent_validations": recent_reports[:10],
            "validation_summary": validation_summary,
            "quality_trend": {
                "average_quality_score": avg_quality,
                "recent_quality_scores": quality_scores
            },
            "configuration": {
                "total_validation_rules": len(service_instance.settings.validation_rules),
                "total_pipeline_rules": len(service_instance.settings.pipeline_validation_rules),
                "monitored_data_sources": len(service_instance.settings.monitored_data_sources),
                "validation_features": {
                    "schema_validation": service_instance.settings.schema_validation_enabled,
                    "data_quality_checks": service_instance.settings.data_quality_checks_enabled,
                    "pipeline_validation": service_instance.settings.pipeline_validation_enabled,
                    "anomaly_detection": service_instance.settings.anomaly_detection_enabled,
                    "csv_validation": service_instance.settings.csv_validation_enabled
                }
            }
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    settings = Settings()
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=settings.service_port,
        log_level=settings.log_level.lower(),
        reload=settings.debug_mode
    )