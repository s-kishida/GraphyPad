import os
import sys
from pathlib import Path

# --- VERCEL CRITICAL SETUP ---
os.environ['MPLCONFIGDIR'] = '/tmp/matplotlib'

import io
import json
import base64
from typing import Optional

try:
    import pandas as pd
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
except Exception as e:
    print(f"Startup error: {e}")

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

app = FastAPI()

# 正確なパス解決
BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"
UPLOAD_DIR = Path("/tmp/uploads")

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

def read_csv_with_fallback(file_path):
    try:
        return pd.read_csv(file_path)
    except:
        return pd.read_csv(file_path, encoding='shift-jis')

@app.get("/", response_class=HTMLResponse)
async def read_index():
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return index_file.read_text(encoding="utf-8")
    return HTMLResponse(content="<h1>Server is running, but static files are missing.</h1>", status_code=200)

@app.post("/upload")
async def upload_csv(file: UploadFile = File(...)):
    if not UPLOAD_DIR.exists(): UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
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
    # ... 他のパラメータ
    title: Optional[str] = Form(""),
    width: float = Form(10.0), height: float = Form(6.0)
):
    # 日本語ライブラリを「ここ」でだけ呼ぶ
    try:
        import japanize_matplotlib
    except:
        pass

    file_path = UPLOAD_DIR / filename
    if not file_path.exists(): raise HTTPException(status_code=404, detail="File not found")
    
    try:
        df = read_csv_with_fallback(file_path)
        plt.figure(figsize=(width, height), facecolor='white')
        plt.plot(df[x_axis], df[json.loads(y_axis_list)[0]], marker='o')
        plt.title(title)
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=100)
        plt.close()
        buf.seek(0)
        return {"image": f"data:image/png;base64,{base64.b64encode(buf.read()).decode('utf-8')}"}
    except Exception as e:
        plt.close()
        raise HTTPException(status_code=500, detail=str(e))
