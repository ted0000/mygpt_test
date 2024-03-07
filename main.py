from typing import Union
import os
import json
from openai import OpenAI
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.responses import StreamingResponse

app = FastAPI()

import requests
import re
import io
import pandas as pd
import FinanceDataReader as fdr
from datetime import datetime, timedelta
import matplotlib
matplotlib.use('Agg')  # GUI가 필요없는 백엔드로 설정
import matplotlib.pyplot as plt
import tempfile

@app.get("/finstate_summary")
def finstate_summary(code: str):
    '''
    요약 재무제표 데이터를 가져와 CSV 문자열을 반환합니다
    :param code: 종목코드
    '''
    print(f'finstate_summary({code}) calling') # 호출 확인을 위한 print

    # fin_type: 재무제표 종류 '0'=주재무제표, '1'=K-GAAP개별, '2'=K-GAAP연결, '3'=K-IFRS별도, '4'=K-IFRS연결
    # freq: 기간: Y=년(기본), Q=분기, 'A'=연간분기 전체
    fin_type, freq ='0', 'Y'

    # encparam 읽어오기
    url = 'https://navercomp.wisereport.co.kr/v2/company/c1010001.aspx?cmp_cd=005930'
    html_text = requests.get(url).text

    if not re.search("encparam: '(.*?)'", html_text):
        print('encparam not found') # encparam이 없는 경우
        return None
    encparam = re.findall ("encparam: '(.*?)'", html_text)[0]

    url = f'https://navercomp.wisereport.co.kr/v2/company/ajax/cF1001.aspx?cmp_cd={code}&fin_typ={fin_type}&freq_typ={freq}&encparam={encparam}'
    r = requests.get(url, headers={'Referer': url})
    df_list = pd.read_html(io.StringIO(r.text), encoding='euc-kr')
    df = df_list[1]
    df.columns = [col[1] for col in df.columns]
    df.set_index('주요재무정보', inplace=True)
    df.columns = [re.sub('[^\.\d]', '', col) for col in df.columns]
    df.columns = [pd.to_datetime(col, format='%Y%m', errors='coerce') for col in df.columns]
    df = df.transpose()
    df.index.name = '날짜'
    return {df.to_csv()} ## CSV 문자열을 반환


# stock history data getting function
@app.get("/history")
def get_stock_history(symbol, duration=30):
    end_date = datetime.now()
    start_date = end_date - timedelta(days=duration)
    df = fdr.DataReader(symbol, start_date, end_date)
    
    # 차트 생성
    plt.figure(figsize=(10, 5))
    plt.plot(df.index, df['Close'], label='Close')
    plt.title(f'{symbol} Close Price Chart')
    
    plot_file = io.BytesIO()
    plt.savefig(plot_file, format='png')
    plt.close()
    plot_file.seek(0)
    
    return StreamingResponse(io.BytesIO(plot_file.read()), media_type="image/png")

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/test")
def test(param: str):
    return {param}
