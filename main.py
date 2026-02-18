import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import japanize_matplotlib
import io
import json
import numpy as np

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
        /* Google風ページネーション用スタイル */
        .page-num-row button {
            background: none !important;
            border: none !important;
            color: #8ab4f8 !important;
            padding: 0 !important;
            min-height: 24px !important;
            line-height: 1.5 !important;
            font-weight: normal !important;
        }
        .page-num-row button:hover {
            text-decoration: underline !important;
            color: #d1d5da !important;
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
        chart_type = st.selectbox("Chart Type (グラフの種類)", [
            "折れ線グラフ", "散布図", "棒グラフ", "ヒストグラム", "円グラフ", "箱ひげ図", "バイオリンプロット"
        ])
        
        # グラフの種類に応じて設定項目を変える
        if chart_type in ["折れ線グラフ", "散布図", "棒グラフ"]:
            x_axis = st.selectbox("X-Axis (横軸)", df.columns)
            y_axes = st.multiselect("Y-Axis (縦軸: 複数選択可)", [c for c in df.columns if c != x_axis], default=[df.columns[1]] if len(df.columns) > 1 else [])
        elif chart_type == "円グラフ":
            x_axis = st.selectbox("Labels (ラベルにする列)", df.columns)
            y_axes = st.multiselect("Values (数値の列: 1つ選択)", [c for c in df.columns if c != x_axis], default=[df.columns[1]] if len(df.columns) > 1 else [], max_selections=1)
        elif chart_type == "ヒストグラム":
            x_axis = None
            y_axes = st.multiselect("Data (対象の列: 複数選択可)", df.columns, default=[df.columns[0]])
        else: # 箱ひげ図, バイオリンプロット
            x_axis = None
            y_axes = st.multiselect("Data (対象の列: 複数選択可)", df.columns, default=df.columns.tolist()[:3])
        

        st.divider()
        st.header("Label Settings")
        default_title = f"{chart_type}"
        if y_axes:
            if chart_type in ["折れ線グラフ", "散布図", "棒グラフ"] and x_axis:
                default_title = f"{', '.join(y_axes)} vs {x_axis}"
            else:
                default_title = f"{chart_type}: {', '.join(y_axes)}"
                
        chart_title = st.text_input("Graph Title", value=default_title)
        
        c1, c2 = st.columns(2)
        x_name = c1.text_input("X Name", value=x_axis if x_axis else "")
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
        marker_size = p1.number_input("Marker Size", 1.0, 50.0, 8.0)
        line_width = p2.number_input("Line/Bar Width", 0.1, 10.0, 1.5 if chart_type == "棒グラフ" else 3.0)

        st.divider()
        st.header("Graph Size")
        s1, s2 = st.columns(2)
        width_val = s1.number_input("Width", 5.0, 30.0, 10.0)
        height_val = s2.number_input("Height", 3.0, 30.0, 6.0)

        st.divider()
        st.header("Scale Settings")
        xmin_val = st.number_input("X Min (Auto if empty)", value=None)
        xmax_val = st.number_input("X Max (Auto if empty)", value=None)

# --- メインエリア ---
if df is not None:
    # データ情報の表示
    with st.expander("📊 アップロードされたデータの詳細を確認", expanded=False):
        st.subheader("データ概要")
        # 各列の情報をまとめる
        info_df = pd.DataFrame({
            "列名": df.columns,
            "データ型": [str(t) for t in df.dtypes],
            "有効データ数": df.count().values,
            "欠損数": df.isnull().sum().values
        })
        st.table(info_df)
        
        st.subheader("データの数値参照")
        total_rows = len(df)
        if total_rows > 50:
            page_size = 50
            num_pages = (total_rows - 1) // page_size + 1
            
            # セッション状態でのページ管理
            if "page_num" not in st.session_state:
                st.session_state.page_num = 1
            
            # --- ページ番号と「次へ」の配置 ---
            cols_spec = [1] * num_pages + [2, 10]
            p_cols = st.columns(cols_spec)
            
            for i in range(1, num_pages + 1):
                with p_cols[i-1]:
                    st.markdown("<div class='page-num-row'>", unsafe_allow_html=True)
                    if i == st.session_state.page_num:
                        # 現在のページは数字のみ（リンクにしない）
                        st.markdown(f"<div style='text-align:center; color:white; font-size:18px; font-weight:bold; margin-top:5px;'>{i}</div>", unsafe_allow_html=True)
                    else:
                        if st.button(str(i), key=f"pg_{i}"):
                            st.session_state.page_num = i
                            st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)
            
            # 「次へ」ボタン
            with p_cols[num_pages]:
                st.markdown("<div class='page-num-row'>", unsafe_allow_html=True)
                if st.session_state.page_num < num_pages:
                    if st.button("次へ >", key="pg_next"):
                        st.session_state.page_num += 1
                        st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
                
            # 指定範囲のデータを表示
            page_num = st.session_state.page_num
            start_idx = (page_num - 1) * page_size
            end_idx = min(start_idx + page_size, total_rows)
            st.caption(f"{total_rows}行中 {start_idx + 1} 〜 {end_idx} 行目を表示しています")
            st.dataframe(df.iloc[start_idx:end_idx], use_container_width=True)
        else:
            st.dataframe(df, use_container_width=True)
    
    if not y_axes:
        st.info("👈 サイドバーで描画するデータを選択してください。")
    else:
        # グラフ作成
        fig, ax = plt.subplots(figsize=(width_val, height_val), facecolor='white')
        ax.set_facecolor('white')
        
        code_snippets = []
        
        try:
            if chart_type == "折れ線グラフ":
                for col in y_axes:
                    ax.plot(df[x_axis], df[col], marker='o', linewidth=line_width, markersize=marker_size, label=col)
                    code_snippets.append(f"ax.plot(df['{x_axis}'], df['{col}'], marker='o', linewidth={line_width}, markersize={marker_size}, label='{col}')")
            
            elif chart_type == "散布図":
                for col in y_axes:
                    ax.scatter(df[x_axis], df[col], s=marker_size*10, label=col, alpha=0.7)
                    code_snippets.append(f"ax.scatter(df['{x_axis}'], df['{col}'], s={marker_size*10}, label='{col}', alpha=0.7)")
            
            elif chart_type == "棒グラフ":
                x = np.arange(len(df[x_axis]))
                width = 0.8 / len(y_axes)
                for i, col in enumerate(y_axes):
                    ax.bar(x + (i - len(y_axes)/2 + 0.5) * width, df[col], width, label=col)
                    code_snippets.append(f"ax.bar(x + ({i} - {len(y_axes)}/2 + 0.5) * {width}, df['{col}'], {width}, label='{col}')")
                ax.set_xticks(x)
                ax.set_xticklabels(df[x_axis])
                code_snippets.insert(0, f"import numpy as np\nx = np.arange(len(df['{x_axis}']))\nwidth = 0.8 / {len(y_axes)}")

            elif chart_type == "ヒストグラム":
                ax.hist([df[col].dropna() for col in y_axes], bins=20, label=y_axes, alpha=0.7)
                code_snippets.append(f"ax.hist([df[col].dropna() for col in {y_axes}], bins=20, label={y_axes}, alpha=0.7)")
                
            elif chart_type == "円グラフ":
                val_col = y_axes[0]
                ax.pie(df[val_col], labels=df[x_axis], autopct='%1.1f%%', startangle=90, counterclock=False)
                code_snippets.append(f"ax.pie(df['{val_col}'], labels=df['{x_axis}'], autopct='%1.1f%%', startangle=90, counterclock=False)")
                
            elif chart_type == "箱ひげ図":
                ax.boxplot([df[col].dropna() for col in y_axes], labels=y_axes)
                code_snippets.append(f"ax.boxplot([df[col].dropna() for col in {y_axes}], labels={y_axes})")
                
            elif chart_type == "バイオリンプロット":
                parts = ax.violinplot([df[col].dropna() for col in y_axes], showmeans=True)
                ax.set_xticks(range(1, len(y_axes) + 1))
                ax.set_xticklabels(y_axes)
                code_snippets.append(f"ax.violinplot([df[col].dropna() for col in {y_axes}], showmeans=True)")

            # ラベル整形
            def fmt(n, u):
                if n and u: return f"{n} ({u})"
                return n if n else (f"({u})" if u else "")

            if chart_type != "円グラフ":
                ax.set_xlabel(fmt(x_name, x_unit) or (x_axis if x_axis else ""), fontsize=font_label, color='black')
                ax.set_ylabel(fmt(y_name, y_unit) or (y_axes[0] if len(y_axes)==1 else ""), fontsize=font_label, color='black')
            
            ax.set_title(chart_title, fontsize=font_title, color='black', pad=20)
            
            if len(y_axes) > 1 and chart_type not in ["円グラフ", "ヒストグラム"]:
                ax.legend()
            elif chart_type == "ヒストグラム":
                ax.legend()
                
            ax.tick_params(labelsize=font_tick, colors='black')
            if chart_type not in ["円グラフ", "箱ひげ図", "バイオリンプロット"]:
                ax.grid(True, linestyle='--', alpha=0.3, color='gray')
            
            if chart_type in ["折れ線グラフ", "散布図"] and xmin_val is not None and xmax_val is not None:
                ax.set_xlim(xmin_val, xmax_val)
            
            # 表示
            st.pyplot(fig)
            
            # 保存とコード
            cx1, cx2 = st.columns(2)
            buf = io.BytesIO()
            fig.savefig(buf, format="png", dpi=150, bbox_inches='tight')
            cx1.download_button("📁 画像をダウンロード", buf.getvalue(), f"graph.png", "image/png")
            
            with st.expander("Python Code"):
                full_code = f"""import pandas as pd
import matplotlib.pyplot as plt
import japanize_matplotlib

# データを読み込む
df = pd.read_csv('data.csv')

fig, ax = plt.subplots(figsize=({width_val}, {height_val}))

{chr(10).join(code_snippets)}

ax.set_title('{chart_title}', fontsize={font_title})
"""
                if chart_type != "円グラフ":
                    full_code += f"ax.set_xlabel('{fmt(x_name, x_unit)}', fontsize={font_label})\n"
                    full_code += f"ax.set_ylabel('{fmt(y_name, y_unit)}', fontsize={font_label})\n"
                
                full_code += f"ax.tick_params(labelsize={font_tick})\n"
                if chart_type not in ["円グラフ", "箱ひげ図", "バイオリンプロット"]:
                    full_code += "ax.grid(True)\n"
                if len(y_axes) > 1:
                    full_code += "ax.legend()\n"
                full_code += "plt.show()"
                
                st.code(full_code, language='python')
                
        except Exception as e:
            st.error(f"グラフ生成中にエラーが発生しました: {e}")
            st.info("選択したデータが数値として正しく読み込めているか確認してください。")

else:
    # ファイル未アップロード時の表示
    st.info("👈 左側のサイドバーからCSVファイルをアップロードして始めましょう。")
    
    # 使い方ガイド
    st.markdown("""
    ### 使い方
    1. **CSVファイルをアップロード**: 左側のパネルからデータを選択します。
    2. **グラフの種類を選択**: 折れ線グラフ、棒グラフ、ヒストグラムなどから選べます。
    3. **見た目の調整**: フォントサイズや線の太さを自分好みに調整できます。
    4. **ダウンロード**: 「 画像をダウンロード」でレポートに貼れるPNGを保存できます。
    """)
    
    # サンプルデータ作成・DL機能
    st.divider()
    st.subheader("💡 サンプルデータで試す")
    st.markdown("グラフの種類に合わせたサンプルCSVをダウンロードして、使い心地を確認できます。")
    
    col_s1, col_s2, col_s3 = st.columns(3)
    
    with col_s1:
        st.write("**実験・変化データ**")
        st.caption("折れ線グラフ・散布図向き")
        # 120行の時系列データ
        rows = 120
        exp_df = pd.DataFrame({
            "時間(s)": np.arange(rows) * 5,
            "温度A(℃)": (20 + np.cumsum(np.random.normal(0.3, 0.5, rows))).round(1),
            "温度B(℃)": (18 + np.cumsum(np.random.normal(0.2, 0.4, rows))).round(1)
        })
        st.download_button("🌡️ 実験データのDL", exp_df.to_csv(index=False).encode('utf-8-sig'), "sample_experiment.csv", "text/csv")

    with col_s2:
        st.write("**分類・割合データ**")
        st.caption("棒グラフ・円グラフ向き")
        # 120行の記録データ（項目を繰り返して日付風に）
        items = ["食費", "光熱費", "通信費", "遊び", "その他"]
        rows = 120
        cat_df = pd.DataFrame({
            "通番": np.arange(1, rows + 1),
            "項目": [items[i % len(items)] for i in range(rows)],
            "金額(円)": np.random.randint(100, 5000, rows),
            "満足度": np.random.randint(1, 6, rows)
        })
        st.download_button("📊 分類データのDL", cat_df.to_csv(index=False).encode('utf-8-sig'), "sample_category.csv", "text/csv")

    with col_s3:
        st.write("**分布・統計データ**")
        st.caption("ヒスト（箱・バイオリン）向き")
        # 120行の統計用データ
        rows = 120
        np.random.seed(42)
        stat_df = pd.DataFrame({
            "グループ1": np.random.normal(70, 10, rows),
            "グループ2": np.random.normal(60, 15, rows),
            "グループ3": np.random.normal(80, 5, rows)
        }).round(1)
        st.download_button("統計データのDL", stat_df.to_csv(index=False).encode('utf-8-sig'), "sample_stats.csv", "text/csv")
