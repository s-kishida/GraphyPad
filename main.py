import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import japanize_matplotlib
import io
import json
import numpy as np
from matplotlib.ticker import MultipleLocator

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
            "折れ線グラフ", "散布図", "棒グラフ", "複合グラフ", "ヒストグラム", "円グラフ", "箱ひげ図", "バイオリンプロット"
        ])
        
        # グラフの種類に応じて設定項目を変える
        if chart_type in ["折れ線グラフ", "散布図", "棒グラフ", "複合グラフ"]:
            x_axis = st.selectbox("X-Axis (横軸)", df.columns)
            y_axes = st.multiselect("Y-Axis (縦軸: 複数選択可)", [c for c in df.columns if c != x_axis], default=[df.columns[1]] if len(df.columns) > 1 else [])
            
            y_configs = {}
            if chart_type == "複合グラフ" and y_axes:
                st.caption("各列のプロット形式:")
                for col in y_axes:
                    y_configs[col] = st.selectbox(f"{col}", ["Line", "Scatter", "Bar"], key=f"type_{col}")
            else:
                # 複合以外の時はデフォルトの型を適用
                base_type = "Line" if chart_type == "折れ線グラフ" else ("Scatter" if chart_type == "散布図" else "Bar")
                for col in y_axes:
                    y_configs[col] = base_type
            
            y_axis_mapping = {}
            if y_axes and chart_type != "円グラフ":
                with st.expander("Axis Settings (軸の割り当て)", expanded=False):
                    for col in y_axes:
                        y_axis_mapping[col] = st.number_input(f"Axis for {col} (0:左, 1:右, 2+:右オフセット)", 0, 5, 0, key=f"axis_{col}")
            else:
                for col in y_axes: y_axis_mapping[col] = 0
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
        y_name = c3.text_input("Y Name (Axis 0)", value=y_axes[0] if y_axes else "")
        y_unit = c4.text_input("Y Unit (Axis 0)", placeholder="N, kg, etc.")
        
        # 追加軸のラベル設定
        used_axes = set(y_axis_mapping.values()) if y_axis_mapping else {0}
        other_labels = {}
        if any(idx > 0 for idx in used_axes):
            with st.expander("Additional Axis Labels", expanded=False):
                for idx in sorted(list(used_axes)):
                    if idx == 0: continue
                    la1, la2 = st.columns(2)
                    other_labels[idx] = {
                        "name": la1.text_input(f"Axis {idx} Name", value="", key=f"y_name_{idx}"),
                        "unit": la2.text_input(f"Axis {idx} Unit", value="", key=f"y_unit_{idx}")
                    }
        
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
        
        aspect_choice = st.selectbox("Aspect Ratio (Data)", ["auto", "equal", "custom"], index=0)
        aspect_val = None
        if aspect_choice == "custom":
            aspect_val = st.number_input("Custom Ratio (Height/Width)", value=1.0, step=0.1)
        elif aspect_choice == "equal":
            aspect_val = "equal"
        else:
            aspect_val = "auto"

        st.divider()
        st.header("Scale Settings")
        c_sc1, c_sc2 = st.columns(2)
        xmin_val = c_sc1.number_input("X Min (Auto if empty)", value=None)
        xmax_val = c_sc2.number_input("X Max (Auto if empty)", value=None)
        
        c_sc3, c_sc4 = st.columns(2)
        ymin_val = c_sc3.number_input("Y Min (Auto if empty)", value=None)
        ymax_val = c_sc4.number_input("Y Max (Auto if empty)", value=None)

        st.divider()
        st.header("Tick & Grid Details")
        with st.expander("X-Axis Ticks"):
            x_major_step = st.number_input("X Major Interval", value=None, key="x_maj")
            x_minor_step = st.number_input("X Minor Interval", value=None, key="x_min")
        with st.expander("Y-Axis Ticks"):
            y_major_step = st.number_input("Y Major Interval", value=None, key="y_maj")
            y_minor_step = st.number_input("Y Minor Interval", value=None, key="y_min")
        with st.expander("Grid & Other"):
            grid_major = st.checkbox("Show Major Grid", value=True)
            grid_minor = st.checkbox("Show Minor Grid", value=False)
            tick_dir = st.selectbox("Tick Direction (目盛の向き)", ["in", "out", "inout"], index=0)

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
        
        # ラベル整形用関数
        def fmt(n, u):
            if n and u: return f"{n} ({u})"
            return n if n else (f"({u})" if u else "")
        
        try:
            if chart_type in ["折れ線グラフ", "散布図", "棒グラフ", "複合グラフ"]:
                # X軸が数値かどうかを判定
                is_numeric_x = pd.api.types.is_numeric_dtype(df[x_axis])
                
                # 座標の決定
                if is_numeric_x and chart_type != "棒グラフ":
                    # 実数値ベース（折れ線、散布図、または複合でXが数値の場合）
                    x_plot = df[x_axis].values
                    use_index_x = False
                else:
                    # カテゴリベース（棒グラフ単体、またはXが数値でない場合）
                    x_plot = np.arange(len(df))
                    use_index_x = True
                
                bar_cols = [c for c, t in y_configs.items() if t == "Bar"]
                if bar_cols:
                    if not use_index_x and len(df) > 1:
                        # 数値軸の場合、データの最小間隔に合わせて棒の幅を計算
                        diffs = np.diff(np.sort(x_plot))
                        min_diff = np.min(diffs[diffs > 0]) if any(diffs > 0) else 1.0
                        total_width = min_diff * 0.8
                    else:
                        total_width = 0.8
                    width = total_width / len(bar_cols)
                
                # 軸の初期化
                axes = {0: ax}
                max_axis_idx = max(y_axis_mapping.values()) if y_axis_mapping else 0
                for i in range(1, max_axis_idx+1):
                    new_ax = ax.twinx()
                    if i > 1:
                        new_ax.spines["right"].set_position(("axes", 1.0 + (i-1)*0.15))
                    axes[i] = new_ax
                    code_snippets.append(f"ax{i} = ax.twinx()")
                    if i > 1:
                        code_snippets.append(f"ax{i}.spines['right'].set_position(('axes', {1.0 + (i-1)*0.15}))")

                bar_count = 0
                for col in y_axes:
                    p_type = y_configs[col]
                    a_idx = y_axis_mapping.get(col, 0)
                    target_ax = axes[a_idx]
                    ax_prefix = f"ax{a_idx}" if a_idx > 0 else "ax"
                    
                    if p_type == "Line":
                        target_ax.plot(x_plot, df[col], marker='o', linewidth=line_width, markersize=marker_size, label=col)
                        code_snippets.append(f"{ax_prefix}.plot(x_plot, df['{col}'], marker='o', linewidth={line_width}, markersize={marker_size}, label='{col}')")
                    elif p_type == "Scatter":
                        target_ax.scatter(x_plot, df[col], s=marker_size*10, label=col, alpha=0.7)
                        code_snippets.append(f"{ax_prefix}.scatter(x_plot, df['{col}'], s={marker_size*10}, label='{col}', alpha=0.7)")
                    elif p_type == "Bar":
                        if len(bar_cols) > 0:
                            offset = (bar_count - len(bar_cols)/2 + 0.5) * width
                            target_ax.bar(x_plot + offset, df[col], width, label=col)
                            code_snippets.append(f"{ax_prefix}.bar(x_plot + {offset}, df['{col}'], {width}, label='{col}')")
                            bar_count += 1
                        else:
                            target_ax.bar(x_plot, df[col], label=col)
                            code_snippets.append(f"{ax_prefix}.bar(x_plot, df['{col}'], label='{col}')")
                
                if use_index_x:
                    ax.set_xticks(x_plot)
                    ax.set_xticklabels(df[x_axis])
                    code_snippets.insert(0, f"ax.set_xticks(x_plot)\nax.set_xticklabels(df['{x_axis}'])")
                
                code_snippets.insert(0, f"import numpy as np\nx_plot = ... # values or arange\n")

                # 各軸のラベル設定
                for i, target_ax in axes.items():
                    if i == 0:
                        target_ax.set_ylabel(fmt(y_name, y_unit) or (y_axes[0] if len(y_axes)==1 else ""), fontsize=font_label, color='black')
                    else:
                        label_info = other_labels.get(i, {"name": "", "unit": ""})
                        target_ax.set_ylabel(fmt(label_info["name"], label_info["unit"]), fontsize=font_label, color='black')
                        code_snippets.append(f"ax{i}.set_ylabel('{fmt(label_info['name'], label_info['unit'])}', fontsize={font_label})")

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


            if chart_type != "円グラフ":
                ax.set_xlabel(fmt(x_name, x_unit) or (x_axis if x_axis else ""), fontsize=font_label, color='black')
                ax.set_ylabel(fmt(y_name, y_unit) or (y_axes[0] if len(y_axes)==1 else ""), fontsize=font_label, color='black')
            
            ax.set_title(chart_title, fontsize=font_title, color='black', pad=20)
            
            if len(y_axes) > 1 and chart_type not in ["円グラフ", "ヒストグラム"]:
                ax.legend()
            elif chart_type == "ヒストグラム":
                ax.legend()
                
            ax.tick_params(labelsize=font_tick, colors='black')
            
            # --- 目盛・グリッドの詳細設定適用 ---
            if chart_type not in ["円グラフ", "ヒストグラム", "箱ひげ図", "バイオリンプロット"]:
                # 先に補助目盛を有効化（後から呼ぶとLocatorがリセットされるため）
                if x_minor_step or y_minor_step or grid_minor:
                    ax.minorticks_on()
                
                # 目盛間隔の設定
                if x_major_step: ax.xaxis.set_major_locator(MultipleLocator(x_major_step))
                if x_minor_step: ax.xaxis.set_minor_locator(MultipleLocator(x_minor_step))
                if y_major_step: ax.yaxis.set_major_locator(MultipleLocator(y_major_step))
                if y_minor_step: ax.yaxis.set_minor_locator(MultipleLocator(y_minor_step))
                
                # 目盛自体の見た目調整
                ax.tick_params(which='major', labelsize=font_tick, colors='black', length=6, direction=tick_dir)
                ax.tick_params(which='minor', colors='black', length=3, direction=tick_dir)
                
                # グリッド
                if grid_major:
                    ax.grid(True, which='major', linestyle='--', alpha=0.3, color='gray')
                else:
                    ax.grid(False, which='major')
                if grid_minor:
                    ax.grid(True, which='minor', linestyle=':', alpha=0.2, color='gray')
                else:
                    ax.grid(False, which='minor')

            if chart_type in ["折れ線グラフ", "散布図"]:
                if xmin_val is not None: ax.set_xlim(left=xmin_val)
                if xmax_val is not None: ax.set_xlim(right=xmax_val)
                if ymin_val is not None: ax.set_ylim(bottom=ymin_val)
                if ymax_val is not None: ax.set_ylim(top=ymax_val)
                ax.set_aspect(aspect_val)
            
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
                
                # グリッドと目盛のコード生成
                if chart_type not in ["円グラフ", "ヒストグラム", "箱ひげ図", "バイオリンプロット"]:
                    full_code += "from matplotlib.ticker import MultipleLocator\n"
                    if x_major_step: full_code += f"ax.xaxis.set_major_locator(MultipleLocator({x_major_step}))\n"
                    if x_minor_step: full_code += f"ax.xaxis.set_minor_locator(MultipleLocator({x_minor_step}))\n"
                    if y_major_step: full_code += f"ax.yaxis.set_major_locator(MultipleLocator({y_major_step}))\n"
                    if y_minor_step: full_code += f"ax.yaxis.set_minor_locator(MultipleLocator({y_minor_step}))\n"
                    
                    if grid_major:
                        full_code += "ax.grid(True, which='major', linestyle='--', alpha=0.3)\n"
                    if grid_minor:
                        full_code += "ax.minorticks_on()\n"
                        full_code += "ax.grid(True, which='minor', linestyle=':', alpha=0.2)\n"
                    
                    full_code += f"ax.tick_params(which='both', direction='{tick_dir}')\n"

                if len(y_axes) > 1:
                    full_code += "ax.legend()\n"
                
                # スケール設定をコードに追加
                if chart_type in ["折れ線グラフ", "散布図"]:
                    if xmin_val is not None: full_code += f"ax.set_xlim(left={xmin_val})\n"
                    if xmax_val is not None: full_code += f"ax.set_xlim(right={xmax_val})\n"
                    if ymin_val is not None: full_code += f"ax.set_ylim(bottom={ymin_val})\n"
                    if ymax_val is not None: full_code += f"ax.set_ylim(top={ymax_val})\n"
                    if aspect_val != 'auto':
                        val_str = f"'{aspect_val}'" if isinstance(aspect_val, str) else aspect_val
                        full_code += f"ax.set_aspect({val_str})\n"

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
