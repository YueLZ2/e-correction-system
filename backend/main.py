# backend/main.py

from team import analyze_bpmn_flow
from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sys
import os
from pathlib import Path
import logging
import base64
from fastapi.staticfiles import StaticFiles
import aiofiles

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



app = FastAPI()
UPLOAD_DIR = Path("/tmp/uploads")
REPORTS_DIR = Path("static/reports")
# 新增static目录创建
STATIC_DIR = Path("static")
STATIC_DIR.mkdir(exist_ok=True, parents=True)
UPLOAD_DIR.mkdir(exist_ok=True, parents=True)
REPORTS_DIR.mkdir(exist_ok=True, parents=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

class BPMNAnalysisRequest(BaseModel):
    bpmn_path: str
    description: str
    checker_model: str
    text_checker_model: str
    corrector_model: str
    fast_corrector_model: str
# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["Content-Type", "Authorization"]
)

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        # 添加空文件名检查
        if not file.filename:
            raise HTTPException(status_code=400, detail="Missing filename")
            
        file_path = UPLOAD_DIR / file.filename
        
        # 确保上传目录存在
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 使用异步文件写入
        async with aiofiles.open(file_path, "wb") as buffer:
            await buffer.write(await file.read())
            
        # 验证文件是否实际存在
        if not file_path.exists():
            raise HTTPException(status_code=500, detail="File save failed")
        else:
            print(f"File saved to: {file_path.absolute()}")
            
        return {"path": str(file_path.absolute())}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail="File upload failed")

@app.post("/analyze")
async def analyze_bpmn(request: BPMNAnalysisRequest):
    try:
        print("开始分析")
        # Validate file existence
        if not Path(request.bpmn_path).exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        # Run analysis
        result = await analyze_bpmn_flow(
            request.description,
            request.bpmn_path,
            
            agent_configs={
               "checker": request.checker_model,
                "text_checker": request.text_checker_model,
                "corrector": request.corrector_model,
                "fast_corrector": request.fast_corrector_model
            }
        )
         # 确保result.diagram_svg存在有效值
        print("Response Data:", result)  # 查看实际返回内容
        # 返回正确的URL路径
        return {
            "diagram_svg": f"http://localhost:8000/{result.get('diagram_svg', 'static/default_diagram.svg')}",
            "suggestions": result.get("suggestions", []),
            "corrections": result.get("corrections", [])
        }
        # return result
    except FileNotFoundError as e:
        logger.error(f"File not found: {request.bpmn_path}")
        raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Analysis failed")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)