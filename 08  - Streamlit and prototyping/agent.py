import streamlit as st
from openai import OpenAI
import logging
import requests
import sqlite3
import pandas as pd
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

# Load OpenAI API Key
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)
# Chat with OpenAI agent
def chat_with_agent(user_message):
    prompt = (
        f"You are an intelligent AI agent that helps users with their questions. "
        f"User message: {user_message}"
    )
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": user_message}],
            max_tokens=150
        )
        reply = response.choices[0].message.content
        logging.info(f"User message: {user_message}, AI reply: {reply}")
        return reply
    except Exception as e:
        logging.error(f"Error in OpenAI agent response: {e}")
        return f"Error in AI agent response: {e}"

# Perform an action via external API
def perform_action(action, data):
    try:
        # Example: Simulated third-party API endpoint
        api_url = "https://jsonplaceholder.typicode.com/posts"
        response = requests.post(api_url, json={"action": action, "data": data})
        logging.info(f"Performed action: {action} with data: {data}, API response: {response.status_code}")
        return response.json()
    except Exception as e:
        logging.error(f"Error performing action: {e}")
        return {"error": str(e)}

# Fetch business information from the database
def fetch_business_info():
    try:
        conn = sqlite3.connect('transactions.sqlite')
        query = "SELECT prop_sb_type, COUNT(*) as count, SUM(prop_price) as total_amount FROM transactions GROUP BY prop_sb_type;"
        df = pd.read_sql_query(query, conn)
        conn.close()
        logging.info("Fetched business information from the database")
        return df
    except Exception as e:
        logging.error(f"Error fetching business information: {e}")
        return pd.DataFrame()

# Streamlit UI
def main():
    st.title("AI Agent with Business Insights")

    # Display business information
    st.header("Business Overview")
    business_info = fetch_business_info()
    if not business_info.empty:
        st.write("### Transactions Summary by Category")
        st.dataframe(business_info)
        st.bar_chart(business_info.set_index("prop_sb_type")["count"])
    else:
        st.error("Failed to fetch business information.")

    # Chat with AI Agent
    st.header("Chat with the AI Agent")
    user_message = st.text_input("Enter your message for the AI agent", placeholder="Ask anything...")

    if st.button("Send Message"):
        if user_message.strip():
            ai_reply = chat_with_agent(user_message)
            st.write("### AI Agent Reply")
            st.text(ai_reply)
        else:
            st.warning("Please enter a message to send to the AI agent.")

    # Perform an action
    st.header("Perform an Action")
    action = st.text_input("Enter an action to perform (e.g., 'notify', 'report')")
    data = st.text_input("Enter data for the action")

    if st.button("Perform Action"):
        if action.strip() and data.strip():
            response = perform_action(action, data)
            st.write("### Action Response")
            st.json(response)
        else:
            st.warning("Please provide both action and data.")

if __name__ == "__main__":
    main()