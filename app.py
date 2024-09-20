import streamlit as st
# import json
# import openai  # Ensure you install openai using `pip install openai`
import pandas as pd
import matplotlib.pyplot as plt

# # Set up OpenAI API key
# openai.api_key = 'your_openai_api_key'

# # Load GAIA dataset metadata
# def load_metadata():
#     with open('metadata.jsonl', 'r') as f:
#         return [json.loads(line) for line in f.readlines()]

# # Send question to OpenAI model and get response
# def query_openai_model(context, question):
#     response = openai.Completion.create(
#         engine="text-davinci-003",  # Or any other model you plan to use
#         prompt=f"Context: {context}\nQuestion: {question}\nAnswer:",
#         max_tokens=150
#     )
#     return response.choices[0].text.strip()

# # Compare model output with expected answer
# def compare_answers(model_answer, expected_answer):
#     return model_answer == expected_answer

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
        question = selected_metadata['question']
        expected_answer = selected_metadata['expected_answer']
        
        st.subheader("Selected Case Information")
        st.write(f"**Context**: {context}")
        st.write(f"**Question**: {question}")
        
        # Get answer from OpenAI model
        if st.button("Get OpenAI Answer"):
            model_answer = query_openai_model(context, question)
            st.write(f"**Model Answer**: {model_answer}")
            st.write(f"**Expected Answer**: {expected_answer}")
            
            # Comparison
            if compare_answers(model_answer, expected_answer):
                st.success("The model's answer matches the expected answer!")
            else:
                st.error("The model's answer is incorrect.")
    
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
