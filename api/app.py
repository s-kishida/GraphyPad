import os
import sys

# DEPLOYMENT_VERSION: 1.0.2
print("Initializing GraphyPad on Vercel...")

# 1. Matplotlib setup (must be before any other mpl imports)
os.environ['MPLCONFIGDIR'] = '/tmp/matplotlib'

import io
import json
import base64
from pathlib import Path
from typing import Optional

try:
    import pandas as pd
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    try:
        import japanize_matplotlib
    except:
        pass
except Exception as e:
    print(f"Base Library Import Error: {e}")

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

app = FastAPI()

# Path settings
BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"
UPLOAD_DIR = Path("/tmp/uploads")

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

def read_csv_with_fallback(file_path):
    try:
        return pd.read_csv(file_path)
    except Exception:
        return pd.read_csv(file_path, encoding='shift-jis')

def ensure_upload_dir():
    if not UPLOAD_DIR.exists():
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@app.get("/", response_class=HTMLResponse)
async def read_index():
    index_file = STATIC_DIR / "index.html"
    if not index_file.exists():
        return HTMLResponse(content=f"<h1>Error: Static files not found at {STATIC_DIR}</h1>", status_code=404)
    return index_file.read_text(encoding="utf-8")

@app.post("/upload")
async def upload_csv(file: UploadFile = File(...)):
    ensure_upload_dir()
    file_path = UPLOAD_DIR / file.filename
    with open(file_path, "wb") as f:
        f.write(await file.read())
    try:
        df = read_csv_with_fallback(file_path)
        return {"filename": file.filename, "columns": df.columns.tolist()}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/generate")
async def generate_graph(
    filename: str = Form(...),
    x_axis: str = Form(...),
    y_axis_list: str = Form(...),
    x_name: Optional[str] = Form(""),
    x_unit: Optional[str] = Form(""),
    y_name: Optional[str] = Form(""),
    y_unit: Optional[str] = Form(""),
    title: Optional[str] = Form(""),
    width: float = Form(10.0),
    height: float = Form(6.0),
    font_title: int = Form(24),
    font_label: int = Form(18),
    font_tick: int = Form(16),
    marker_size: float = Form(8.0),
    line_width: float = Form(3.0),
    x_min: Optional[float] = Form(None),
    x_max: Optional[float] = Form(None)
):
    file_path = UPLOAD_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        df = read_csv_with_fallback(file_path)
        y_cols = json.loads(y_axis_list)
        
        plt.figure(figsize=(width, height), facecolor='white')
        ax = plt.axes()
        for col in y_cols:
            plt.plot(df[x_axis], df[col], marker='o', linewidth=line_width, markersize=marker_size, label=col)
        
        def format_label(name, unit, default):
            if not name and not unit: return default
            if name and unit: return f"{name} ({unit})"
            return name if name else f"({unit})"

        plt.xlabel(format_label(x_name, x_unit, x_axis), fontsize=font_label)
        plt.ylabel(format_label(y_name, y_unit, y_cols[0] if len(y_cols)==1 else ""), fontsize=font_label)
        plt.title(title if title else "Graph", fontsize=font_title)
        if len(y_cols) > 1: plt.legend()
        ax.tick_params(labelsize=font_tick)
        if x_min is not None and x_max is not None: plt.xlim(x_min, x_max)
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=100)
        plt.close()
        buf.seek(0)
        img_str = base64.b64encode(buf.read()).decode('utf-8')
        
        return {"image": f"data:image/png;base64,{img_str}", "code": "# Preview code will be here"}
    except Exception as e:
        plt.close()
        raise HTTPException(status_code=500, detail=str(e))
