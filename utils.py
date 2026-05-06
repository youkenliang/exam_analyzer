"""
utils.py

工具函数（文件读取、数据清洗）
"""

import pandas as pd


def clean_exam(exam):
    if pd.isna(exam):
        return ""
    exam = str(exam).strip()
    if exam.lower() == "nan":
        return ""
    if "班主任" in exam:
        return ""
    return exam


def clean_field(field):
    if pd.isna(field):
        return ""
    return str(field).strip().replace("\u3000", "")


def process_excel(file, sheet=0):
    df = pd.read_excel(file, sheet_name=sheet, header=[0, 1])

    df.columns = pd.MultiIndex.from_tuples([
        (clean_exam(exam), clean_field(field))
        for exam, field in df.columns
    ])

    return df


def get_exam_list(df):
    return sorted(set(df.columns.get_level_values(0)) - {""})


def get_subjects(df, exam):
    return sorted(
        df.loc[:, exam].columns
    )


def extract_scores(df, exam, subject):
    # 1. 统一清洗列名，防止类似 "数学 " 或 "数学.1" 的干扰
    # 我们直接通过索引位置或显式匹配来找
    
    try:
        # 获取基础信息（姓名、学号）
        # 注意：这里直接从原始 df 取，避免切片丢失索引
        student_id = df[("", "学号")]
        name = df[("", "姓名")]
        
        # 获取成绩信息
        # 使用 .xs (Cross-section) 是处理多级表头最稳妥的方法
        # 或者直接用简单的元组索引
        score = df[(exam, subject)]
        
        result = pd.DataFrame({
            "student_id": student_id,
            "name": name,
            "score": score
        })
        
        # 强制转为数值，无法转换的变 NaN
        result["score"] = pd.to_numeric(result["score"], errors="coerce")
        
        # 返回前去掉学号为空的行（可能是表格底部的备注行）
        return result.dropna(subset=["student_id"])

    except KeyError as e:
        # 这里的错误会通过 app.py 的 try-except 捕获并显示在 UI
        raise ValueError(f"架构匹配失败: 无法在考试 [{exam}] 中找到科目 [{subject}]。请检查表头是否有重复或空格。")