import streamlit as st
import akshare as ak
import plotly.express as px
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time

# 缓存数据获取函数（减少重复请求）
@st.cache_data(ttl=3600)
def get_board_data():
    board_df = ak.stock_board_industry_name_em()

    data_list = []
    for index, row in board_df.iterrows():
        try:
            df = ak.stock_board_industry_hist_em(
                symbol = row["板块名称"],
                start_date = (datetime.now() - timedelta(days=7)).strftime("%Y%m%d"),
                end_date = datetime.now().strftime("%Y%m%d"),
                adjust = ""
            )
            latest = df.iloc[-1].to_dict()
            latest["板块名称"] = row["板块名称"]
            data_list.append(latest)
        except Exception as e:
            continue

    return pd.DataFrame(data_list)

# 获取A股股票列表
@st.cache_data(ttl=86400)  # 缓存24小时
def get_stock_list():
    """
    获取A股股票列表
    """
    try:
        # 主要方法：使用akshare获取
        stock_list = ak.stock_info_a_code_name()
        
        # 检查并标准化列名
        cols = stock_list.columns.tolist()
        column_mapping = {}
        
        # 查找可能的"代码"列
        for col in cols:
            if '代码' in col or 'code' in col.lower() or 'symbol' in col.lower():
                column_mapping[col] = '代码'
                break
        
        # 查找可能的"名称"列
        for col in cols:
            if '名称' in col or 'name' in col.lower() or '简称' in col:
                column_mapping[col] = '名称'
                break
        
        # 重命名列
        if column_mapping:
            stock_list = stock_list.rename(columns=column_mapping)
        
        # 验证列是否存在，若不存在则尝试其他方法
        if '代码' not in stock_list.columns or '名称' not in stock_list.columns:
            raise KeyError("未找到'代码'或'名称'列")
            
        # 成功获取后保存到本地作为备份
        if not stock_list.empty:
            stock_list.to_csv('stock_list_backup.csv', index=False)
        
        return stock_list
    except Exception as e:
        st.warning(f"通过akshare获取股票列表失败: {e}")
    
    # 尝试备用方法1：使用不同的akshare接口
    try:
        # 使用另一个akshare接口
        stock_list = ak.stock_zh_a_spot_em()
        if not stock_list.empty:
            # 检查并调整列名
            if '代码' in stock_list.columns and '名称' in stock_list.columns:
                # 如果已经有正确的列名，只保留这两列
                stock_list = stock_list[['代码', '名称']]
            else:
                # 尝试查找并重命名
                cols = stock_list.columns.tolist()
                # 查找代码列
                code_col = None
                for col in cols:
                    if '代码' in col or 'code' in col.lower() or 'symbol' in col.lower():
                        code_col = col
                        break
                
                # 查找名称列
                name_col = None
                for col in cols:
                    if '名称' in col or 'name' in col.lower() or '简称' in col:
                        name_col = col
                        break
                
                if code_col and name_col:
                    # 重命名并只保留这两列
                    stock_list = stock_list.rename(columns={code_col: '代码', name_col: '名称'})
                    stock_list = stock_list[['代码', '名称']]
                else:
                    # 如果找不到合适的列，使用前两列并重命名
                    first_two_cols = stock_list.columns[:2].tolist()
                    stock_list = stock_list.rename(columns={
                        first_two_cols[0]: '代码',
                        first_two_cols[1]: '名称'
                    })
                    stock_list = stock_list[['代码', '名称']]
            
            stock_list.to_csv('stock_list_backup.csv', index=False)
            return stock_list
    except Exception as e:
        st.warning(f"通过备用akshare接口获取股票列表失败: {e}")
    
    # 尝试备用方法2：使用本地文件
    try:
        st.info("正在使用本地备份的股票列表数据...")
        stock_list = pd.read_csv('stock_list_backup.csv')
        if not stock_list.empty:
            # 确保列名正确
            if '代码' in stock_list.columns and '名称' in stock_list.columns:
                return stock_list
            else:
                # 尝试重命名列
                cols = stock_list.columns.tolist()
                if len(cols) >= 2:
                    stock_list = stock_list.rename(columns={
                        cols[0]: '代码',
                        cols[1]: '名称'
                    })
                    return stock_list
    except Exception as e:
        st.warning(f"读取本地备份股票列表失败: {e}")
    
    # 最后的备选方案：使用硬编码的常用股票列表
    st.error("无法获取完整股票列表，将使用有限的股票列表")
    # 提供一些常用股票作为最低限度的备选
    default_stocks = [
        {"代码": "000001", "名称": "平安银行"},
        {"代码": "000002", "名称": "万科A"},
        {"代码": "000063", "名称": "中兴通讯"},
        {"代码": "000333", "名称": "美的集团"},
        {"代码": "000651", "名称": "格力电器"},
        {"代码": "000858", "名称": "五粮液"},
        {"代码": "002415", "名称": "海康威视"},
        {"代码": "600000", "名称": "浦发银行"},
        {"代码": "600036", "名称": "招商银行"},
        {"代码": "600276", "名称": "恒瑞医药"},
        {"代码": "600519", "名称": "贵州茅台"},
        {"代码": "601318", "名称": "中国平安"},
        {"代码": "601857", "名称": "中国石油"},
        {"代码": "601398", "名称": "工商银行"},
        {"代码": "601988", "名称": "中国银行"},
        {"代码": "603288", "名称": "海天味业"},
        {"代码": "601888", "名称": "中国中免"},
        {"代码": "600050", "名称": "中国联通"},
        {"代码": "600009", "名称": "上海机场"},
        {"代码": "688981", "名称": "中芯国际"}
    ]
    return pd.DataFrame(default_stocks)

# 获取个股K线数据
@st.cache_data(ttl=3600)
def get_stock_data(stock_code, start_date, end_date):
    try:
        df = ak.stock_zh_a_hist(symbol=stock_code, start_date=start_date, end_date=end_date, adjust="qfq")
        return df
    except Exception as e:
        st.error(f"获取股票数据失败: {e}")
        return pd.DataFrame()

# 获取个股基本面数据
@st.cache_data(ttl=86400)
def get_stock_fundamental(stock_code):
    try:
        # 主要财务指标
        financial = ak.stock_financial_analysis_indicator(symbol=stock_code)
        # 获取最新一期数据
        if not financial.empty:
            latest_financial = financial.iloc[0]
        else:
            latest_financial = pd.Series()
            
        # 获取市盈率、市净率等指标
        stock_info = ak.stock_a_lg_indicator(symbol=stock_code)
        
        # 合并数据
        result = {
            "股票代码": stock_code,
            "市盈率(动态)": stock_info.loc[stock_info['指标名称'] == '市盈率(动态)', '最新值'].values[0] if not stock_info.empty else None,
            "市净率": stock_info.loc[stock_info['指标名称'] == '市净率', '最新值'].values[0] if not stock_info.empty else None,
            "ROE": latest_financial.get('净资产收益率加权(%)') if not latest_financial.empty else None,
            "营收增长率(%)": latest_financial.get('营业收入同比增长率(%)') if not latest_financial.empty else None,
            "净利润增长率(%)": latest_financial.get('净利润同比增长率(%)') if not latest_financial.empty else None,
        }
        return pd.DataFrame([result])
    except Exception as e:
        st.warning(f"获取基本面数据失败: {e}")
        return pd.DataFrame(columns=["股票代码", "市盈率(动态)", "市净率", "ROE", "营收增长率(%)", "净利润增长率(%)"])

# 计算技术指标
def calculate_indicators(df):
    if df.empty:
        return df
    
    # 确保必要的列存在
    required_cols = ['收盘', '开盘', '最高', '最低', '成交量']
    if not all(col in df.columns for col in required_cols):
        return df
    
    # 计算MA
    df['MA5'] = df['收盘'].rolling(5).mean()
    df['MA10'] = df['收盘'].rolling(10).mean()
    df['MA20'] = df['收盘'].rolling(20).mean()
    
    # 计算MACD
    df['EMA12'] = df['收盘'].ewm(span=12, adjust=False).mean()
    df['EMA26'] = df['收盘'].ewm(span=26, adjust=False).mean()
    df['DIF'] = df['EMA12'] - df['EMA26']
    df['DEA'] = df['DIF'].ewm(span=9, adjust=False).mean()
    df['MACD'] = 2 * (df['DIF'] - df['DEA'])
    
    # 计算KDJ
    low_9 = df['最低'].rolling(window=9).min()
    high_9 = df['最高'].rolling(window=9).max()
    df['RSV'] = (df['收盘'] - low_9) / (high_9 - low_9) * 100
    df['K'] = df['RSV'].ewm(alpha=1/3, adjust=False).mean()
    df['D'] = df['K'].ewm(alpha=1/3, adjust=False).mean()
    df['J'] = 3 * df['K'] - 2 * df['D']
    
    # 计算RSI
    delta = df['收盘'].diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    ema_up = up.ewm(com=13, adjust=False).mean()
    ema_down = down.ewm(com=13, adjust=False).mean()
    rs = ema_up / ema_down
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # 计算威廉WR指标(窗口期21，使用滚动均值)
    # 计算21日滚动窗口内的最高价和最低价的均值
    highest_high_21_mean = df['最高'].rolling(window=21).mean()
    lowest_low_21_mean = df['最低'].rolling(window=21).mean()
    
    # 使用均值计算威廉WR指标
    df['WR21'] = -100 * (highest_high_21_mean - df['收盘']) / (highest_high_21_mean - lowest_low_21_mean)
    
    return df

# 数据处理函数
def process_data(df):
    numeric_cols = ['开盘','收盘','最高','最低','成交量','成交额','振幅','涨跌幅','换手率']
    df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce')

    df['量价强度'] = df['涨跌幅'] * df['换手率']
    df['成交额（亿）'] = df['成交额'] / 1e8
    df['成交量（万手）'] = df['成交量'] / 10000
    df['涨跌幅'] = df['涨跌幅'] * 100 # 确保为百分比值
    # 新增四舍五入处理（保留两位小数）
    round_cols = ['涨跌幅', '换手率', '量价强度', '成交额（亿）', '成交量（万手）']
    df[round_cols] = df[round_cols].round(0)
    df['涨跌幅'] = df['涨跌幅'] / 100  # 确保为百分比值
    return df.dropna(subset=['涨跌幅'])

# 选股功能
def filter_stocks(pe_min, pe_max, pb_min, pb_max, roe_min, growth_min, max_stocks=200):
    st.info("正在筛选股票，请稍候...")
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # 获取股票列表
    stock_list = get_stock_list()
    
    if stock_list.empty:
        st.error("无法获取股票列表，选股功能无法继续")
        return pd.DataFrame()
    
    # 限制处理的股票数量以提高性能
    if len(stock_list) > max_stocks:
        st.warning(f"为提高性能，将只筛选前 {max_stocks} 只股票")
        stock_list = stock_list.head(max_stocks)
    
    filtered_stocks = []
    total_stocks = len(stock_list)
    processed_count = 0
    error_count = 0
    
    for i, (_, row) in enumerate(stock_list.iterrows()):
        # 更新进度条和状态
        progress = min(i / total_stocks, 1.0)
        progress_bar.progress(progress)
        processed_count += 1
        
        if i % 5 == 0:  # 每处理5只股票更新一次状态
            status_text.text(f"已处理: {processed_count}/{total_stocks} | 符合条件: {len(filtered_stocks)} | 错误: {error_count}")
        
        try:
            stock_code = row['代码']
            # 获取基本面数据
            fund_data = get_stock_fundamental(stock_code)
            
            if fund_data.empty:
                continue
                
            # 应用筛选条件，增加健壮性检查
            valid_data = True
            required_fields = ['市盈率(动态)', '市净率', 'ROE', '营收增长率(%)', '净利润增长率(%)']
            
            # 检查是否所有必需字段都存在且不是NaN
            for field in required_fields:
                if field not in fund_data.columns or pd.isna(fund_data.iloc[0][field]):
                    valid_data = False
                    break
            
            if valid_data:
                pe = float(fund_data.iloc[0]['市盈率(动态)'])
                pb = float(fund_data.iloc[0]['市净率'])
                roe = float(fund_data.iloc[0]['ROE'])
                growth = float(fund_data.iloc[0]['营收增长率(%)'])
                
                # 排除负值和异常值
                if pe < 0 or pb < 0 or pe > 2000 or pb > 100:
                    continue
                
                if (pe_min <= pe <= pe_max or pe_min == pe_max == 0) and \
                   (pb_min <= pb <= pb_max or pb_min == pb_max == 0) and \
                   roe >= roe_min and growth >= growth_min:
                    filtered_stocks.append({
                        "代码": stock_code,
                        "名称": row['名称'],
                        "市盈率": pe,
                        "市净率": pb,
                        "ROE(%)": roe,
                        "营收增长率(%)": growth,
                        "净利润增长率(%)": fund_data.iloc[0]['净利润增长率(%)']
                    })
            
            # 为避免频繁请求导致API限制，添加短暂延迟
            if i % 10 == 0 and i > 0:
                time.sleep(0.5)
                
        except Exception as e:
            error_count += 1
            # 如果错误太多，提前终止
            if error_count > 20:
                st.warning("遇到过多错误，提前终止筛选")
                break
            continue
    
    progress_bar.progress(1.0)
    status_text.text(f"筛选完成，共找到 {len(filtered_stocks)} 只符合条件的股票")
    
    if not filtered_stocks:
        st.warning("没有找到符合条件的股票，请尝试放宽筛选条件")
        return pd.DataFrame()
    
    return pd.DataFrame(filtered_stocks)

# 绘制K线图
def plot_candlestick(df):
    if df.empty:
        return go.Figure()
    
    # 创建蜡烛图
    fig = go.Figure()
    
    # 添加K线图
    fig.add_trace(go.Candlestick(
        x=df['日期'],
        open=df['开盘'],
        high=df['最高'],
        low=df['最低'],
        close=df['收盘'],
        name='K线'
    ))
    
    # 添加MA线
    if 'MA5' in df.columns:
        fig.add_trace(go.Scatter(
            x=df['日期'],
            y=df['MA5'],
            mode='lines',
            name='MA5',
            line=dict(color='blue', width=1)
        ))
    
    if 'MA10' in df.columns:
        fig.add_trace(go.Scatter(
            x=df['日期'],
            y=df['MA10'],
            mode='lines',
            name='MA10',
            line=dict(color='orange', width=1)
        ))
    
    if 'MA20' in df.columns:
        fig.add_trace(go.Scatter(
            x=df['日期'],
            y=df['MA20'],
            mode='lines',
            name='MA20',
            line=dict(color='purple', width=1)
        ))
    
    # 设置图表布局
    fig.update_layout(
        title='K线图表',
        xaxis_title='日期',
        yaxis_title='价格',
        xaxis_rangeslider_visible=False,
        height=500
    )
    
    return fig

# 绘制成交量图
def plot_volume(df):
    if df.empty:
        return go.Figure()
    
    colors = ['red' if row['收盘'] - row['开盘'] >= 0 else 'green' for _, row in df.iterrows()]
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df['日期'],
        y=df['成交量'],
        marker_color=colors,
        name='成交量'
    ))
    
    fig.update_layout(
        title='成交量',
        xaxis_title='日期',
        yaxis_title='成交量',
        height=200
    )
    
    return fig

# 主程序
def main():
    st.set_page_config(
        page_title="股票分析平台",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # 创建选项卡
    tab1, tab2, tab3 = st.tabs(["板块热力图", "个股分析", "选股工具"])
    
    # 热力图选项卡
    with tab1:
        st.title("📈 实时板块资金流向热力图")
        st.markdown("""
        **数据说明：**
        - 颜色映射：绿色表示下跌，红色表示上涨
        - 数据更新：{}
        """.format(datetime.now().strftime("%Y-%m-%d %H:%M")))

        # 侧边栏控件
        col1, col2 = st.columns(2)
        with col1:
            color_metric = st.selectbox(
                "颜色指标",
                options=['涨跌幅','换手率','量价强度'],
                index=0,
                key="heatmap_color"
            )
            size_metric = st.selectbox(
                "板块大小指标",
                options=['成交额（亿）','成交量（万手）','换手率'],
                index=0,
                key="heatmap_size"
            )
        with col2:
            date_range = st.slider(
                "回溯天数",
                min_value=1,
                max_value=30,
                value=7,
                key="heatmap_days"
            )
            color_scale = st.selectbox(
                "配色方案",
                options=['RdYlGn_r','BrBG_r','PiYG_r','RdBu_r'], # 全部使用反转色阶
                index=0,
                key="heatmap_color_scale"
            )

        # 数据加载
        with st.spinner('正在获取最新行情数据...'):
            raw_df = get_board_data()
            processed_df = process_data(raw_df)

        # 数据过滤
        filtered_df = processed_df[
            processed_df['日期'] >= (datetime.now() - timedelta(days=date_range)).strftime("%Y-%m-%d")
            ]

        # 创建可视化
        fig = px.treemap(
            filtered_df,
            path=['板块名称'],
            values=size_metric,
            color=color_metric,
            color_continuous_scale=color_scale,
            range_color=[filtered_df[color_metric].min(), filtered_df[color_metric].max()],
            hover_data={
                '涨跌幅':':.2f%',
                '换手率':':.2f%',
                '成交额（亿）':':.2f',
                '量价强度':':.2f'
            },
            height=600
        )

        # 样式调整
        fig.update_layout(
            margin=dict(t=0, l=0, r=0, b=0),
            coloraxis_colorbar=dict(
                title=color_metric + (" (%)"if color_metric =="涨跌幅"else""),
                tickformat=".1f"if color_metric =="涨跌幅"else".1f",
                thickness=15
            )
        )

        fig.update_traces(
            texttemplate='%{label} %{customdata[0]:.2f} % ',
            hovertemplate = ('<b>%{label}</b>'
                f'{color_metric}: %{{color:.2f}}{"%" if color_metric == "涨跌幅" else ""}'
                '换手率: %{customdata[1]:.2f}%'
                '成交额: %{customdata[2]:.2f}亿'
            )
        )

        st.plotly_chart(fig, use_container_width=True)

        # 数据表格
        with st.expander("查看原始数据"):
            st.dataframe(
                filtered_df.sort_values(by='涨跌幅', ascending=False),
                column_config={
                    "日期":"日期",
                    "板块名称": st.column_config.TextColumn(width="large"),
                    "涨跌幅": st.column_config.NumberColumn(format="▁%.2f%%",help="颜色映射："),
                    "换手率": st.column_config.NumberColumn(format="%.2f%%"),
                    "成交额（亿）": st.column_config.NumberColumn(format="%.1f 亿")
                },
                height=300,
                hide_index=True
            )

    # 个股分析选项卡
    with tab2:
        st.title("🔍 个股详细分析")
        
        # 获取股票列表用于搜索
        with st.spinner("正在加载股票列表..."):
            stock_list = get_stock_list()
        
        if stock_list.empty:
            st.error("无法获取股票列表，请检查网络连接或刷新页面重试")
            st.stop()
        
        # 创建股票代码和名称的映射字典
        stock_dict = dict(zip(stock_list['名称'], stock_list['代码']))
        
        # 股票选择组件
        col1, col2 = st.columns([3, 1])
        with col1:
            # 添加手动输入股票代码的选项
            input_option = st.radio(
                "选择输入方式",
                options=["从列表选择", "手动输入代码"],
                index=0,
                horizontal=True,
                key="input_method"
            )
            
            if input_option == "从列表选择":
                # 从列表选择股票
                selected_stock = st.selectbox(
                    "选择股票",
                    options=list(stock_dict.keys()),
                    key="stock_selector"
                )
                if selected_stock:
                    stock_code = stock_dict[selected_stock]
            else:
                # 手动输入股票代码
                stock_code = st.text_input(
                    "输入股票代码（如：000001）",
                    key="manual_stock_code"
                )
                selected_stock = None
                # 验证输入的股票代码
                if stock_code:
                    # 尝试在列表中找到对应名称
                    matching_stocks = stock_list[stock_list['代码'] == stock_code]
                    if not matching_stocks.empty:
                        selected_stock = matching_stocks.iloc[0]['名称']
                    else:
                        selected_stock = "未知股票"
        
        with col2:
            days = st.number_input(
                "数据周期(天)",
                min_value=5,
                max_value=365,
                value=60,
                key="stock_days"
            )
        
        # 处理股票数据
        if (selected_stock and input_option == "从列表选择") or (stock_code and input_option == "手动输入代码"):
            # 确保stock_code是有效的
            if input_option == "从列表选择":
                stock_code = stock_dict[selected_stock]
            
            # 显示股票名称和代码
            st.subheader(f"{selected_stock or '股票'} ({stock_code})")
            
            start_date = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")
            end_date = datetime.now().strftime("%Y%m%d")
            
            # 获取并处理数据
            with st.spinner(f"正在获取 {selected_stock or stock_code} 数据..."):
                try:
                    stock_data = get_stock_data(stock_code, start_date, end_date)
                    if not stock_data.empty:
                        # 计算技术指标
                        stock_data = calculate_indicators(stock_data)
                except Exception as e:
                    st.error(f"获取数据时出错: {e}")
                    stock_data = pd.DataFrame()
            
            if not stock_data.empty:
                # 创建指标选择行
                indicator_col1, indicator_col2 = st.columns(2)
                with indicator_col1:
                    selected_indicators = st.multiselect(
                        "选择技术指标",
                        options=["MACD", "KDJ", "RSI", "WR21"],
                        default=["MACD"],
                        key="tech_indicators"
                    )
                
                # 创建K线图
                k_fig = plot_candlestick(stock_data)
                st.plotly_chart(k_fig, use_container_width=True)
                
                # 创建成交量图
                vol_fig = plot_volume(stock_data)
                st.plotly_chart(vol_fig, use_container_width=True)
                
                # 创建技术指标图
                if "MACD" in selected_indicators:
                    macd_fig = go.Figure()
                    macd_fig.add_trace(go.Scatter(x=stock_data['日期'], y=stock_data['DIF'], mode='lines', name='DIF'))
                    macd_fig.add_trace(go.Scatter(x=stock_data['日期'], y=stock_data['DEA'], mode='lines', name='DEA'))
                    
                    # 添加MACD柱状图
                    colors = ['red' if val >= 0 else 'green' for val in stock_data['MACD']]
                    macd_fig.add_trace(go.Bar(x=stock_data['日期'], y=stock_data['MACD'], name='MACD', marker_color=colors))
                    
                    macd_fig.update_layout(title='MACD指标', height=200)
                    st.plotly_chart(macd_fig, use_container_width=True)
                    
                if "KDJ" in selected_indicators:
                    kdj_fig = go.Figure()
                    kdj_fig.add_trace(go.Scatter(x=stock_data['日期'], y=stock_data['K'], mode='lines', name='K'))
                    kdj_fig.add_trace(go.Scatter(x=stock_data['日期'], y=stock_data['D'], mode='lines', name='D'))
                    kdj_fig.add_trace(go.Scatter(x=stock_data['日期'], y=stock_data['J'], mode='lines', name='J'))
                    
                    kdj_fig.update_layout(title='KDJ指标', height=200)
                    st.plotly_chart(kdj_fig, use_container_width=True)
                    
                if "RSI" in selected_indicators:
                    rsi_fig = go.Figure()
                    rsi_fig.add_trace(go.Scatter(x=stock_data['日期'], y=stock_data['RSI'], mode='lines', name='RSI'))
                    
                    # 添加参考线
                    rsi_fig.add_shape(type="line", x0=stock_data['日期'].iloc[0], y0=80, x1=stock_data['日期'].iloc[-1], y1=80,
                                      line=dict(color="red", width=1, dash="dash"))
                    rsi_fig.add_shape(type="line", x0=stock_data['日期'].iloc[0], y0=20, x1=stock_data['日期'].iloc[-1], y1=20,
                                      line=dict(color="green", width=1, dash="dash"))
                    
                    rsi_fig.update_layout(title='RSI指标', height=200)
                    st.plotly_chart(rsi_fig, use_container_width=True)
                
                if "WR21" in selected_indicators:
                    wr_fig = go.Figure()
                    wr_fig.add_trace(go.Scatter(x=stock_data['日期'], y=stock_data['WR21'], mode='lines', name='WR(21日均值)'))
                    
                    # 添加超买超卖参考线
                    wr_fig.add_shape(type="line", x0=stock_data['日期'].iloc[0], y0=-20, x1=stock_data['日期'].iloc[-1], y1=-20,
                                    line=dict(color="red", width=1, dash="dash"))
                    wr_fig.add_shape(type="line", x0=stock_data['日期'].iloc[0], y0=-80, x1=stock_data['日期'].iloc[-1], y1=-80,
                                    line=dict(color="green", width=1, dash="dash"))
                    
                    wr_fig.update_layout(title='威廉WR指标(21日均值)', height=200)
                    st.plotly_chart(wr_fig, use_container_width=True)
                
                # 显示基本面数据
                if not fund_data.empty:
                    st.subheader("基本面数据")
                    
                    # 创建基本面指标展示
                    metric_cols = st.columns(5)
                    
                    with metric_cols[0]:
                        st.metric("市盈率", f"{fund_data.iloc[0]['市盈率(动态)']:.2f}")
                    
                    with metric_cols[1]:
                        st.metric("市净率", f"{fund_data.iloc[0]['市净率']:.2f}")
                    
                    with metric_cols[2]:
                        st.metric("ROE(%)", f"{fund_data.iloc[0]['ROE']:.2f}")
                    
                    with metric_cols[3]:
                        st.metric("营收增长率(%)", f"{fund_data.iloc[0]['营收增长率(%)']:.2f}")
                    
                    with metric_cols[4]:
                        st.metric("净利润增长率(%)", f"{fund_data.iloc[0]['净利润增长率(%)']:.2f}")
                
                # 显示近期数据
                with st.expander("查看历史数据"):
                    st.dataframe(
                        stock_data.sort_values('日期', ascending=False),
                        height=300
                    )
            else:
                st.error(f"未能获取到 {selected_stock} 的数据，请尝试其他股票。")
    
    # 选股工具选项卡
    with tab3:
        st.title("🔎 多维度选股工具")
        
        st.markdown("""
        ### 使用说明
        - 设置下面的筛选条件，系统将为您从A股市场筛选符合条件的股票
        - 留空或设置为0表示不限制该条件
        - 为提高性能，系统将只处理部分股票
        - 筛选可能需要一些时间，请耐心等待
        """)
        
        # 筛选条件输入
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.subheader("市盈率(PE)")
            pe_min = st.number_input("最小PE", min_value=0.0, max_value=1000.0, value=0.0, step=1.0)
            pe_max = st.number_input("最大PE", min_value=0.0, max_value=1000.0, value=50.0, step=1.0)
        
        with col2:
            st.subheader("市净率(PB)")
            pb_min = st.number_input("最小PB", min_value=0.0, max_value=100.0, value=0.0, step=0.1)
            pb_max = st.number_input("最大PB", min_value=0.0, max_value=100.0, value=5.0, step=0.1)
        
        with col3:
            st.subheader("其他指标")
            roe_min = st.number_input("最小ROE(%)", min_value=0.0, max_value=100.0, value=10.0, step=1.0)
            growth_min = st.number_input("最小营收增长率(%)", min_value=-100.0, max_value=1000.0, value=5.0, step=1.0)
            
        # 添加高级选项
        with st.expander("高级选项"):
            max_stocks = st.slider("最大处理股票数量", min_value=50, max_value=500, value=200, step=50,
                                help="增加此值会提高筛选结果的全面性，但会降低性能")
        
        # 开始筛选按钮
        if st.button("开始筛选", key="start_filter"):
            # 执行筛选
            result_df = filter_stocks(pe_min, pe_max, pb_min, pb_max, roe_min, growth_min, max_stocks)
            
            # 显示结果
            if not result_df.empty:
                st.success(f"共找到 {len(result_df)} 只符合条件的股票")
                
                # 添加排序选项
                sort_column = st.selectbox(
                    "排序依据",
                    options=["ROE(%)", "市盈率", "市净率", "营收增长率(%)", "净利润增长率(%)"],
                    index=0
                )
                
                sort_order = st.radio(
                    "排序方式",
                    options=["降序", "升序"],
                    index=0,
                    horizontal=True
                )
                
                # 显示筛选结果
                st.dataframe(
                    result_df.sort_values(by=sort_column, ascending=(sort_order=="升序")),
                    column_config={
                        "代码": st.column_config.TextColumn(width="small"),
                        "名称": st.column_config.TextColumn(width="medium"),
                        "市盈率": st.column_config.NumberColumn(format="%.2f"),
                        "市净率": st.column_config.NumberColumn(format="%.2f"),
                        "ROE(%)": st.column_config.NumberColumn(format="%.2f%%"),
                        "营收增长率(%)": st.column_config.NumberColumn(format="%.2f%%"),
                        "净利润增长率(%)": st.column_config.NumberColumn(format="%.2f%%")
                    },
                    height=500,
                    hide_index=True
                )
                
                # 提供导出功能
                csv = result_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="导出为CSV",
                    data=csv,
                    file_name=f"选股结果_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime='text/csv',
                )
            else:
                st.warning("未找到符合条件的股票，请尝试放宽筛选条件")

if __name__ == "__main__":
    main()