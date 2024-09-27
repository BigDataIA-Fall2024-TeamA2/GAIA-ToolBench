import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from models.benchmark_results import (
    fetch_benchmark_results,
    create_benchmark_result,
)
from models.test_cases import fetch_all_tests
from utils.openai_utils import invoke_openai_api
import datetime

# Load environment variables from .env file
load_dotenv()

# Function to handle navigation between pages
def main():
    # Initialize session state for page navigation and annotator steps
    if "page" not in st.session_state:
        st.session_state.page = "Home"
    if "deny_answer" not in st.session_state:
        st.session_state.deny_answer = False
    if "annotator_steps" not in st.session_state:
        st.session_state.annotator_steps = ""
    if "model_answer" not in st.session_state:
        st.session_state.model_answer = ""
    # New session state variables for re-evaluation
    if "re_evaluated_answer" not in st.session_state:
        st.session_state.re_evaluated_answer = None
    if "re_evaluated_status" not in st.session_state:
        st.session_state.re_evaluated_status = None

    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Go to",
        ["Home", "Test Case & Annotator Modification", "Reports & Visualization"],
    )

    # Set the page in session state
    st.session_state.page = page

    # Home page
    if st.session_state.page == "Home":
        st.title("GAIA OpenAI Model Evaluator")
        st.write(
            """
            Welcome to the GAIA OpenAI Model Evaluator. This tool allows you to:
            - Select a validation test case from the GAIA dataset
            - Evaluate the OpenAI model's performance
            - Compare the model's answers with expected answers
            - Modify annotator steps and re-evaluate the model
            - Provide feedback and generate reports with visualizations.
        """
        )

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

        context = selected_metadata.task_id  # Assuming 'task_id' is what you want to display
        st.subheader("Selected Case Information")
        st.write(f"**Context**: {context}")
        question = st.text_area("Question", value=selected_metadata.question, height=100)
        expected_answer = selected_metadata.answer  # Assuming 'answer' is the expected answer
        file_path = selected_metadata.file_path
        annotator_steps = selected_metadata.metadata_steps

        # Show the current annotator steps in the session state
        st.session_state.annotator_steps = annotator_steps

        # Selectbox for model selection
        model_options = ["gpt-4o-2024-05-13", "gpt-4o-mini-2024-07-18"]
        selected_model = st.selectbox("Select a Model", model_options)

        # Get answer from OpenAI model
        if st.button("Get OpenAI Answer"):
            try:
                # Send context and question to the OpenAI API
                st.session_state.model_answer = invoke_openai_api(
                    question=question,
                    file_path=file_path,
                    model=selected_model  # Pass selected model
                )
                # Display the model's answer
                st.write(f"**Model Answer**: {st.session_state.model_answer}")

                # Compare with expected answer
                if expected_answer.strip().lower() in st.session_state.model_answer.strip().lower():
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
                # Save the accepted answer in the benchmark_results table
                try:
                    create_benchmark_result(
                        llm_answer=st.session_state.model_answer,
                        is_cot=False,
                        model_name=selected_model,  # Use the selected model
                        prompted_question=question,
                        task_id=context,
                        status="Accepted" if expected_answer.strip().lower() in st.session_state.model_answer.strip().lower() else "Failed",
                    )
                    st.success("Answer accepted and stored successfully!")  # Confirmation message
                except Exception as e:
                    st.error(f"Error storing the accepted answer: {e}")

        with col2:
            if st.button("Deny Answer"):
                # Set session state to indicate that the answer was denied
                st.session_state.deny_answer = True
                try:
                    create_benchmark_result(
                        llm_answer=st.session_state.model_answer,
                        is_cot=False,
                        model_name=selected_model,  # Use the selected model
                        prompted_question=question,
                        task_id=context,
                        status="Failed",
                    )
                    # st.success("Answer denied and stored successfully!")
                except Exception as e:
                    st.error(f"Error storing the denied answer: {e}")

        # Annotator Steps Modification (conditional display)
        if st.session_state.get("deny_answer", False):
            st.subheader("Modify Annotator Steps")
            modified_steps = st.text_area("Annotator Steps", value=st.session_state.annotator_steps)

            # Option to re-evaluate the model
            if st.button("Re-evaluate with Modified Steps"):
                st.write("Re-evaluating with modified steps...")

                # Create the combined question with metadata steps
                combined_question = f"{question}\n\n{modified_steps}"
                
                try:
                    # Send combined question with modified steps to the OpenAI API
                    st.session_state.re_evaluated_answer = invoke_openai_api(
                        question=combined_question,
                        file_path=file_path,
                        model=selected_model
                    )
                    # Display the model's new answer
                    st.write(f"**Model Answer After Re-evaluation**: {st.session_state.re_evaluated_answer}")

                    # Compare with expected answer
                    if expected_answer.strip().lower() in st.session_state.re_evaluated_answer.strip().lower():
                        st.success("The model's answer matches the expected answer!")
                        st.session_state.re_evaluated_status = "Accepted"
                    else:
                        st.error("The model's answer is incorrect.")
                        st.session_state.re_evaluated_status = "Failed"

                except Exception as e:
                    st.error(f"Error fetching the OpenAI answer: {e}")
                    st.session_state.re_evaluated_answer = None
                    st.session_state.re_evaluated_status = None

            # Display accept/deny buttons only if re-evaluation has been performed
            if st.session_state.re_evaluated_answer is not None:
                col3, col4 = st.columns(2)
                with col3:
                    if st.button("Accept Re-evaluated Answer"):
                        try:
                            create_benchmark_result(
                                llm_answer=st.session_state.re_evaluated_answer,
                                is_cot=False,
                                model_name=selected_model,
                                prompted_question=question,
                                task_id=context,
                                status=st.session_state.re_evaluated_status,
                            )
                            st.success("Re-evaluated answer accepted and stored successfully!")
                            # Reset the re-evaluation state
                            st.session_state.re_evaluated_answer = None
                            st.session_state.re_evaluated_status = None
                        except Exception as e:
                            st.error(f"Error storing the accepted answer: {e}")

                with col4:
                    if st.button("Deny Re-evaluated Answer"):
                        try:
                            create_benchmark_result(
                                llm_answer=st.session_state.re_evaluated_answer,
                                is_cot=False,
                                model_name=selected_model,
                                prompted_question=question,
                                task_id=context,
                                status="Failed",
                            )
                            st.success("Re-evaluated answer denied and stored.")
                            # Reset the re-evaluation state
                            st.session_state.re_evaluated_answer = None
                            st.session_state.re_evaluated_status = None
                        except Exception as e:
                            st.error(f"Error storing the denied answer: {e}")

    # Reports & Visualization page
    elif st.session_state.page == "Reports & Visualization":
        st.title("Evaluation Reports & Visualization")

        # Fetch benchmark results from the database
        benchmark_results = fetch_benchmark_results()

        if not benchmark_results:
            st.write("No benchmark results found.")
        else:
            # Convert results to a DataFrame
            data = [
                {
                    "Test Case": result.task_id,
                    "Model": result.model_name,
                    "LLM Answer": result.llm_answer,
                    "Question": result.prompted_question,
                    "Status": result.status,
                    "Timestamp": result.created_at,
                }
                for result in benchmark_results
            ]

            df = pd.DataFrame(data)

            # Display the DataFrame
            st.dataframe(df)

            # Generate a simple bar plot for Status (e.g., Correct vs Incorrect)
            status_counts = df['Status'].value_counts()
            plt.figure(figsize=(10, 5))
            plt.bar(status_counts.index, status_counts.values)
            plt.title("Benchmark Results Summary")
            plt.xlabel("Status")
            plt.ylabel("Count")
            st.pyplot(plt)

            # Pie chart of Status
            st.subheader("Pie Chart: Status Distribution")
            fig2, ax2 = plt.subplots()
            ax2.pie(
                status_counts,
                labels=status_counts.index,
                autopct="%1.1f%%",
                startangle=90,
            )
            ax2.axis("equal")  # Equal aspect ratio ensures the pie is drawn as a circle
            st.pyplot(fig2)

            # Histogram for model performance distribution
            st.subheader("Histogram: Model Performance")
            fig3, ax3 = plt.subplots()
            df["Model"].value_counts().plot(
                kind="hist", bins=10, ax=ax3, color="skyblue"
            )
            ax3.set_title("Distribution of Models in the Benchmark")
            ax3.set_xlabel("Model Count")
            ax3.set_ylabel("Frequency")
            st.pyplot(fig3)

            # Bar chart showing performance per model
            st.subheader("Model-wise Status Distribution")
            fig4, ax4 = plt.subplots()
            model_status = (
                df.groupby("Model")["Status"].value_counts().unstack().fillna(0)
            )
            model_status.plot(kind="bar", stacked=True, ax=ax4)
            ax4.set_title("Model-wise Performance")
            ax4.set_xlabel("Models")
            ax4.set_ylabel("Count of Status (Correct/Incorrect)")
            st.pyplot(fig4)

if __name__ == "__main__":
    main()