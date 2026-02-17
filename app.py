import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import japanize_matplotlib
import io
import json

# --- デザイン：以前のカスタムCSSをStreamlitに注入 ---
def local_css():
    st.markdown("""
        <style>
        /* 全体の背景色（GitHubダーク） */
        .stApp {
            background-color: #0d1117;
            color: #c9d1d9;
        }
        /* サイドバーの背景色 */
        [data-testid="stSidebar"] {
            background-color: #161b22;
            border-right: 1px solid #30363d;
        }
        /* テキスト入力やセレクトボックス */
        .stTextInput>div>div>input, .stSelectbox>div>div>div {
            background-color: #0d1117 !important;
            color: #c9d1d9 !important;
            border-color: #30363d !important;
        }
        /* セクション見出し */
        h1, h2, h3 {
            color: #58a6ff !important;
            font-weight: 600 !important;
        }
        /* ボタンのデザイン */
        .stButton>button {
            background-color: #238636 !important;
            color: white !important;
            border: none !important;
            border-radius: 6px !important;
            font-weight: bold;
            width: 100%;
        }
        .stButton>button:hover {
            background-color: #2ea043 !important;
        }
        /* 強調ラベル */
        .stMarkdown p {
            font-size: 0.95rem;
        }
        </style>
    """, unsafe_allow_html=True)

local_css()

# タイトル（以前のスタイル）
st.title("GraphyPad")
st.markdown("<p style='color: #8b949e; margin-top: -15px;'>高校生のためのグラフ作成ツール</p>", unsafe_allow_html=True)

# --- サイドバー：以前のセクション構成を再現 ---
with st.sidebar:
    st.header("Data Input")
    uploaded_file = st.file_uploader("CSVファイルを選択", type="csv")
    
    df = None
    if uploaded_file:
        try:
            try:
                df = pd.read_csv(uploaded_file)
            except UnicodeDecodeError:
                uploaded_file.seek(0)
                df = pd.read_csv(uploaded_file, encoding='shift-jis')
        except Exception as e:
            st.error(f"Error: {e}")

    if df is not None:
        st.divider()
        st.header("Axis Settings")
        x_axis = st.selectbox("X-Axis (横軸)", df.columns)
        y_axes = st.multiselect("Y-Axis (縦軸: 複数選択可)", [c for c in df.columns if c != x_axis], default=[df.columns[1]] if len(df.columns) > 1 else [])
        
        st.divider()
        st.header("Data Calculation")
        with st.expander("列を計算して追加"):
            col_a = st.selectbox("対象の列", df.columns, key="calc_col")
            factor = st.number_input("倍率", value=1.0, format="%.4f")
            new_col = st.text_input("新しい列の名前", value=f"{col_a}_calc")
            if st.button("Calculate & Add"):
                df[new_col] = df[col_a] * factor
                st.toast(f"Added {new_col}")

        st.divider()
        st.header("Label Settings")
        chart_title = st.text_input("Graph Title", value="Multiple Data Comparison" if len(y_axes) > 1 else f"{y_axes[0] if y_axes else ''} vs {x_axis}")
        
        c1, c2 = st.columns(2)
        x_name = c1.text_input("X Name", value=x_axis)
        x_unit = c2.text_input("X Unit", placeholder="s, m, etc.")
        
        c3, c4 = st.columns(2)
        y_name = c3.text_input("Y Name", value=y_axes[0] if y_axes else "")
        y_unit = c4.text_input("Y Unit", placeholder="N, kg, etc.")
        
        st.subheader("Font Sizes")
        f1, f2, f3 = st.columns(3)
        font_title = f1.number_input("Title", 10, 50, 24)
        font_label = f2.number_input("Label", 10, 40, 18)
        font_tick = f3.number_input("Tick", 8, 30, 14)

        st.divider()
        st.header("Plot Settings")
        p1, p2 = st.columns(2)
        marker_size = p1.number_input("Marker Size", 1.0, 20.0, 8.0)
        line_width = p2.number_input("Line Width", 1.0, 10.0, 3.0)

        st.divider()
        st.header("Graph Size")
        s1, s2 = st.columns(2)
        width_val = s1.number_input("Width", 5.0, 20.0, 10.0)
        height_val = s2.number_input("Height", 3.0, 15.0, 6.0)

        st.divider()
        st.header("Scale Settings")
        xmin_val = st.number_input("X Min (Auto if empty)", value=None)
        xmax_val = st.number_input("X Max (Auto if empty)", value=None)

# --- メインエリア ---
if df is not None:
    if not y_axes:
        st.info("👈 サイドバーで描画するY軸のデータを選択してください。")
    else:
        # グラフ作成
        fig, ax = plt.subplots(figsize=(width_val, height_val), facecolor='white')
        ax.set_facecolor('white')
        
        for col in y_axes:
            ax.plot(df[x_axis], df[col], marker='o', linewidth=line_width, markersize=marker_size, label=col)
        
        # ラベル整形
        def fmt(n, u):
            if n and u: return f"{n} ({u})"
            return n if n else (f"({u})" if u else "")

        ax.set_xlabel(fmt(x_name, x_unit) or x_axis, fontsize=font_label, color='black')
        ax.set_ylabel(fmt(y_name, y_unit) or (y_axes[0] if len(y_axes)==1 else ""), fontsize=font_label, color='black')
        ax.set_title(chart_title, fontsize=font_title, color='black', pad=20)
        
        if len(y_axes) > 1: ax.legend()
        ax.tick_params(labelsize=font_tick, colors='black')
        ax.grid(True, linestyle='--', alpha=0.3, color='gray')
        if xmin_val is not None and xmax_val is not None: ax.set_xlim(xmin_val, xmax_val)
        
        # 表示
        st.pyplot(fig)
        
        # 保存とコード
        cx1, cx2 = st.columns(2)
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=150, bbox_inches='tight')
        cx1.download_button("📁 画像をダウンロード", buf.getvalue(), f"graph.png", "image/png")
        
        with st.expander("Python Code"):
            st.code("# Matplotlib code summary will be generated here...", language='python')
else:
    # ファイル未アップロード時の表示
    st.info("👈 左側のサイドバーからCSVファイルをアップロードして始めましょう。")
    
    # 使い方ガイド
    st.markdown("""
    ### 🚀 使い方
    1. **CSVファイルをアップロード**: 左側のパネルからデータを選択します。
    2. **データ加工**: 「Data Calculation」で単位変換などが可能です。
    3. **グラフ作成**: 「Axis Settings」で軸を選ぶと即座に描画されます。
    4. **見た目の調整**: フォントサイズや線の太さを自分好みに調整できます。
    5. **ダウンロード**: 「📁 画像をダウンロード」でレポートに貼れるPNGを保存できます。
    """)
    
    # サンプルデータ作成・DL機能
    st.divider()
    sample_df = pd.DataFrame({
        "時間": [0, 1, 2, 3, 4, 5],
        "速度1": [0, 2.1, 3.9, 6.2, 8.1, 9.8],
        "速度2": [0, 1.5, 3.2, 4.5, 6.1, 7.8]
    })
    st.write("サンプルデータで試すにはこちらをダウンロード:")
    st.download_button("サンプルCSVをダウンロード", sample_df.to_csv(index=False).encode('utf-8-sig'), "sample.csv", "text/csv")
