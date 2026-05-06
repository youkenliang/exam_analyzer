import streamlit as st
import pandas as pd
import plotly.express as px

def render_metrics(stats, compare_data=None):
    """渲染顶部核心指标看板"""
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("📌 参考人数", f"{stats['参考人数']}人")
    m4.metric("🏆 最高分", f"{stats['最高分']}")
    
    if compare_data:
        m2.metric("📊 平均分", f"{stats['平均分']}", delta=f"{compare_data['avg_diff']}")
        m3.metric("🎯 及格率", f"{stats['及格率']}%", delta=f"{compare_data['pass_diff']}%")
    else:
        m2.metric("📊 平均分", f"{stats['平均分']}")
        m3.metric("🎯 及格率", f"{stats['及格率']}%")


def render_distribution(dist_series):
    """渲染分数分布（表格 + 科学色调横向柱状图）"""
    st.markdown("### 📊 分数分布细节")
    
    # 构造展示用的 DataFrame
    dist_df = pd.DataFrame({
        "分数等级": dist_series.index,
        "人数": dist_series.values
    })

    col1, col2 = st.columns([1, 2])
    with col1:
        # 显示明细表
        st.dataframe(dist_df, use_container_width=True, hide_index=True)
        
    with col2:
        # 绘图：设置 y 轴顺序为分类顺序，确保“优秀”在顶部
        fig = px.bar(
            dist_df, x="人数", y="分数等级", orientation='h',
            text="人数", color="人数", 
            color_continuous_scale="Teal", # 科学色调
            category_orders={"分数等级": list(dist_series.index)} 
        )
        fig.update_layout(
            template="plotly_white", 
            height=300, 
            margin=dict(l=0, r=0, t=10, b=0),
            xaxis_title="人数", 
            yaxis_title="",
            coloraxis_showscale=False # 隐藏侧边色条使界面更干净
        )
        st.plotly_chart(fig, use_container_width=True)




def render_rank_tables(full_ranking, full_compare=None, display_count="10"):
    """
    并排渲染排名表和进退步表，支持自定义人数
    """
    # 1. 确定截取长度
    is_all = display_count == "全员"
    limit = len(full_ranking) if is_all else int(display_count)
    
    st.write("---")
    st.markdown(f"### 🏆 荣誉榜单")
    
    col1, col2 = st.columns(2)
    
    # --- 左侧：考试排名表 ---
    with col1:
        st.markdown(f"**🌟 本次考试 TOP {display_count}**")
        df_rank = full_ranking.head(limit)[["rank", "name", "score"]]
        
        # 统一重命名提高可读性
        rank_display = df_rank.rename(columns={"rank": "名次", "name": "姓名", "score": "分数"})
        
        st.dataframe(rank_display, use_container_width=True, hide_index=True)


    # --- 右侧：进退步明细表 ---
    with col2:
        st.markdown(f"**🚀 进步最快 TOP {display_count}**")
        if full_compare is not None and not full_compare.empty:
            df_comp = full_compare.head(limit)[["name", "score_old", "score_new", "score_change"]]
            
            # 统一重命名
            comp_display = df_comp.rename(columns={
                "name": "姓名", "score_old": "上次", "score_new": "本次", "score_change": "进步"
            })
            st.dataframe(comp_display, use_container_width=True, hide_index=True)

        else:
            st.info("ℹ️ 暂无对比数据。")