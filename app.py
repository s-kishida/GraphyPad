import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import japanize_matplotlib
import io

# ページ設定
st.set_page_config(page_title="GraphyPad | 高校生のためのグラフ作成ツール", page_icon="📊", layout="wide")

# カスタムCSS（ダークテーマの微調整）
st.markdown("""
    <style>
    .main { background-color: #0d1117; color: #c9d1d9; }
    .stButton>button { width: 100%; border-radius: 6px; background-color: #238636; color: white; border: none; height: 3em; font-weight: bold; }
    .stButton>button:hover { background-color: #2ea043; border: none; }
    </style>
""", unsafe_allow_html=True)

st.title("📊 GraphyPad")
st.markdown("高校生の探究学習・理科のレポート作成をサポートする高機能グラフツール")

# サイドバー：ファイルアップロードとデータ計算
with st.sidebar:
    st.header("1. データ入力")
    uploaded_file = st.file_uploader("CSVファイルをアップロードしてください", type="csv")
    
    if uploaded_file:
        try:
            # エンコーディングの自動判別（UTF-8 or Shift-JIS）
            try:
                df = pd.read_csv(uploaded_file)
            except UnicodeDecodeError:
                uploaded_file.seek(0)
                df = pd.read_csv(uploaded_file, encoding='shift-jis')
            
            st.success("ファイルを読み込みました！")
            
            # データ計算機能
            st.divider()
            st.header("2. データ計算")
            with st.expander("新しい列を作成"):
                col_to_calc = st.selectbox("元の列を選択", df.columns)
                factor = st.number_input("倍率（係数）", value=1.0, format="%.4f")
                new_col_name = st.text_input("新しい列の名前", value=f"{col_to_calc}_calc")
                
                if st.button("列を追加"):
                    df[new_col_name] = df[col_to_calc] * factor
                    st.toast(f"列 '{new_col_name}' を追加しました！")
            
        except Exception as e:
            st.error(f"エラー: {e}")
            df = None
    else:
        df = None

# メインエリア
if df is not None:
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.header("⚙️ グラフ設定")
        
        # 軸の選択
        tab1, tab2, tab3 = st.tabs(["軸・データ", "外観・サイズ", "タイトル・フォント"])
        
        with tab1:
            x_axis = st.selectbox("X軸（横軸）を選択", df.columns)
            y_axes = st.multiselect("Y軸（縦軸）を選択（複数可）", [c for c in df.columns if c != x_axis], default=[df.columns[1]] if len(df.columns) > 1 else [])
            
            st.divider()
            st.subheader("軸ラベルの設定")
            cx1, cx2 = st.columns(2)
            x_name = cx1.text_input("X軸の名称", value=x_axis)
            x_unit = cx2.text_input("X軸の単位", placeholder="例: s, m/s")
            
            cy1, cy2 = st.columns(2)
            y_name = cy1.text_input("Y軸の名称", value=y_axes[0] if y_axes else "")
            y_unit = cy2.text_input("Y軸の単位", placeholder="例: kg, N")
            
            st.divider()
            st.subheader("表示範囲")
            rx1, rx2 = st.columns(2)
            x_min = rx1.number_input("X軸最小値（空欄で自動）", value=None)
            x_max = rx2.number_input("X軸最大値（空欄で自動）", value=None)

        with tab2:
            st.subheader("プロットの見た目")
            line_w = st.slider("線の太さ", 1.0, 10.0, 3.0)
            marker_s = st.slider("マーカー（点）の大きさ", 1.0, 20.0, 8.0)
            
            st.divider()
            st.subheader("グラフのサイズ")
            g_width = st.slider("横幅", 5.0, 20.0, 10.0)
            g_height = st.slider("高さ", 3.0, 15.0, 6.0)

        with tab3:
            st.subheader("タイトル")
            chart_title = st.text_input("グラフのタイトル", value="実験データの比較" if len(y_axes) > 1 else f"{y_axes[0] if y_axes else ''} vs {x_axis}")
            
            st.divider()
            st.subheader("文字サイズ")
            f_title = st.number_input("タイトルのフォントサイズ", 10, 50, 24)
            f_label = st.number_input("軸ラベルのフォントサイズ", 10, 40, 18)
            f_tick = st.number_input("目盛のフォントサイズ", 8, 30, 14)

    with col2:
        st.header("🖼️ 生成されたグラフ")
        
        if not y_axes:
            st.warning("Y軸を選択してください")
        else:
            # グラフ描画
            fig, ax = plt.subplots(figsize=(g_width, g_height), facecolor='white')
            ax.set_facecolor('white')
            
            for col in y_axes:
                ax.plot(df[x_axis], df[col], marker='o', linewidth=line_w, markersize=marker_s, label=col)
            
            # ラベル整形
            def fmt_lab(name, unit):
                if name and unit: return f"{name} ({unit})"
                return name if name else f"({unit})"
            
            ax.set_xlabel(fmt_lab(x_name, x_unit), fontsize=f_label, color='black')
            ax.set_ylabel(fmt_lab(y_name, y_unit), fontsize=f_label, color='black')
            ax.set_title(chart_title, fontsize=f_title, color='black', pad=20)
            
            if len(y_axes) > 1:
                ax.legend()
            
            ax.tick_params(labelsize=f_tick, colors='black')
            ax.grid(True, linestyle='--', alpha=0.3, color='gray')
            
            if x_min is not None and x_max is not None:
                ax.set_xlim(x_min, x_max)
            
            # 表示
            st.pyplot(fig)
            
            # ダウンロードボタン
            buf = io.BytesIO()
            fig.savefig(buf, format="png", dpi=150, bbox_inches='tight')
            st.download_button(
                label="📁 グラフを画像(PNG)として保存",
                data=buf.getvalue(),
                file_name=f"graph_{uploaded_file.name.split('.')[0]}.png",
                mime="image/png"
            )
            
            # Pythonコードのプレビュー
            with st.expander("🐍 レポート用Pythonコード（Matplotlib）"):
                y_code = "\n".join([f"plt.plot(df['{x_axis}'], df['{col}'], marker='o', linewidth={line_w}, markersize={marker_s}, label='{col}')" for col in y_axes])
                st.code(f"""import pandas as pd
import matplotlib.pyplot as plt
import japanize_matplotlib

# データを読み込む
df = pd.read_csv('{uploaded_file.name}')

# グラフの設定
plt.figure(figsize=({g_width}, {g_height}))
{y_code}
{ 'plt.legend()' if len(y_axes) > 1 else '' }

# ラベルとタイトルの設定
plt.xlabel('{fmt_lab(x_name, x_unit)}', fontsize={f_label})
plt.ylabel('{fmt_lab(y_name, y_unit)}', fontsize={f_label})
plt.title('{chart_title}', fontsize={f_title})
plt.tick_params(labelsize={f_tick})
plt.grid(True)

plt.show()""", language='python')

else:
    # ファイル未アップロード時の表示
    st.info("👈 左側のサイドバーからCSVファイルをアップロードして始めましょう。")
    
    # 使い方ガイド
    st.markdown("""
    ### 🚀 使い方
    1. CSVファイルをアップロードします。
    2. 必要に応じて「列を追加」でデータを加工できます（例：1000倍して単位を変換など）。
    3. X軸とY軸を選択すると、即座にグラフが表示されます。
    4. 「外観」タブで、線の太さや文字の大きさを自由に調整できます。
    5. 完成したグラフはボタン一つで画像として保存できます。
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
