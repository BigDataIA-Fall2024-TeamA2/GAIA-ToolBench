import os
from dotenv import load_dotenv
import psycopg2
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from LLM.OpenAIcalls import create_prompt, get_response

# Load environment variables from .env file
load_dotenv()

# Function to get a PostgreSQL connection
def get_postgres_conn():
    conn_string = os.getenv('POSTGRES_CONN_STRING')
    if not conn_string:
        raise ValueError("Postgres connection string not set in environment variables.")
    
    conn = psycopg2.connect(conn_string)
    return conn

# Function to load metadata from the PostgreSQL database
def load_metadata():
    conn = get_postgres_conn()
    cur = conn.cursor()
    
    cur.execute("SELECT * FROM test_cases;")
    rows = cur.fetchall()
    cur.close()
    conn.close()

    metadata = []
    for row in rows:
        metadata.append({
            'id': row[0],
            'context': row[1],
            'question': row[2],
            'expected_answer': row[4],
            'annotator_steps': row[5],
            'file_path' :row[6]
        })
    
    return metadata

# Function to handle navigation between pages
def main():
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox("Go to", ["Home", "Test Case Selection", "Annotator Modification", "Feedback", "Reports & Visualization"])

    # Home page
    if page == "Home":
        st.title("GAIA OpenAI Model Evaluator")
        st.write("""
            Welcome to the GAIA OpenAI Model Evaluator. This tool allows you to:
            - Select a validation test case from the GAIA dataset
            - Evaluate the OpenAI model's performance
            - Compare the model's answers with expected answers
            - Modify annotator steps and re-evaluate the model
            - Provide feedback and generate reports with visualizations.
        """)

    # Test Case Selection page
    elif page == "Test Case Selection":
        st.title("Test Case Selection & Model Evaluation")
        
        # Load the GAIA metadata
        metadata = load_metadata()
        
        # Let user select a test case
        test_cases = [f"Test Case {i}" for i in range(len(metadata))]
        selected_case = st.selectbox("Select a Test Case", test_cases)
        
        # Display selected case metadata
        selected_metadata = metadata[int(selected_case.split()[-1])]
        context = selected_metadata['context']
        question = st.text_area("Question", value=selected_metadata['question'], height=100)
        expected_answer = st.text_input("Expected Answer", value=selected_metadata['expected_answer'])
        file_path = selected_metadata['file_path']
        st.subheader("Selected Case Information")
        st.write(f"**Context**: {context}")
        
        # Get answer from OpenAI model
        if st.button("Get OpenAI Answer"):

            try:
                # Send context and question to the OpenAI API
                if file_path != None :
                    prompt = create_prompt(question)
                    model_answer = get_response(prompt)
                else:
                    prompt = create_prompt(question,file_path)
                    model_answer = get_response(prompt)        
                
                # Display the model's answer
                st.write(f"**Model Answer**: {model_answer}")
                
                # Compare with expected answer
                if model_answer.strip().lower() == expected_answer.strip().lower():
                    st.success("The model's answer matches the expected answer!")
                else:
                    st.error("The model's answer is incorrect.")
            except Exception as e:
                st.error(f"Error fetching the OpenAI answer: {e}")

    # Annotator Modification page
    elif page == "Annotator Modification":
        st.title("Modify Annotator Steps & Re-evaluate")
        
        # Load the GAIA metadata
        metadata = load_metadata()
        
        # Let user select a test case for modification
        test_cases = [f"Test Case {i}" for i in range(len(metadata))]
        selected_case = st.selectbox("Select a Test Case", test_cases)
        
        selected_metadata = metadata[int(selected_case.split()[-1])]
        annotator_steps = selected_metadata['annotator_steps']
        
        st.subheader("Modify Annotator Steps")
        modified_steps = st.text_area("Annotator Steps", value=annotator_steps)
        
        # Option to re-evaluate the model
        if st.button("Re-evaluate with Modified Steps"):
            st.write("Re-evaluating with modified steps...")
            # Placeholder for actual re-evaluation logic
    
    # Feedback page
    elif page == "Feedback":
        st.title("User Feedback")
        
        feedback = st.text_area("Enter your feedback")
        if st.button("Submit Feedback"):
            # Store the feedback (you can use a database or file storage)
            st.success("Feedback submitted successfully!")
    
    # Reports & Visualization page
    elif page == "Reports & Visualization":
        st.title("Evaluation Reports & Visualization")
        
        # Placeholder for feedback and performance visualization
        feedback_data = pd.DataFrame({
            'Test Case': ['Case 1', 'Case 2', 'Case 3'],
            'Correct': [2, 1, 3],
            'Incorrect': [1, 2, 1]
        })
        st.write(feedback_data)

        # Generate a bar plot for correct/incorrect answers
        fig, ax = plt.subplots()
        feedback_data.set_index('Test Case').plot(kind='bar', ax=ax)
        st.pyplot(fig)

# Run the Streamlit app
if __name__ == "__main__":
    main()
