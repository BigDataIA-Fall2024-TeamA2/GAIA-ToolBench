import os
from dotenv import load_dotenv
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from sqlalchemy.orm import sessionmaker
from models.db import DatabaseSession
from models.test_cases import fetch_all_tests, fetch_test_by_id  # Import functions from test_cases
from llm_utils.openai_utils import create_prompt, get_response

# Load environment variables from .env file
load_dotenv()

# Function to handle navigation between pages
def main():
    # Initialize session state for page navigation and annotator steps
    if 'page' not in st.session_state:
        st.session_state.page = "Home"
    if 'deny_answer' not in st.session_state:
        st.session_state.deny_answer = False
    if 'annotator_steps' not in st.session_state:
        st.session_state.annotator_steps = ""

    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox("Go to", ["Home", "Test Case & Annotator Modification", "Feedback", "Reports & Visualization"])
    
    # Set the page in session state
    st.session_state.page = page

    # Home page
    if st.session_state.page == "Home":
        st.title("GAIA OpenAI Model Evaluator")
        st.write("""
            Welcome to the GAIA OpenAI Model Evaluator. This tool allows you to:
            - Select a validation test case from the GAIA dataset
            - Evaluate the OpenAI model's performance
            - Compare the model's answers with expected answers
            - Modify annotator steps and re-evaluate the model
            - Provide feedback and generate reports with visualizations.
        """)

    # Test Case & Annotator Modification page
    elif st.session_state.page == "Test Case & Annotator Modification":
        st.title("Test Case Selection & Annotator Modification")
        
        # Load all test cases
        metadata = fetch_all_tests()  # Fetch metadata from the database
        
        # Let user select a test case
        test_cases = [f"Test Case {i + 1}" for i in range(len(metadata))]
        selected_case = st.selectbox("Select a Test Case", test_cases)
        
        # Display selected case metadata
        selected_metadata = metadata[int(selected_case.split()[-1]) - 1]
        
        context = selected_metadata.task_id  # Assuming 'question' is what you want to display
        st.subheader("Selected Case Information")
        st.write(f"**Context**: {context}")
        question = st.text_area("Question", value=selected_metadata.question, height=100)
        expected_answer = selected_metadata.answer  # Assuming 'answer' is the expected answer
        file_path = selected_metadata.file_path
        annotator_steps = selected_metadata.metadata_steps
        
        # Show the current annotator steps in the session state
        st.session_state.annotator_steps = annotator_steps
        
        

        # Get answer from OpenAI model
        if st.button("Get OpenAI Answer"):
            try:
                # Send context and question to the OpenAI API
                if file_path is not None:
                    prompt = create_prompt(question)
                else:
                    prompt = create_prompt(question, file_path)
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

        # Display expected answer after getting the model's answer
        st.write(f"**Expected Answer**: {expected_answer}")

        # Side-by-side buttons for accepting or denying the answer
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Accept Answer"):
                # Here you could implement logic to save the acceptance
                st.success("Answer accepted!")

        with col2:
            if st.button("Deny Answer"):
                # Set session state to indicate that the answer was denied
                st.session_state.deny_answer = True
                
        # Annotator Steps Modification (conditional display)
        if st.session_state.get('deny_answer', False):
            st.subheader("Modify Annotator Steps")
            modified_steps = st.text_area("Annotator Steps", value=st.session_state.annotator_steps)
            
            # Option to re-evaluate the model
            if st.button("Re-evaluate with Modified Steps"):
                st.write("Re-evaluating with modified steps...")
                # Placeholder for actual re-evaluation logic
                st.session_state.deny_answer = False  # Reset the state after re-evaluation

    # Feedback page
    elif st.session_state.page == "Feedback":
        st.title("User Feedback")
        
        feedback = st.text_area("Enter your feedback")
        if st.button("Submit Feedback"):
            # Store the feedback (you can use a database or file storage)
            st.success("Feedback submitted successfully!")
    
    # Reports & Visualization page
    elif st.session_state.page == "Reports & Visualization":
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

