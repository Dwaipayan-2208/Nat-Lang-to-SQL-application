import os
from pathlib import Path
import mysql.connector
from openai import OpenAI
import pandas as pd
import streamlit as st
from dotenv import find_dotenv, load_dotenv

# Locate .env specifically inside the "NL to SQL app" subfolder
BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / "NL to SQL app" / ".env"

# If the file isn't in a subfolder, check the script's direct directory
if not ENV_PATH.exists():
    ENV_PATH = BASE_DIR / ".env"

load_dotenv(dotenv_path=ENV_PATH, override=True)

# Streamlit Page Setup
st.set_page_config(page_title="NL to SQL Agent", page_icon="🤖", layout="wide")

# Sidebar: App Rules and Information
st.sidebar.title("📌 Query Guidelines & Rules")
st.sidebar.markdown(
    """
1. **Plain English Only:** Type your database question naturally without SQL code.
2. **Schema Scope:** Ensure your questions pertain to the existing tables (`student`, `bridge`, `chess`, `music`).
3. **Read-Only Queries:** The agent is designed to execute data-retrieval (`SELECT`) operations only.
4. **Specific Column Names:** If querying specific details (e.g., scores, sex, classes), specify them clearly if needed.
"""
)

st.title("🤖 Natural Language to SQL Agent")
st.write(
    "Ask any question about your database in plain English. The AI will convert it into a SQL query and retrieve the results."
)


# Initialize NVIDIA API Client
def get_nvidia_client():
    api_key = os.getenv("NVIDIA_API_KEY")

    if not api_key:
        st.error(
            f"NVIDIA_API_KEY is missing! Checked file path: {ENV_PATH}"
        )
        st.stop()

    # Ensure base_url is exact: "https://integrate.api.nvidia.com/v1"
    return OpenAI(
        api_key=api_key,
        base_url="https://integrate.api.nvidia.com/v1",
    )

# Database Connection Setup
def connect_to_sql():
    host = st.secrets.get("MYSQL_HOST", os.getenv("MYSQL_HOST"))
    port = int(st.secrets.get("MYSQL_PORT", os.getenv("MYSQL_PORT", 3306)))
    user = st.secrets.get("MYSQL_USER", os.getenv("MYSQL_USER"))
    password = st.secrets.get("MYSQL_PASSWORD", os.getenv("MYSQL_PASSWORD"))
    database = st.secrets.get("MYSQL_DATABASE", os.getenv("MYSQL_DATABASE"))

    return mysql.connector.connect(
        host=host, user=user, password=password, database=database,temperature=0.0,max_tokens=150,connection_timeout=60
    )


# Final Database Schema Definition matching exact MySQL Workbench columns
SCHEMA = """The schema of the database is as follows:
TABLE_NAME  COLUMN_NAME DATA_TYPE   COLUMN_TYPE
bridge      ID          int         int
bridge      FullName    text        text
bridge      Sex         text        text
bridge      Class       text        text
chess       ID          int         int
chess       FullName    text        text
chess       Sex         text        text
chess       Class       text        text
music       ID          int         int
music       Type        text        text
student     ID          int         int
student     FullName    varchar     varchar(100)
student     DOB         varchar     varchar(20)
student     Sex         varchar     varchar(10)
student     Class       varchar     varchar(10)
student     HCode       varchar     varchar(10)
student     DCode       varchar     varchar(10)
student     Remission   binary      binary(1)
student     MTest       int         int
student     PTest       int         int
"""

# Function to translate Natural Language into SQL Query
def generate_sql_query(user_question):
    client = get_nvidia_client()

    prompt = (
        f"Given the following database schema:\n{SCHEMA}\n"
        f"Convert this question into a SQL query. Return ONLY the raw SQL query without any explanation, "
        f"markdown formatting, or code blocks:\n{user_question}"
    )

    response = client.chat.completions.create(
        model="nvidia/nemotron-3.5-lightning-30b-a3b",
        messages=[{"role": "user", "content": prompt}],
    )

    sql_query = response.choices[0].message.content.strip()
    # Clean up standard markdown backticks if returned by the LLM
    sql_query = sql_query.replace("```sql", "").replace("```", "").strip()
    return sql_query


# Streamlit Input UI (Generic placeholder)
user_query = st.text_input(
    "Enter your question:", placeholder="Type your query here..."
)

if st.button("Ask Database", type="primary"):
    if user_query.strip():
        with st.spinner("Generating SQL query..."):
            try:
                # Step 1: Generate SQL from Natural Language
                sql_query = generate_sql_query(user_query)
                st.subheader("Generated SQL Query:")
                st.code(sql_query, language="sql")

                # Step 2: Execute SQL Query against MySQL
                with st.spinner("Executing query against database..."):
                    conn = connect_to_sql()
                    df = pd.read_sql_query(sql_query, conn)
                    conn.close()

                    # Convert raw binary/byte columns to display 'BLOB' string matching MySQL Workbench
                for col in df.columns:
                    df[col] = df[col].apply(
                        lambda x: "BLOB" if isinstance(x, (bytes, bytearray)) else x
                    )

                # Step 3: Display Data Results
                st.subheader("Database Results:")
                if not df.empty:
                    st.dataframe(df, use_container_width=True)
                else:
                    st.info("Query executed successfully, but returned no rows.")

            except Exception as e:
                st.error(f"Error processing your query: {e}")
    else:
        st.warning("Please enter a question before submitting.")

