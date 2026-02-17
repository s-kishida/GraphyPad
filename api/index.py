import os
import sys

# --- Vercel環境用の特殊設定 ---
# 1. Matplotlibの書き込み先を/tmpに指定（必須）
# インポートより先に設定する必要がある
os.environ['MPLCONFIGDIR'] = '/tmp/matplotlib'

import io
import json
import base64
from pathlib import Path
from typing import Optional

try:
    import pandas as pd
    import matplotlib
    # 2. 画面がない環境で動くように設定（必須）
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    
    # 3. 日本語対応
    import japanize_matplotlib
except Exception as e:
    print(f"Startup Import Error: {str(e)}")
    # クラッシュさせずに続行を試みる（または後のエラーで詳細を出す）

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

app = FastAPI()

# パスの設定
# api/index.py から見て親ディレクトリがルート
BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"
UPLOAD_DIR = Path("/tmp/uploads")

# 静的ファイルの提供（フォルダが存在する場合のみ）
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

def read_csv_with_fallback(file_path):
    try:
        return pd.read_csv(file_path)
    except UnicodeDecodeError:
        return pd.read_csv(file_path, encoding='shift-jis')

def ensure_upload_dir():
    if not UPLOAD_DIR.exists():
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@app.get("/", response_class=HTMLResponse)
async def read_index():
    index_file = STATIC_DIR / "index.html"
    if not index_file.exists():
        return HTMLResponse(content="<h1>Error: static/index.html not found</h1>", status_code=404)
    return index_file.read_text(encoding="utf-8")

@app.post("/upload")
async def upload_csv(file: UploadFile = File(...)):
    if not file.filename.lower().endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed.")
    
    ensure_upload_dir()
    file_path = UPLOAD_DIR / file.filename
    with open(file_path, "wb") as f:
        f.write(await file.read())
    
    try:
        df = read_csv_with_fallback(file_path)
        return {"filename": file.filename, "columns": df.columns.tolist()}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading CSV: {str(e)}")

@app.post("/calculate")
async def calculate_column(
    filename: str = Form(...),
    new_col: str = Form(...),
    col_a: str = Form(...),
    factor: float = Form(...)
):
    file_path = UPLOAD_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        df = read_csv_with_fallback(file_path)
        df[new_col] = df[col_a] * factor
        df.to_csv(file_path, index=False)
        return {"columns": df.columns.tolist()}
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
    x_min: Optional[float] = Form(None),
    x_max: Optional[float] = Form(None),
    x_step: Optional[float] = Form(None),
    width: float = Form(10.0),
    height: float = Form(6.0),
    font_title: int = Form(24),
    font_label: int = Form(18),
    font_tick: int = Form(16),
    marker_size: float = Form(8.0),
    line_width: float = Form(3.0)
):
    file_path = UPLOAD_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        df = read_csv_with_fallback(file_path)
        y_cols = json.loads(y_axis_list)
        
        plt.figure(figsize=(width, height), facecolor='white')
        ax = plt.axes()
        ax.set_facecolor('white')
        
        for col in y_cols:
            plt.plot(df[x_axis], df[col], marker='o', linewidth=line_width, markersize=marker_size, label=col)
        
        def format_label(name, unit, default):
            if not name and not unit: return default
            if name and unit: return f"{name} ({unit})"
            return name if name else f"({unit})"

        x_label_final = format_label(x_name, x_unit, x_axis)
        y_label_final = format_label(y_name, y_unit, y_cols[0] if len(y_cols) == 1 else "")

        plt.xlabel(x_label_final, color='black', fontsize=font_label)
        plt.ylabel(y_label_final, color='black', fontsize=font_label)
        plt.title(title if title else (f"{y_cols[0]} vs {x_axis}" if len(y_cols) == 1 else "複数データの比較"), color='black', fontsize=font_title, pad=20)
        
        if len(y_cols) > 1:
            plt.legend()

        ax.spines['bottom'].set_color('black')
        ax.spines['top'].set_color('black')
        ax.spines['left'].set_color('black')
        ax.spines['right'].set_color('black')
        ax.tick_params(axis='x', colors='black', labelsize=font_tick)
        ax.tick_params(axis='y', colors='black', labelsize=font_tick)
        plt.grid(True, linestyle='--', alpha=0.3, color='gray')
        
        if x_min is not None and x_max is not None:
             plt.xlim(x_min, x_max)
        
        y_plots_code = "\n".join([f"plt.plot(df['{x_axis}'], df['{col}'], marker='o', linewidth={line_width}, markersize={marker_size}, label='{col}')" for col in y_cols])
        legend_code = "plt.legend()" if len(y_cols) > 1 else ""
        
        code = f"""import matplotlib.pyplot as plt\nimport japanize_matplotlib\nimport pandas as pd\n\ndf = pd.read_csv('{filename}')\nplt.figure(figsize=({width}, {height}))\n{y_plots_code}\n{legend_code}\nplt.xlabel('{x_label_final}', fontsize={font_label})\nplt.ylabel('{y_label_final}', fontsize={font_label})\nplt.title('{title if title else "複数データの比較"}', fontsize={font_title})\nplt.tick_params(labelsize={font_tick})\nplt.grid(True)\nplt.show()"""

        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=100)
        plt.close()
        buf.seek(0)
        img_str = base64.b64encode(buf.read()).decode('utf-8')
        
        return {"image": f"data:image/png;base64,{img_str}", "code": code}
    except Exception as e:
        plt.close()
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
