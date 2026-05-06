import os
from fpdf import FPDF
import datetime

class ExamReport(FPDF):
    def header(self):
        # 顶部深色背景
        self.set_fill_color(0, 102, 102) # 稍微深一点的青色
        self.rect(0, 0, 210, 35, 'F')
        self.set_text_color(255, 255, 255)
        self.set_font("NotoSerif", "", 20)
        self.set_y(12)
        self.cell(0, 10, "学 业 质 量 监 测 分 析 报 告", ln=True, align="C")
        self.set_text_color(0, 0, 0)

    def footer(self):
        self.set_y(-15)
        self.set_font("NotoSerif", "", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"Page {self.page_no()} | AI 数据分析系统", align="C")

def generate_pdf_report(analysis_res, meta_info, output_filename="report.pdf"):
    pdf = ExamReport()
    
    # 1. 字体注册
    font_path = os.path.join(os.path.dirname(__file__), "fonts", "NotoSerifSC-Regular.ttf")
    if not os.path.exists(font_path):
        font_path = "/System/Library/Fonts/Supplemental/Songti.ttc"
    pdf.add_font("NotoSerif", "", font_path)
    pdf.add_page()

    # --- 第一部分：基本信息 ---
    pdf.set_y(40)
    pdf.set_font("NotoSerif", "", 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 5, f"学年: {meta_info['school_year']} | 考试: {meta_info['exam_name']} | 科目: {meta_info['subject']}", ln=True)
    pdf.ln(5)

    # --- 第二部分：核心指标卡片 ---
    stats = analysis_res['stats']
    card_w = (pdf.epw) / 4
    curr_x, curr_y = pdf.get_x(), pdf.get_y()
    
    metrics = [("👥参考人数", f"{stats['参考人数']}"), ("📈平均分", f"{stats['平均分']}"), 
               ("✅及格率", f"{stats['及格率']}%"), ("🏆最高分", f"{stats['最高分']}")]

    for label, val in metrics:
        pdf.set_fill_color(245, 250, 250)
        pdf.rect(curr_x, curr_y, card_w-2, 22, 'F')
        pdf.set_xy(curr_x, curr_y + 4)
        pdf.set_text_color(0, 102, 102)
        pdf.cell(card_w-2, 5, label, align='C', ln=0)
        pdf.set_xy(curr_x, curr_y + 11)
        pdf.set_font("NotoSerif", "", 14)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(card_w-2, 8, val, align='C', ln=0)
        curr_x += card_w
    
    pdf.ln(25)

    # --- 第三部分：分数分布与模型柱状图 (重点补全) ---
    pdf.set_font("NotoSerif", "", 12)
    pdf.cell(0, 10, "📊 分数段分布细节", ln=True)
    pdf.ln(2)

    dist = analysis_res['dist']
    total_students = stats['参考人数'] if stats['参考人数'] > 0 else 1
    
    # 定义分布栏的起始位置
    table_x = pdf.get_x()
    col_label_w, col_count_w, col_bar_w = 30, 25, 130 # 列表宽度分配

    # 表头
    pdf.set_font("NotoSerif", "", 9)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(col_label_w, 8, " 分数区间", border=1, fill=True)
    pdf.cell(col_count_w, 8, " 人数", border=1, fill=True)
    pdf.cell(col_bar_w, 8, " 分布模型柱状图", border=1, fill=True)
    pdf.ln()

    # 循环分数段数据
    for label, count in dist.items():
        percentage = (count / total_students * 100)
        
        # 1. 标签列
        pdf.cell(col_label_w, 10, f" {label}", border=1)
        # 2. 人数列
        pdf.cell(col_count_w, 10, f" {count} 人", border=1)
        
        # 3. 柱状图列 (在单元格内手动绘制矩形)
        curr_pos_x = pdf.get_x()
        curr_pos_y = pdf.get_y()
        
        # 先画一个空框
        pdf.cell(col_bar_w, 10, "", border=1) 
        
        # 计算柱状子条的长度 (最大长度 120mm)
        bar_max_w = 120
        bar_val_w = (percentage / 100) * bar_max_w
        
        # 填充颜色 (根据浓度变化：及格以上用青色，以下用灰色)
        if "及格" in label or "优秀" in label: pdf.set_fill_color(0, 153, 153)
        else: pdf.set_fill_color(180, 180, 180)
            
        # 绘制进度条矩形 (居中对齐一点)
        if bar_val_w > 0:
            pdf.rect(curr_pos_x + 5, curr_pos_y + 3, bar_val_w, 4, 'F')
        
        # 标注百分比文字
        pdf.set_xy(curr_pos_x + bar_val_w + 7, curr_pos_y)
        pdf.set_font("NotoSerif", "", 8)
        pdf.cell(20, 10, f"{percentage:.1f}%")
        
        pdf.set_xy(table_x, curr_pos_y + 10) # 换行回起始位置

    pdf.ln(10)

    # --- 第四部分：双榜单 Top 10 ---
    pdf.set_font("NotoSerif", "", 12)
    pdf.set_draw_color(0, 102, 102)
    pdf.cell(0, 10, "🏆 卓越与飞跃榜单", border="B", ln=True)
    pdf.ln(5)

    col_w = (pdf.epw - 10) / 2
    top_10 = analysis_res['full_ranking'].head(10)
    compare_data = analysis_res.get('compare')

    for i in range(10):
        # 左侧排名
        l_text = f"No.{i+1} {top_10.iloc[i]['name']} ({int(top_10.iloc[i]['score'])}分)" if i < len(top_10) else "-"
        pdf.set_fill_color(252, 252, 252) if i % 2 == 0 else pdf.set_fill_color(255, 255, 255)
        pdf.set_font("NotoSerif", "", 9)
        pdf.cell(col_w, 9, l_text, border='B', fill=True)
        
        pdf.set_x(pdf.get_x() + 10)
        
        # 右侧进步
        if compare_data and i < len(compare_data['full_compare']):
            c_row = compare_data['full_compare'].iloc[i]
            r_text = f"🚀 {c_row['name']} 提升 +{int(c_row['score_change'])} 分"
        else:
            r_text = "-"
        pdf.cell(col_w, 9, r_text, border='B', fill=True)
        pdf.ln()

    # 导出
    pdf.output(output_filename)
    return output_filename