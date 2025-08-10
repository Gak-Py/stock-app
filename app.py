import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import date
import numpy as np
# plotlyをインポート
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ページ全体のレイアウトを「ワイド」に設定
st.set_page_config(layout="wide")

st.title('株価可視化アプリ')

# ティッカーシンボル入力欄
st.sidebar.header('銘柄設定')

# st.markdownを使って複数行の説明文を追加
st.sidebar.markdown("""
**銘柄コードを入力してください**
(例: AAPL)
(東証の場合は、最後に`.T`を入力)
""")

# text_inputで1行の入力を受け付ける
symbol = st.sidebar.text_input('(例: 7203.T)', placeholder='ティッカーシンボル')

# 期間設定
st.sidebar.header('期間設定')
today = date.today()
start_date = st.sidebar.date_input('開始日', value=today.replace(year=today.year - 1))
end_date = st.sidebar.date_input('終了日', value=today)

# pandas-taを使わずにRSIを計算する関数
def calculate_rsi(df, period=14):
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    return df

# pandas-taを使わずにMACDを計算する関数
def calculate_macd(df, short_period=12, long_period=26, signal_period=9):
    ema_short = df['Close'].ewm(span=short_period, adjust=False).mean()
    ema_long = df['Close'].ewm(span=long_period, adjust=False).mean()
    df['MACD'] = ema_short - ema_long
    df['Signal'] = df['MACD'].ewm(span=signal_period, adjust=False).mean()
    df['MACD_Hist'] = df['MACD'] - df['Signal']
    return df

if symbol:
    try:
        # 株価データの取得
        ticker = yf.Ticker(symbol)
        df = ticker.history(start=start_date, end=end_date)
        
        if df.empty:
            st.warning(f"指定された期間の株価データが見つかりませんでした: {symbol}")
        else:
            # データの表示
            st.subheader(f'{symbol} の株価データ')
            st.write(df)

            # 移動平均線を計算
            df['MA20'] = df['Close'].rolling(window=20).mean()
            df['MA50'] = df['Close'].rolling(window=50).mean()

            # RSIとMACDを計算
            df_rsi = calculate_rsi(df.copy())
            df_macd = calculate_macd(df.copy())

            # サブプロットの作成
            st.subheader('ローソク足、RSI、MACD')
            fig = make_subplots(rows=3, cols=1, shared_xaxes=True, 
                                vertical_spacing=0.05,
                                row_heights=[0.5, 0.25, 0.25],
                                subplot_titles=[f'{symbol} 株価', 'RSI', 'MACD'])

            # ローソク足チャートと移動平均線を描画
            fig.add_trace(go.Candlestick(x=df.index,
                                        open=df['Open'],
                                        high=df['High'],
                                        low=df['Low'],
                                        close=df['Close'],
                                        name='ローソク足'), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], mode='lines', name='MA20',
                                     line=dict(color='orange', width=2)), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['MA50'], mode='lines', name='MA50',
                                     line=dict(color='purple', width=2)), row=1, col=1)

            # RSIチャートを描画
            fig.add_trace(go.Scatter(x=df_rsi.index, y=df_rsi['RSI'], mode='lines', name='RSI',
                                     line=dict(color='green', width=2)), row=2, col=1)
            # RSIの買われすぎ・売られすぎを示す水平線を追加
            fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
            fig.add_hline(y=30, line_dash="dash", line_color="blue", row=2, col=1)


            # MACDチャートを描画
            fig.add_trace(go.Scatter(x=df_macd.index, y=df_macd['MACD'], mode='lines', name='MACD',
                                     line=dict(color='blue', width=2)), row=3, col=1)
            fig.add_trace(go.Scatter(x=df_macd.index, y=df_macd['Signal'], mode='lines', name='Signal',
                                     line=dict(color='red', width=1)), row=3, col=1)
            fig.add_trace(go.Bar(x=df_macd.index, y=df_macd['MACD_Hist'], name='Histogram',
                                 marker_color='gray'), row=3, col=1)

            # レイアウト調整
            fig.update_layout(xaxis_rangeslider_visible=False,
                              height=1000, # チャート全体の高さを設定
                              showlegend=True,
                              # マウスホバー時に縦線を表示する設定
                              hovermode='x unified')
            st.plotly_chart(fig, use_container_width=True)

            st.write('---')

            st.subheader(f'{symbol} の企業情報')
            info = ticker.info
            st.write(f"**会社名:** {info.get('longName', 'N/A')}")
            st.write(f"**業種:** {info.get('sector', 'N/A')}")
            st.write(f"**所在地:** {info.get('country', 'N/A')}")
            st.write(f"**ウェブサイト:** {info.get('website', 'N/A')}")

    except Exception as e:
        st.error(f"エラーが発生しました: {e}")
        st.warning("ティッカーシンボルを正しく入力しているか確認してください。")
