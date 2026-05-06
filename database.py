import sqlite3
from pathlib import Path
import pandas as pd
from typing import List

# 1. 绝对路径锁定
DB_PATH = Path(__file__).parent / "data" / "scores.db"

def get_connection() -> sqlite3.Connection:
    """获取数据库连接（确保目录存在）"""
    DB_PATH.parent.mkdir(exist_ok=True)
    return sqlite3.connect(DB_PATH)

def init_db() -> None:
    """初始化数据库并强制验证"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scores (
                school_year TEXT NOT NULL,
                student_id TEXT NOT NULL,
                name TEXT NOT NULL,
                class TEXT NOT NULL,
                subject TEXT NOT NULL,
                exam_name TEXT NOT NULL,
                score REAL NOT NULL,
                PRIMARY KEY (student_id, exam_name, subject)
            )
        """)
        conn.commit()
        
        # 物理检查
        cursor.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name='scores';")
        if cursor.fetchone()[0] > 0:
            print(f"✅ [数据库就绪]: {DB_PATH.absolute()}")
    except Exception as e:
        print(f"❌ [初始化异常]: {e}")
    finally:
        conn.close()


def insert_scores(df: pd.DataFrame, exam_name: str, subject: str, class_name: str, school_year: str) -> None:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        
        data = []
        for _, row in df.iterrows():
            raw_score = row['score']
            
            # --- 1. 学号处理：转为字符串并去掉 ".0" ---
            # 无论原始数据是 float 还是 int，统一转为干净的字符串
            sid = str(row['student_id']).split('.')[0].strip()
            
            # --- 2. 分数处理 ---
            try:
                val = float(row['score'])
                valid_score = val if not pd.isna(val) else -1.0
            except:
                valid_score = -1.0

            data.append((
                school_year,
                sid,
                str(row['name']).strip(),
                class_name, 
                subject,
                exam_name,
                valid_score,
            ))

        cursor.executemany("""
            INSERT OR REPLACE INTO scores (
                school_year, student_id, name, class, subject, exam_name, score
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, data)
        conn.commit()
        
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def get_all_scores() -> pd.DataFrame:
    conn = get_connection()
    try:
        # 显式查询，不使用 try-except 掩盖错误
        df = pd.read_sql_query("SELECT * FROM scores", conn)
        return df
    except Exception as e:
        # 如果报错，在 streamlit 终端或页面打印出具体错误
        print(f"读取数据库失败: {e}")
        # 返回带列名的空表，防止前端崩溃
        return pd.DataFrame(columns=['school_year', 'student_id', 'name', 'class', 'subject', 'exam_name', 'score'])
    finally:
        conn.close()



def delete_all():
    """清空所有数据（危险操作）"""
    conn = get_connection()
    try:
        conn.execute("DELETE FROM scores")
        conn.commit()
    finally:
        conn.close()

# 如果 app.py 里还用到了这个函数，记得保留
def get_exam_list() -> List[str]:
    try:
        conn = get_connection()
        res = conn.execute("SELECT DISTINCT exam_name FROM scores").fetchall()
        conn.close()
        return [r[0] for r in res]
    except:
        return []
    

def get_existing_tables() -> List[str]:
    """查询数据库中当前存在的所有表名"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        return tables
    finally:
        conn.close()



def get_scores_by_exam(exam_name: str) -> pd.DataFrame:
    """根据考试名称查询成绩"""
    conn = get_connection()
    try:
        df = pd.read_sql_query("SELECT * FROM scores WHERE exam_name = ?", conn, params=(exam_name,))
        return df
    except Exception as e:
        print(f"❌ [查询异常]: {e}")
        return pd.DataFrame()
    finally:
        conn.close()