import streamlit as st
from models.benchmark_results import create_benchmark_result
from models.test_cases import fetch_all_tests
from utils.openai_utils import invoke_openai_api

def app():
    # Initialize session state variables
    if "deny_answer" not in st.session_state:
        st.session_state.deny_answer = False
    if "annotator_steps" not in st.session_state:
        st.session_state.annotator_steps = ""
    if "model_answer" not in st.session_state:
        st.session_state.model_answer = ""
    if "re_evaluated_answer" not in st.session_state:
        st.session_state.re_evaluated_answer = None
    if "re_evaluated_status" not in st.session_state:
        st.session_state.re_evaluated_status = None

    st.title("Test Case Selection & Annotator Modification")

    # Load all test cases
    metadata = fetch_all_tests()

    # Let user select a test case
    test_cases = [f"Test Case {i + 1}" for i in range(len(metadata))]
    selected_case = st.selectbox("Select a Test Case", test_cases, key="test_case_select")

    # Display selected case metadata
    selected_metadata = metadata[int(selected_case.split()[-1]) - 1]

    context = selected_metadata.task_id
    st.subheader("Selected Case Information")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Context**: {context}")
        question = st.text_area("Question", value=selected_metadata.question, height=100, key="question_area")
    with col2:
        expected_answer = selected_metadata.answer
        st.markdown("**Expected Answer:**")
        st.markdown(f"<div style='background-color: rgba(255, 255, 255, 0.7); padding: 10px; border-radius: 5px;'>{expected_answer}</div>", unsafe_allow_html=True)
    
    file_path = selected_metadata.file_path
    annotator_steps = selected_metadata.metadata_steps

    # Show the current annotator steps in the session state
    st.session_state.annotator_steps = annotator_steps

    # Selectbox for model selection
    model_options = ["gpt-4o-2024-05-13", "gpt-4o-mini-2024-07-18"]
    selected_model = st.selectbox("Select a Model", model_options, key="model_select")

    # Get answer from OpenAI model
    if st.button("Get OpenAI Answer", key="get_answer_button"):
        with st.spinner("Fetching answer from OpenAI..."):
            try:
                st.session_state.model_answer = invoke_openai_api(
                    question=question,
                    file_path=file_path,
                    model=selected_model
                )
                st.markdown("**Model Answer:**")
                st.markdown(f"<div style='background-color: rgba(255, 255, 255, 0.7); padding: 10px; border-radius: 5px;'>{st.session_state.model_answer}</div>", unsafe_allow_html=True)

                if expected_answer.strip().lower() in st.session_state.model_answer.strip().lower():
                    st.success("The model's answer matches the expected answer!")
                else:
                    st.error("The model's answer is incorrect.")

            except Exception as e:
                st.error(f"Error fetching the OpenAI answer: {e}")

    # Accept or deny the answer
    if st.session_state.model_answer:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Accept Answer", key="accept_button"):
                try:
                    create_benchmark_result(
                        llm_answer=st.session_state.model_answer,
                        is_cot=False,
                        model_name=selected_model,
                        prompted_question=question,
                        task_id=context,
                        status="Accepted" if expected_answer.strip().lower() in st.session_state.model_answer.strip().lower() else "Failed",
                    )
                    st.success("Answer accepted and stored successfully!")
                except Exception as e:
                    st.error(f"Error storing the accepted answer: {e}")

        with col2:
            if st.button("Deny Answer", key="deny_button"):
                st.session_state.deny_answer = True
                try:
                    create_benchmark_result(
                        llm_answer=st.session_state.model_answer,
                        is_cot=False,
                        model_name=selected_model,
                        prompted_question=question,
                        task_id=context,
                        status="Failed",
                    )
                    # st.success("Answer denied and stored successfully!")
                except Exception as e:
                    st.error(f"Error storing the denied answer: {e}")

    # Annotator Steps Modification (conditional display)
    if st.session_state.deny_answer:
        st.subheader("Modify Annotator Steps")
        modified_steps = st.text_area("Annotator Steps", value=st.session_state.annotator_steps, key="modified_steps")

        if st.button("Re-evaluate with Modified Steps", key="re_evaluate_button"):
            with st.spinner("Re-evaluating with modified steps..."):
                combined_question = f"{question}\n\n{modified_steps}"
                
                try:
                    st.session_state.re_evaluated_answer = invoke_openai_api(
                        question=combined_question,
                        file_path=file_path,
                        model=selected_model
                    )
                    st.markdown("**Model Answer After Re-evaluation:**")
                    st.markdown(f"<div style='background-color: rgba(255, 255, 255, 0.7); padding: 10px; border-radius: 5px;'>{st.session_state.re_evaluated_answer}</div>", unsafe_allow_html=True)

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

        if st.session_state.re_evaluated_answer is not None:
            col3, col4 = st.columns(2)
            with col3:
                if st.button("Accept Re-evaluated Answer", key="accept_re_evaluated_button"):
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
                        st.session_state.re_evaluated_answer = None
                        st.session_state.re_evaluated_status = None
                    except Exception as e:
                        st.error(f"Error storing the accepted answer: {e}")

            with col4:
                if st.button("Deny Re-evaluated Answer", key="deny_re_evaluated_button"):
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
                        st.session_state.re_evaluated_answer = None
                        st.session_state.re_evaluated_status = None
                    except Exception as e:
                        st.error(f"Error storing the denied answer: {e}")