import asyncio
import edge_tts
import streamlit as st
import os
import sqlite3
import pandas as pd
import whisper
import tempfile
from gtts import gTTS
import pygame
import torch

# ワイド画面設定
st.set_page_config(layout="wide")

# DB に接続（なければ自動で作成される）
conn = sqlite3.connect("voice_record.db")
cur = conn.cursor()

# テーブルが存在しなければ作成
cur.execute("""
CREATE TABLE IF NOT EXISTS voice_data (
    filename TEXT TEXT NOT NULL UNIQUE,
    document TEXT,
    voice TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
)
""")

conn.commit()

filename_op = pd.read_sql_query('select filename from voice_data',conn)
filename_list = filename_op['filename'].to_list()

conn.close()

col = st.columns(2)

with col[0]:
    
    # Streamlit ファイルと同じ階層にある "audio" フォルダを指定
    AUDIO_DIR = "pp"

    os.makedirs(AUDIO_DIR, exist_ok=True)

    # mp3 ファイル一覧を取得
    mp3_files = [f for f in os.listdir(AUDIO_DIR) if f.endswith(".mp3")]

    if not mp3_files:
        st.warning("audio フォルダに mp3 ファイルがありません。")
        filename = ""
    else:
        # mp3 を選択
        selected_file = st.selectbox("再生する MP3 を選んでください", mp3_files)

        filename_split = selected_file.split('.')
        filename = filename_split[0]

        # ファイルパス
        file_path = os.path.join(AUDIO_DIR, selected_file)

        # 再生
        st.audio(file_path)

    conn = sqlite3.connect('voice_record.db')

    df = pd.read_sql_query('select * from voice_data order by created_at DESC',conn)
    st.dataframe(df,width='stretch',hide_index=True)

    conn.close()

with col[1]:

    new_entry = st.checkbox('新規')

    conn = sqlite3.connect('voice_record.db')
    cur = conn.cursor()
    
    doc = pd.read_sql_query('select document,voice from voice_data where filename=?',conn,params=[filename])

    if new_entry==True or len(doc)==0:
        filename = st.text_input('新規登録')
        TEXT = st.text_area("登録文言", value="文章を入力してください",height=500)
    else:
        TEXT = st.text_area("登録文言", value=doc['document'].iloc[0],height=500)

    if len(doc)!=0 and doc['voice'].iloc[0]=="男性":
        index=0
    else:
        index=1
    voice_select = st.radio('声の種類',['男性','女性'],horizontal=True,index=index)

    if voice_select == '女性':
        VOICE = 'ja-JP-NanamiNeural'
    else:
        VOICE = 'ja-JP-KeitaNeural'
    
    if st.button('録音'):

        async def generate_audio():
            communicate = edge_tts.Communicate(TEXT, VOICE)
            # 直接wav（またはmp3）として保存可能
            await communicate.save(file_path)

        folder_path = "pp"
        # フォルダが無ければ作成（存在していてもエラーにならない）
        os.makedirs(folder_path, exist_ok=True)

        file_path = f"pp\\{filename}.mp3"
        
        conn = sqlite3.connect('voice_record.db')
        cur = conn.cursor()

        item = pd.read_sql_query('select * from voice_data where filename = ?',conn,params=[filename])

        if len(item)>0:
            cur.execute('update voice_data set document=?,voice=? where filename=?',(TEXT,voice_select,filename,))
            conn.commit()
            messege_kubun = "上書き"
            st.success(f"{filename}　の{messege_kubun}が完了しました")
        else:
            cur.execute('insert into voice_data (filename,document,voice) values(?,?,?)',(filename,TEXT,voice_select,))
            conn.commit()
            messege_kubun = "新規登録"

            st.success(f"{filename}　の{messege_kubun}が完了しました")
        
        asyncio.run(generate_audio())

        conn.close()

        st.rerun()

        # 実行
        #if __name__ == "__main__":
        #    asyncio.run(generate_audio())

conn.close()
    

    