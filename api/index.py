import os
import io
import json
import base64
import pandas as pd
import matplotlib.pyplot as plt
import japanize_matplotlib
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from typing import Optional

app = FastAPI()

# Determine the base path (for Vercel environment)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# In serverless, we can only write to /tmp
UPLOAD_DIR = "/tmp/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Static files mapping
STATIC_DIR = os.path.join(BASE_DIR, "static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

def read_csv_with_fallback(file_path):
    try:
        return pd.read_csv(file_path)
    except UnicodeDecodeError:
        return pd.read_csv(file_path, encoding='shift-jis')
    except Exception as e:
        raise e

@app.get("/", response_class=HTMLResponse)
async def read_index():
    index_path = os.path.join(STATIC_DIR, "index.html")
    with open(index_path, "r", encoding="utf-8") as f:
        return f.read()

@app.post("/upload")
async def upload_csv(file: UploadFile = File(...)):
    if not file.filename.lower().endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed.")
    
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as f:
        f.write(await file.read())
    
    try:
        df = read_csv_with_fallback(file_path)
        columns = df.columns.tolist()
        return {"filename": file.filename, "columns": columns}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading CSV: {str(e)}")

@app.post("/calculate")
async def calculate_column(
    filename: str = Form(...),
    new_col: str = Form(...),
    col_a: str = Form(...),
    factor: float = Form(...)
):
    file_path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(file_path):
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
    y_axis_list: str = Form(...), # JSON string of list
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
    file_path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        df = read_csv_with_fallback(file_path)
        y_cols = json.loads(y_axis_list)
        
        # Plotting
        plt.figure(figsize=(width, height), facecolor='white')
        ax = plt.axes()
        ax.set_facecolor('white')
        
        # Plot data for each Y column
        for col in y_cols:
            plt.plot(df[x_axis], df[col], marker='o', linewidth=line_width, markersize=marker_size, label=col)
        
        # Helper to format label
        def format_label(name, unit, default):
            if not name and not unit: return default
            if name and unit: return f"{name} ({unit})"
            return name if name else f"({unit})"

        x_label_final = format_label(x_name, x_unit, x_axis)
        y_label_final = format_label(y_name, y_unit, y_cols[0] if len(y_cols) == 1 else "")

        # Labels and Style
        plt.xlabel(x_label_final, color='black', fontsize=font_label)
        plt.ylabel(y_label_final, color='black', fontsize=font_label)
        plt.title(title if title else (f"{y_cols[0]} vs {x_axis}" if len(y_cols) == 1 else "複数データの比較"), color='black', fontsize=font_title, pad=20)
        
        if len(y_cols) > 1:
            plt.legend()

        # Axis colors
        ax.spines['bottom'].set_color('black')
        ax.spines['top'].set_color('black')
        ax.spines['left'].set_color('black')
        ax.spines['right'].set_color('black')
        ax.tick_params(axis='x', colors='black', labelsize=font_tick)
        ax.tick_params(axis='y', colors='black', labelsize=font_tick)
        
        # Grid
        plt.grid(True, linestyle='--', alpha=0.3, color='gray')
        
        # Custom limits
        if x_min is not None and x_max is not None:
             plt.xlim(x_min, x_max)
        
        # Generate Python Code String
        y_plots_code = "\n".join([f"plt.plot(df['{x_axis}'], df['{col}'], marker='o', linewidth={line_width}, markersize={marker_size}, label='{col}')" for col in y_cols])
        legend_code = "plt.legend()" if len(y_cols) > 1 else ""
        
        code = f"""import matplotlib.pyplot as plt
import japanize_matplotlib
import pandas as pd

# データを読み込む
df = pd.read_csv('{filename}')

# グラフの設定
plt.figure(figsize=({width}, {height}))
{y_plots_code}
{legend_code}

# ラベルとタイトルの設定
plt.xlabel('{x_label_final}', fontsize={font_label})
plt.ylabel('{y_label_final}', fontsize={font_label})
plt.title('{title if title else (f"{y_cols[0]} vs {x_axis}" if len(y_cols) == 1 else "複数データの比較")}', fontsize={font_title})
plt.tick_params(labelsize={font_tick})
plt.grid(True)

# 表示
plt.show()"""

        # Save to buffer
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=100)
        plt.close()
        buf.seek(0)
        
        img_str = base64.b64encode(buf.read()).decode('utf-8')
        
        return {
            "image": f"data:image/png;base64,{img_str}",
            "code": code
        }
    except Exception as e:
        plt.close()
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
