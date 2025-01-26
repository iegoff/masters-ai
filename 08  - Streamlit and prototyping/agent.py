from openai import OpenAI
import streamlit as st
import os
from dotenv import load_dotenv
import pandas as pd
import numpy as np

load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")


chart_data = pd.DataFrame(np.random.rand(20, 3), columns=["Samana", "RED Square", "Verdes"])
chart_data_offplan = pd.DataFrame(np.random.rand(20, 2), columns=["Ready", "Off-Plan"])
with st.sidebar:
    if not openai_api_key:
        openai_api_key = st.text_input("OpenAI API Key", key="chatbot_api_key", type="password")


st.title("🏘️ Dubai Properties Transactions")
st.caption("🤖 Dubai properties transactions AI Assistant")

# Insert containers separated into tabs:
tab1, tab2, tab3  = st.tabs(["Flats", "Villas", "Commercial"])
df = chart_data

# You can also use "with" notation:
with tab1:
    st.area_chart(chart_data_offplan)
    st.bar_chart(df)
with tab2:
    
    st.bar_chart(chart_data_offplan, horizontal=True)
    st.line_chart(df)



    
if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "Ask me about dubai property transactions"}]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

if prompt := st.chat_input():
    if not openai_api_key:
        st.info("Please add your OpenAI API key to continue.")
        st.stop()

    client = OpenAI(api_key=openai_api_key)
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)
    response = client.chat.completions.create(model="gpt-4o", messages=st.session_state.messages)
    msg = response.choices[0].message.content
    st.session_state.messages.append({"role": "assistant", "content": msg})
    st.chat_message("assistant").write(msg)