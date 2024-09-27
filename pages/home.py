import streamlit as st

def app():
    st.title("GAIA OpenAI Model Evaluator")
    
    st.markdown("""
    <div style="background-color: rgba(255, 255, 255, 0.7); padding: 20px; border-radius: 10px;">
        <h2 style="color: #1e3d59;">Welcome to the GAIA OpenAI Model Evaluator</h2>
        <p>This tool allows you to:</p>
        <ul>
            <li>Select a validation test case from the GAIA dataset</li>
            <li>Evaluate the OpenAI model's performance</li>
            <li>Compare the model's answers with expected answers</li>
            <li>Modify annotator steps and re-evaluate the model</li>
            <li>Provide feedback and generate reports with visualizations</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div style="background-color: rgba(255, 255, 255, 0.7); padding: 20px; border-radius: 10px; margin-top: 20px;">
        <h3 style="color: #1e3d59;">Getting Started</h3>
        <p>Use the navigation sidebar to explore different functionalities:</p>
        <ol>
            <li><strong>Test Case & Annotator Modification:</strong> Select and evaluate test cases</li>
            <li><strong>Reports & Visualization:</strong> View performance reports and visualizations</li>
        </ol>
    </div>
    """, unsafe_allow_html=True)
