import pandas as pd
import numpy as np

# =========================================================
# 1. 内部数据清洗工具
# =========================================================

def _get_valid_df(df: pd.DataFrame) -> pd.DataFrame:
    """过滤掉分数为 -1.0 的记录，确保统计数据真实有效"""
    if df is None or df.empty:
        return pd.DataFrame()
    return df[df["score"] != -1.0].copy()

# =========================================================
# 2. 核心统计逻辑
# =========================================================

def basic_stats(df: pd.DataFrame, pass_line: float = 60) -> dict:
    """计算本次考试的基础统计指标"""
    valid_df = _get_valid_df(df)
    if valid_df.empty:
        return {
            "平均分": 0, "最高分": 0, "最低分": 0, 
            "中位数": 0, "标准差": 0, "及格率": 0, "参考人数": 0
        }
    
    scores = valid_df["score"]
    return {
        "平均分": round(scores.mean(), 2),
        "最高分": float(scores.max()),
        "最低分": float(scores.min()),
        "中位数": round(scores.median(), 2),
        "标准差": round(scores.std(ddof=0), 2) if len(scores) > 1 else 0,
        "及格率": round((scores >= pass_line).mean() * 100, 2),
        "参考人数": int(scores.count())
    }

def score_distribution(df):
    """计算分数段分布（已调转顺序并加入中文标签）[cite: 2]"""
    valid_df = _get_valid_df(df)
    bins = [0, 60, 70, 80, 90, 101]
    # 定义标准标签
    labels = ["不及格", "及格 (60-69)", "中等 (70-79)", "良好 (80-89)", "优秀 (90+)"]
    valid_df["range"] = pd.cut(valid_df["score"], bins=bins, labels=labels, right=False)
    
    # 按照要求调转顺序：从优秀到不及格[cite: 2]
    target_order = ["优秀 (90+)", "良好 (80-89)", "中等 (70-79)", "及格 (60-69)", "不及格"]
    return valid_df["range"].value_counts().reindex(target_order).fillna(0).astype(int)

# =========================================================
# 3. 对比分析逻辑
# =========================================================

def compare_exams(df_old: pd.DataFrame, df_new: pd.DataFrame) -> pd.DataFrame:
    """对比两次考试，仅计算两次均参加且分数有效的学生"""
    v_old = _get_valid_df(df_old)
    v_new = _get_valid_df(df_new)
    
    # 使用 Inner Join 确保对比的公平性[cite: 2]
    merged = pd.merge(
        v_old[['student_id', 'name', 'score']],
        v_new[['student_id', 'score']],
        on="student_id",
        how="inner",
        suffixes=("_old", "_new")
    )
    
    merged["score_change"] = merged["score_new"] - merged["score_old"]
    # 排名变化计算：排名差 = 旧排名 - 新排名（正数代表进步）[cite: 2]
    merged["rank_old"] = merged["score_old"].rank(method="min", ascending=False)
    merged["rank_new"] = merged["score_new"].rank(method="min", ascending=False)
    merged["rank_change"] = merged["rank_old"] - merged["rank_new"]
    
    return merged

def get_top_improvements(compare_df: pd.DataFrame, n: int = 10):
    """获取进步最快的前 N 名学生[cite: 2]"""
    if compare_df.empty:
        return pd.DataFrame()
    return compare_df.sort_values("score_change", ascending=False).head(n)

# =========================================================
# 4. 综合数据包装器 (供 app.py 和 report 调用)
# =========================================================

def get_full_analysis_context(df_curr: pd.DataFrame, df_prev: pd.DataFrame = None):
    """
    聚合所有计算结果为一个字典。
    这种结构非常方便后续直接传递给 PDF 生成器。
    """
    if df_curr.empty:
        return None
    
    valid_curr = _get_valid_df(df_curr)
    valid_curr['rank'] = valid_curr['score'].rank(method='min', ascending=False).astype(int)
    full_ranking = valid_curr.sort_values('rank')
    
    context = {
        "stats": basic_stats(df_curr),
        "dist": score_distribution(df_curr),
        "full_ranking": full_ranking, 
        "compare": None
    }
    
    if df_prev is not None and not df_prev.empty:
        comp_df = compare_exams(df_prev, df_curr)
        # 同样确保对比表中的分数也是整数
        comp_df['score_old'] = comp_df['score_old'].astype(int)
        comp_df['score_new'] = comp_df['score_new'].astype(int)
        comp_df['score_change'] = comp_df['score_change'].astype(int)
        
        full_compare = comp_df.sort_values("score_change", ascending=False)
        context["compare"] = {
            "full_compare": full_compare,
            "avg_diff": round(context["stats"]["平均分"] - basic_stats(df_prev)["平均分"], 2),
            "pass_diff": round(context["stats"]["及格率"] - basic_stats(df_prev)["及格率"], 2),
        }
    return context