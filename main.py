from fastapi import FastAPI
from fastapi.responses import StreamingResponse

app = FastAPI()

import requests
import re
import io
import pandas as pd
import FinanceDataReader as fdr
from datetime import datetime, timedelta
import mplfinance as mpf
from io import BytesIO


@app.get("/finstate_summary")
def finstate_summary(code: str):
    '''
    Get summary financial statement data and return a CSV string.
    
    :param code: Stock code.
    :return: CSV string of the summary financial statement data.
    '''
    print(f'finstate_summary({code}) calling') # Print for confirmation

    # fin_type: Type of financial statement: '0' = Main financial statement, '1' = K-GAAP individual, '2' = K-GAAP consolidated, '3' = K-IFRS separate, '4' = K-IFRS consolidated
    # freq: Period: Y = Year (default), Q = Quarter, 'A' = Annual and quarterly combined
    fin_type, freq ='0', 'Y'

    # Read encparam
    url = 'https://navercomp.wisereport.co.kr/v2/company/c1010001.aspx?cmp_cd=005930'
    html_text = requests.get(url).text

    if not re.search("encparam: '(.*?)'", html_text):
        print('encparam not found') # Return None if encparam is not found
        return None
    encparam = re.findall ("encparam: '(.*?)'", html_text)[0]

    url = f'https://navercomp.wisereport.co.kr/v2/company/ajax/cF1001.aspx?cmp_cd={code}&fin_typ={fin_type}&freq_typ={freq}&encparam={encparam}'
    r = requests.get(url, headers={'Referer': url})
    df_list = pd.read_html(io.StringIO(r.text), encoding='euc-kr')
    df = df_list[1]
    df.columns = [col[1] for col in df.columns]
    df.set_index('주요재무정보', inplace=True)
    df.columns = [re.sub('[^\\.\\d]', '', col) for col in df.columns]
    df.columns = [pd.to_datetime(col, format='%Y%m', errors='coerce') for col in df.columns]
    df = df.transpose()
    df.index.name = '날짜'
    return {df.to_csv()} ## Return CSV string


# Stock history data getting function
@app.get("/history")
def get_stock_history(symbol, duration=180):
    '''
    Get stock history data for a given symbol and duration.
    
    :param symbol: Stock symbol.
    :param duration: Duration in days (default is 30 days).
    :return: StreamingResponse object containing the plot image in PNG format.
    '''
    end_date = datetime.now()
    start_date = end_date - timedelta(days=duration)
    df = fdr.DataReader(symbol, start_date, end_date)
    
    buf = BytesIO()
    
    mpf.plot(df, type='candle', style='yahoo', mav=(10, 20, 60),
         title=(f'{symbol} Price Chart'),
         ylabel='Price ($)',
         figratio=(10,6),
         volume=True, savefig=buf)
    buf.seek(0)
    
    return StreamingResponse(buf, media_type="image/png")

@app.get("/")
def read_root():
    '''
    Default route handler.
    
    :return: JSON response with "Hello" and "World" keys.
    '''
    return {"Hello": "World"}

@app.get("/test")
def test(param: str):
    '''
    Test route handler.
    
    :param param: Test parameter.
    :return: JSON response with the test parameter.
    '''
    return {param}
