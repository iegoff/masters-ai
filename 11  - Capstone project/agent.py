import os
import logging
import datetime
import requests
import pandas as pd
import numpy as np
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
from json import loads
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
import matplotlib.pyplot as plt

st.set_page_config(
        page_title='Dubai Properties Transactions',
        page_icon="🏘️"                  
        )
retry_strategy = Retry(
    total=4,  # maximum number of retries
    backoff_factor=1,
    status_forcelist=[403, 429, 500, 502, 503, 504],  # the HTTP status codes to retry on
)
adapter = HTTPAdapter(max_retries=retry_strategy)
session = requests.Session()
session.mount("http://", adapter)
session.mount("https://", adapter)
# Load environment variables
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
DUBAI_TRANSACTIONS_URL = "https://gateway.dubailand.gov.ae/open-data/transactions"
EXCHANGE_RATE_API = "https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/aed.json"
TRANSACTION_LIMIT = 20 # Limit the number of transactions to fetch by agent "Security countermeasure"

tools  = [
        {
            "type": "function",
            "function": {
                    "name": "fetch_exchange_rate",
                    "description": "Get the latest currency exchange rates for AED.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "currency": {
                                "type": "string",
                                "description": "Curency code e.g. usd, eur, gbp"
                            }
                        },
                        "additionalProperties": False
                    },
                },
            "strict": True
        },
        {
            "type": "function",
            "function": {
                "name": "fetch_dubai_transactions",
                "description": "Retrieve Dubai property transactions.",
                "parameters": {
                    "type": "object",
                        "properties": {
                            "from_date": {
                                "type": "string",
                                "description": f"Start date (MM/DD/YYYY), current date is {datetime.date.today()}"
                            },
                            "to_date": {"type": "string", "description": "End date (MM/DD/YYYY)"},
                            "prop_type_id": {"type": "string", "description": "Property type ID (1=Land, 2=Building, 3=Unit)"},
                            "take": {"type": "integer", "description": "Number of transactions to retrieve e.g 10"}
                        },
                        "additionalProperties": False
                }
            },
            "strict": True
        }
    ]
# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def fetch_dubai_transactions(from_date=None, to_date=None, prop_type_id="3", take=1000):
    """Fetch property transactions from the Dubai Land Department API."""
    
    if not from_date:
        from_date = (datetime.date.today() - datetime.timedelta(days=1)).strftime("%m/%d/%Y")
    if not to_date:
        to_date = datetime.date.today().strftime("%m/%d/%Y")

    headers = {"Content-Type": "application/json"}
    payload = {
        "P_FROM_DATE": from_date,
        "P_TO_DATE": to_date,
        "P_GROUP_ID": "",
        "P_IS_OFFPLAN": "",
        "P_IS_FREE_HOLD": "1",
        "P_AREA_ID": "",
        "P_USAGE_ID": "1",
        "P_PROP_TYPE_ID": prop_type_id,
        "P_TAKE": str(take),
        "P_SKIP": "0",
        "P_SORT": "TRANSACTION_NUMBER_ASC"
    }
    try:
        response = session.post(DUBAI_TRANSACTIONS_URL, json=payload, headers=headers)
        response.raise_for_status()
    except (requests.RequestException) as e:
        logging.error(f"Failed to fetch exchange rates: {e}")
        raise 
    data = response.json().get("response", {}).get("result", [])

    logging.info(f"Fetched {len(data)} transactions from {from_date} to {to_date}.")
    return data
    # if data:
    #     df = pd.DataFrame(data)
    #     return df[["TRANSACTION_NUMBER", "INSTANCE_DATE", "AREA_EN", "TRANS_VALUE", "PROJECT_EN"]]
    # return pd.DataFrame()

def fetch_exchange_rate(currency="usd"):
    """Fetch the latest exchange rates for AED."""
    try:
        response = requests.get(EXCHANGE_RATE_API)
        response.raise_for_status()
        data = response.json()
        return data.get("aed").get(currency)
    except Exception as e:
        logging.error(f"Failed to fetch exchange rates: {e}")
        return {}

# Initialize Streamlit UI
st.title("🏘️ Dubai Properties Transactions")
st.caption("🤖 Dubai properties transactions AI Assistant")



# Tabs for different property types
tab1, = st.tabs(["Get data here"])

with tab1:
    from_date = st.text_input("From Date (MM/DD/YYYY)", value="01/28/2025")
    to_date = st.text_input("To Date (MM/DD/YYYY)", value="01/29/2025")
    property_type = st.selectbox("Property Type", ["Unit", "Building", "Land"], index=0)
    take = st.slider("Number of Transactions", 1, 100, 10)
    property_type_map = {"Unit": "3", "Building": "2", "Land": "1"}

    if st.button("Fetch Transactions"):
        transactions = fetch_dubai_transactions(from_date, to_date, property_type_map[property_type], take)
        # curr = fetch_exchange_rate()
        predefined_df = pd.DataFrame(transactions)
        columns_to_display = ["TRANSACTION_NUMBER", "AREA_EN", "ROOMS_EN", "PROCEDURE_AREA", "TRANS_VALUE"]
        df_display = predefined_df[columns_to_display]

        # Rename columns for better readability
        rename_dict = {
            "TRANSACTION_NUMBER": "Transaction ID",
            "AREA_EN": "Area",
            "ROOMS_EN": "Rooms",
            "PROCEDURE_AREA": "Property Size (sqm)",
            "TRANS_VALUE": "Transaction Value (AED)"
        }
        df_display = df_display.rename(columns=rename_dict)
        if not predefined_df.empty:
            st.dataframe(df_display)
        else:
            st.warning("No transactions found.")

# Sidebar API Key Input
with st.sidebar:
    df = pd.DataFrame(fetch_dubai_transactions())
    top_areas = df.groupby("AREA_EN")["TRANS_VALUE"].sum().nlargest(10).index
    df_filtered = df[df["AREA_EN"].isin(top_areas)]

    # Streamlit app title
    st.title("Real Estate Transactions Dashboard")




    # Bar chart: Transaction Value per Area
    st.subheader("Transaction Value per Area")
    fig, ax = plt.subplots()
    df_filtered.groupby("AREA_EN")["TRANS_VALUE"].sum().plot(kind="bar", ax=ax)
    ax.set_ylabel("Total Transaction Value")
    ax.set_xlabel("Area")
    ax.set_title("Total Transaction Value by Area")
    st.pyplot(fig)
    # Filter selection (only top 10 areas)
    selected_area = st.selectbox("Select an Area:", top_areas)

    # Filter data based on selection
    filtered_df = df_filtered[df_filtered["AREA_EN"] == selected_area]
    # Scatter Plot: Property Size vs. Transaction Value
    st.subheader("Property Size vs. Transaction Value")
    fig, ax = plt.subplots()
    ax.scatter(df_filtered["PROCEDURE_AREA"], df_filtered["TRANS_VALUE"], c="blue", label="All Data")
    ax.scatter(
        filtered_df["PROCEDURE_AREA"], filtered_df["TRANS_VALUE"], c="red", label=f"{selected_area} Data"
    )
    ax.set_xlabel("Property Size (sqm)")
    ax.set_ylabel("Transaction Value")
    ax.set_title("Property Size vs. Transaction Value")
    ax.legend()
    st.pyplot(fig)
    if not openai_api_key:
        openai_api_key = st.text_input("OpenAI API Key", key="chatbot_api_key", type="password")
# Chatbot with function calling
if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "Ask me about Dubai property transactions"}]

for msg in st.session_state.messages:
    if  msg["role"] != "tool":
        st.chat_message(msg["role"]).write(msg["content"])
    # st.chat_message(msg.role).write(msg.content)

if prompt := st.chat_input():
    if not openai_api_key:
        st.warning("Please provide an OpenAI API key.")
        st.stop()
    client = OpenAI(api_key=openai_api_key)
    # Define available functions
    
    # Send the user prompt to OpenAI
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)
    with st.spinner('Wait for it...'):
        assistant_placeholder = st.chat_message("assistant").empty()
        assistant_placeholder.write("Thinking...") 
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=st.session_state.messages,
            tools=tools
        )

        # Check if the response wants to call a function
        msg = response.choices[0].message
        # print(msg.tool_calls)

        if msg.tool_calls:
            st.session_state.messages.append({                               # append result message
                        "role": msg.role,
                        "tool_calls": msg.tool_calls,
                        "content": msg.content
                    })
            for func in msg.tool_calls:
                # print(func) 
                # print(func.id) 
                function_name = func.function.name
                function_args = func.function.arguments
                
                logging.info(f"Function call requested: {function_name} with args {function_args}")
                data = loads(function_args)
                # Execute the function
                if function_name == "fetch_exchange_rate":                
                    if data.get("currency"):
                        currency = data.get("currency")
                    function_response = fetch_exchange_rate(currency)
                elif function_name == "fetch_dubai_transactions":
                    if data.get("take") and data.get("take") > TRANSACTION_LIMIT:
                        st.warning(f"Maximum transactions allowed is {TRANSACTION_LIMIT}.")
                        data["take"] = TRANSACTION_LIMIT
                    function_response = fetch_dubai_transactions(
                        from_date=data.get("from_date"),
                        to_date=data.get("to_date"),
                        prop_type_id=data.get("prop_type_id"),
                        take=data.get("take")
                    )[:TRANSACTION_LIMIT]
                else:
                    function_response = {"error": "Function not found"}
                st.session_state.messages.append({                               # append result message
                        "role": "tool",
                        "tool_call_id": func.id,
                        "content": str(function_response)
                    })
                # # Send the function response back to the LLM
                # st.session_state.messages.append(
                #     {"role": "function", "name": function_name, "content": str(function_response)}
                # )
                # st.chat_message("assistant").write(str(function_response))

            response = client.chat.completions.create(
                model="gpt-4o",
                messages=st.session_state.messages,
                tools=tools,
            )
            msg = response.choices[0].message
            st.session_state.messages.append({"role": "assistant", "content": msg.content})
            st.chat_message("assistant").write(msg.content)

        else:
            # Normal response
            st.session_state.messages.append({"role": "assistant", "content": msg.content})
            st.chat_message("assistant").write(msg.content)
