import streamlit as st
import yfinance as yf
import pandas as pd
from yahooquery import Ticker
import plotly.graph_objs as go
import csv
import os
import altair as alt
import numpy as np
import pandas as pd
import locale

from valuation_measures import ValuationMeasures as vm
from finance_data import FinanceData as fd
from file_operation import FileOperation as ff
from favorites import favorite_manager as fm


@st.cache_data
def get_symbols():
    with open(os.getcwd() + u'/value_list.txt', newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter=',', quotechar='"')
        symbols = [row[0] for row in reader]

    return symbols


# ページの幅を1200ピクセルに設定
# st.set_page_config(layout="wide")

# ロケールを設定する（日本語を指定）
locale.setlocale(locale.LC_NUMERIC, 'ja_JP')

### data ###################################################################

# 株価リストを取得
symbols = get_symbols()
symbols = [""] + symbols

### Sidebar ###################################################################
main, favorite = st.sidebar.tabs(["main", "favorite"])

with main:
    # mainタブの処理
    ticker = st.selectbox(
        'Please select a stock symbol',
        symbols,
    )

    if ticker != "":
        
        stock = yf.Ticker(ticker + ".T")
        info = stock.info
        st.write(info.get("longName"))
        if len(ticker) != 0:

            st.divider()

            st.subheader(':blue[セクター情報]')
            info_col1, info_col2 = st.columns(2)
            with info_col1:
                st.caption('industry')
                st.write(stock.info['industry'])
            with info_col2:
                st.caption('sector')
                st.write(stock.info['sector'])

            st.divider()
            
            # 株価情報を表示
            st.subheader(':blue[株価情報]')
            info_col1, info_col2, info_col3 = st.columns(3)
            finish_value = stock.info['regularMarketPreviousClose']
            open_value = stock.info['regularMarketOpen']
            high_value = stock.info['dayHigh']
            low_value = stock.info['dayLow']
            with info_col1:
                st.metric("始値", open_value, open_value - finish_value)
            with info_col2:
                st.metric("高値", high_value, high_value - finish_value)
            with info_col3:
                st.metric("安値", low_value, low_value - finish_value)

            try:
                st.write('配当金')
                st.write(stock.info['dividendRate'])
            except:
                pass

with favorite:
    file_path = "C:/Users/tokyo/Documents/GitHub/Streamlit/favorites.csv"

    # 1. CSVファイルからお気に入り情報を読み込む
    favorites_df = fm.load_favorites(file_path)
    favorites = fm.parse_favorites(favorites_df)

    # 2. お気に入り情報を編集する
    favorites = fm.edit_favorites(favorites)

    if favorites != None:
        # 3. お気に入り情報を更新する
        fm.update_favorites(favorites, file_path)

    # 4. お気に入りを呼び出す
    if favorites != None:
        selected_codes = fm.select_favorites(favorites)

    # 5. 結果を表示する
    st.write("Selected Securities:", selected_codes)

### Main ######################################################################
options_multiselect = []
if 'prev_tickers' not in st.session_state:
    st.session_state.prev_tickers = []

if 'tickers' not in st.session_state:
    st.session_state.tickers = []

if ticker not in st.session_state.tickers:
    st.session_state.tickers.append(ticker)

if len(selected_codes) != 0:
    for code in selected_codes:
        if not code in st.session_state.tickers:
            st.session_state.tickers.append(code)

# options_multiselectに含まれるtickerを更新するために、
# 新しいリストを作成してからoptions_multiselectを更新する
selected_tickers = st.session_state.tickers.copy()
if ticker not in selected_tickers:
    selected_tickers.append(ticker)
if st.session_state.tickers[0] == '' and len(st.session_state.tickers) == 1:
    options_multiselect = st.multiselect(
        'Selected stock symbols',
        symbols,
        key='color_multiselect'
        )

else:
    selected_tickers = [x for x in selected_tickers if x != '']
    options_multiselect = st.multiselect(
        'Selected stock symbols',
        symbols,
        selected_tickers,
        key='color_multiselect'
    )

# options_multiselectから選択されなくなったtickerを削除する
unselected_tickers = set(st.session_state.tickers) - set(options_multiselect)
if unselected_tickers:
    for unselected_ticker in unselected_tickers:
        st.session_state.tickers.remove(unselected_ticker)

select_symbols_df = pd.DataFrame(
    columns=['証券コード', '社名', 'マーケット', '時価総額', '予想PER', 'PER', 'PBR', '配当利回', "is_widget"])


# 新しい行を作成し、データフレームに追加する
for sss in options_multiselect:
    try:
        stock = yf.Ticker(sss + ".T")
        info = stock.info

        try:
            trailingPE = round(info.get('trailingPE', 'N/A'), 2)
        except:
            trailingPE = 'N/A'
        try:
            priceToBook = round(info.get('priceToBook', 'N/A'), 2)
        except:
            priceToBook = 'N/A'
        try:
            trailing_annual_dividend_yield = info.get(
                'trailingAnnualDividendYield')
            if trailing_annual_dividend_yield is not None:
                dividend_payout_ratio = round(
                    trailing_annual_dividend_yield * 100, 2)
            else:
                dividend_payout_ratio = 'N/A'
        except:
            dividend_payout_ratio = 'N/A'

        stock_data = {
            '証券コード': sss,
            '社名': info.get('longName', 'N/A'),
            'マーケット': info.get('market', 'N/A'),
            '時価総額': info.get('marketCap', 'N/A'),
            '予想PER': round(info.get('forwardPE', 'N/A'), 2),
            'PER': trailingPE,
            'PBR': priceToBook,
            '配当利回': dividend_payout_ratio,
            "is_widget": True
        }
        new_row = pd.Series({
            "証券コード": stock_data['証券コード'], 
            "社名": stock_data['社名'], 
            "マーケット": stock_data['マーケット'], 
            "時価総額": stock_data['時価総額'], 
            "予想PER": stock_data['予想PER'],
            "PER": stock_data['PER'], 
            "PBR": stock_data['PBR'], 
            "配当利回": stock_data['配当利回'], 
            "is_widget": True})
        select_symbols_df = select_symbols_df.append(
            new_row, ignore_index=True)
    except:
        st.error(sss + 'は何かしらの情報を取得できません', icon="🚨")

edited_df = st.experimental_data_editor(select_symbols_df)

# データエディターで編集された値を取得する
edited_df_dict = edited_df.to_dict(orient='records')
# 編集後の値を select_symbols_df に反映する
select_symbols_df = pd.DataFrame.from_records(edited_df_dict)

try:

    st.divider()
    # info_col1, info_col2 = st.columns(2)
    # with info_col1:
    months = st.slider(':blue[月数]', 1, 100, 2)
    # with info_col2:
        # ymin, ymax = st.slider(':blue[株価範囲]', 0.0, 10000.0, (1000.0, 5000.0))

    # 株価のグラフを表示
    tickers = select_symbols_df['証券コード']
    is_widget = select_symbols_df['is_widget']

    tickers = [tickers[i] for i in range(len(tickers)) if is_widget[i]]

    tickers_close_value = fd.get_data(months, tickers, "Close", 0)
    tickers_volume_value = fd.get_data(months, tickers, "Volume", 0)
    
    tickers_close_value = tickers_close_value.loc[tickers]
    tickers_volume_value = tickers_volume_value.loc[tickers]

    # データの整形
    tickers_close_value = tickers_close_value.T.reset_index()
    tickers_close_value = pd.melt(tickers_close_value, id_vars=['Date']).rename(
        columns={'value': 'Close'}
    )
    tickers_volume_value = tickers_volume_value.T.reset_index()
    tickers_volume_value = pd.melt(tickers_volume_value, id_vars=['Date']).rename(
        columns={'value': 'Volume'}
    )

    color_scale = alt.Scale(range=["#003f5c", "#bc5090", "#ffa600"])
    ymin = tickers_close_value['Close'].min()
    ymax = tickers_close_value['Close'].max()
    chart_close = (
        alt.Chart(tickers_close_value)
        .mark_line(opacity=0.8, clip=True)
        .encode(
            x="Date:T",
            y=alt.Y("Close:Q", stack=None,
                    scale=alt.Scale(domain=[ymin, ymax])),
            color=alt.Color('Name:N', scale=alt.Scale(scheme='category10'))
        )
        .configure_axis(
            gridOpacity=0.8,
        )
        .configure_legend(
            titleFontSize=12,
            labelFontSize=11,
            symbolType="circle",
            symbolSize=100,
            padding=5,
            cornerRadius=5,
        )
    )
    
    ymin = tickers_volume_value['Volume'].min()
    ymax = tickers_volume_value['Volume'].max()
    chart_volume = (
        alt.Chart(tickers_volume_value)
        .mark_line(opacity=0.8, clip=True)
        .encode(
            x="Date:T",
            y=alt.Y("Volume:Q", stack=None,
                    scale=alt.Scale(domain=[ymin, ymax])),
            color=alt.Color('Name:N', scale=alt.Scale(scheme='category10'))
        )
        .configure_axis(
            gridOpacity=0.8,
        )
        .configure_legend(
            titleFontSize=12,
            labelFontSize=11,
            symbolType="circle",
            symbolSize=100,
            padding=5,
            cornerRadius=5,
        )
    )
    
    info_col1, info_col2 = st.columns(2)
    with info_col1:
        st.subheader(":blue[Value Chart]")
        st.altair_chart(chart_close.interactive(), use_container_width=True)
    with info_col2:
        st.subheader(":blue[Volume Chart]")
        st.altair_chart(chart_volume.interactive(), use_container_width=True)
    
    
    subsets = vm.get_valuation_measures(tickers)
    charts_pbr = []
    charts_per = []
    for subset in subsets:
        chart_pbr = alt.Chart(subset).mark_line().encode(
            x='asOfDate',
            y=alt.Y('PbRatio', scale=alt.Scale(
                domain=[subset['PbRatio'].min()-0.1, subset['PbRatio'].max()+0.1])),
            color=alt.Color('symbol:N', scale=alt.Scale(scheme='category10')),
            tooltip=['symbol', 'asOfDate', 'PbRatio'],  # ツールチップに表示する列を指定
        )

        charts_pbr.append(chart_pbr)
        chart_per = alt.Chart(subset).mark_line().encode(
            x='asOfDate',
            y=alt.Y('PeRatio', scale=alt.Scale(
                domain=[subset['PeRatio'].min()-0.1, subset['PeRatio'].max()+0.1])),
            color=alt.Color('symbol:N', scale=alt.Scale(scheme='category10')),  # 列 'symbol' をカラーに設定
            tooltip=['symbol', 'asOfDate', 'PeRatio']  # ツールチップに表示する列を指定
        )
        charts_per.append(chart_per)
    info_col1, info_col2 = st.columns(2)
    with info_col1:
        st.subheader(":blue[PBR]")
        st.altair_chart(alt.layer(*charts_pbr), use_container_width=True)
    with info_col2:
        st.subheader(":blue[PER]")
        st.altair_chart(alt.layer(*charts_per), use_container_width=True)

    df_income = fd.get_data(months, tickers, "Dividends", 1)
    data_income = df_income.loc[tickers]
    data_income = ff.remove_all_zero_col(data_income)
    st.write("### :blue[配当実績]", data_income.sort_index())

except Exception as e:
    print("****************************************************")
    print(e)
    print("****************************************************")
    st.stop()
