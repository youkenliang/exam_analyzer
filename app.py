import streamlit as st
import pandas as pd
import database
import utils
import time
import analysis, visuals, report_generator ### import functions from other files

# 脚本加载时立即初始化数据库
database.init_db()

# 页面配置
st.set_page_config(page_title="学生成绩分析系统", page_icon="📊", layout="wide")

def main():
    st.title("📊 学生成绩分析系统")

    # --- 1. 核心 UI 框架 ---
    tab1, tab2, tab3, tab4 = st.tabs([
        "📝 数据提取与入库", 
        "📈 成绩分析", 
        "📄 报告生成", 
        "🗄️ 数据库管理"
    ])

    # === Tab 1: 数据提取与入库 (上传逻辑移到这里) ===
    with tab1:
        st.header("1. 导入新成绩")
        uploaded_file = st.file_uploader("选择 Excel 文件以添加新数据", type=["xlsx", "xls"])
        
        if uploaded_file:
            years = ["2025-2026", "2026-2027", "2027-2028", "2028-2029"]
            sel_year = st.selectbox("学年", years, index=0)
            # 这里的逻辑保持你之前的 Sheet 选择和预览
            excel_reader = pd.ExcelFile(uploaded_file)
            sheet_names = excel_reader.sheet_names
            # 如果预设名在列表里，找到它的位置；否则默认选第0个
            default_sheet = "新能源25（1）班"  # 你期望首选的班级名
            try:
                default_index = sheet_names.index(default_sheet)
            except ValueError:
                default_index = 0
            selected_sheet = st.selectbox("请选择班级 (Sheet)", sheet_names, index=default_index)
            
            if selected_sheet:
                df = utils.process_excel(uploaded_file, sheet=selected_sheet)
                exams = utils.get_exam_list(df)
                # 默认选中最后一个考试
                exam_idx = len(exams) - 1 if exams else 0
                sel_exam = st.selectbox("选择本次考试名称", exams, index=exam_idx)
                
                subjects = utils.get_subjects(df, sel_exam)
                # 默认尝试选中“数学”
                try:
                    sub_idx = subjects.index("数学")
                except ValueError:
                    sub_idx = 0
                sel_subject = st.selectbox("选择科目", subjects, index=sub_idx)

                # 数据预览
                score_df = utils.extract_scores(df, sel_exam, sel_subject)
                st.subheader("数据预览")
                st.dataframe(score_df, use_container_width=True, height=250)

                if st.button("💾 确认存入数据库", type="primary"):
                    database.insert_scores(
                        df=score_df,
                        exam_name=sel_exam,
                        subject=sel_subject,
                        class_name=selected_sheet,
                        school_year=sel_year
                    )
                    st.success(f"✅ {sel_year} - {selected_sheet} - {sel_exam} 数据已入库！")
                    time.sleep(5)
                    st.rerun()
        else:
            st.info("💡 提示：如有新成绩，请在此上传并存入数据库。")


    # === Tab 2: 成绩分析 (从数据库读) ===
    with tab2:
        st.header("📈 成绩可视化与深度分析")
        all_data = database.get_all_scores() 
        
        if all_data.empty:
            st.warning("数据库为空，请先导入数据。")
            st.stop()

        # 1. 筛选条件区 (可以放在 expander 里让界面更清爽)
        with st.expander("⚙️ 展开设置对比条件", expanded=True):
            c1, c2 = st.columns(2)
            sel_class = c1.selectbox("筛选班级", all_data['class'].unique())
            sel_sub = c2.selectbox("筛选科目", all_data[all_data['class']==sel_class]['subject'].unique())
            
            col_l, col_r = st.columns(2)
            y_c = col_l.selectbox("📍 本次学年", all_data['school_year'].unique(), key="yc")
            e_c = col_l.selectbox("本次考试", all_data[(all_data['school_year']==y_c)&(all_data['class']==sel_class)]['exam_name'].unique(), key="ec")
            
            y_p = col_r.selectbox("🔙 对比学年", all_data['school_year'].unique(), key="yp")
            e_p = col_r.selectbox("对比考试", all_data[(all_data['school_year']==y_p)&(all_data['class']==sel_class)]['exam_name'].unique(), key="ep")

        st.divider()

        # 2. 核心查询与数据组装
        df_curr = all_data[(all_data['school_year']==y_c) & (all_data['exam_name']==e_c) & (all_data['subject']==sel_sub)]
        # 防止选了同一场考试作为对比
        if (y_c == y_p) and (e_c == e_p):
            df_prev = None
        else:
            df_prev = all_data[(all_data['school_year']==y_p) & (all_data['exam_name']==e_p) & (all_data['subject']==sel_sub)]

        # 3. 业务处理与渲染输出
        analysis_res = analysis.get_full_analysis_context(df_curr, df_prev)
        
        if analysis_res:
            # A. 渲染核心指标和分布
            visuals.render_metrics(analysis_res['stats'], analysis_res.get('compare'))
            visuals.render_distribution(analysis_res['dist'])
            
            # B. 人数选择器
            st.write("---")
            c1, _ = st.columns([2, 3])
            display_opt = c1.selectbox(
                "🔢 选择展示的学生人数",
                options=["10", "20", "30", "全员"],
                index=0
            )

            # C. 并排渲染两个表
            full_comp = analysis_res['compare']['full_compare'] if analysis_res.get('compare') else None
            visuals.render_rank_tables(
                full_ranking=analysis_res['full_ranking'], 
                full_compare=full_comp,
                display_count=display_opt
            )
        else:
            st.error("无法分析选定数据，请确保本次考试有成绩录入。")


    # === Tab 3: 报告生成 (从数据库读) ===
    with tab3:
        st.header("📄 生成分析报告")
        
        # 这里的 meta 来源于你在 Tab 2 选中的那些 selectbox 变量
        meta_data = {
            "school_year": y_c,
            "exam_name": e_c,
            "subject": sel_sub
        }
        
        if st.button("🛠️ 立即构建 PDF 报告"):
            # 获取最新的分析数据
            res = analysis.get_full_analysis_context(df_curr, df_prev)
            
            if res:
                with st.spinner("正在排版并生成 PDF..."):
                    pdf_path = report_generator.generate_pdf_report(res, meta_data)
                    
                    with open(pdf_path, "rb") as f:
                        st.download_button(
                            label="📥 点击下载 PDF 报告",
                            data=f,
                            file_name=f"{meta_data['exam_name']}_{meta_data['subject']}_报告.pdf",
                            mime="application/pdf"
                        )
            else:
                st.error("数据不足，无法生成报告。")

    # === Tab 4: 数据库管理 ===
    with tab4:
        st.header("🗄️ 数据库内容管理")
        # 打印绝对路径（诊断用，之后可以删掉）
        st.write(f"当前程序读取的数据库位置: `{database.DB_PATH.absolute()}`")
        all_data = database.get_all_scores()
        if not all_data.empty:
            # 搜索与展示
            search = st.text_input("🔍 搜索姓名、学号、班级...", "")
            if search:
                all_data = all_data[
                    all_data['name'].str.contains(search) | 
                    all_data['student_id'].str.contains(search) |
                    all_data['class'].str.contains(search)
                ]
            st.dataframe(all_data, use_container_width=True, hide_index=True)
            
            if st.button("☠️ 清空所有数据"):
                database.delete_all()
                st.rerun()
        else:
            st.info("数据库目前是空的。")

if __name__ == "__main__":
    main()