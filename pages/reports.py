import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from models.benchmark_results import fetch_benchmark_results

def app():
    st.title("Evaluation Reports & Visualization")

    # Fetch benchmark results from the database
    benchmark_results = fetch_benchmark_results()

    if not benchmark_results:
        st.warning("No benchmark results found.")
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
        st.subheader("Raw Data")
        st.dataframe(df)

        # Use Seaborn to set the style
        sns.set(style='darkgrid')  # You can change to other styles like 'darkgrid', 'white', etc.

        # Generate a simple bar plot for Status
        st.subheader("Benchmark Results Summary")
        fig, ax = plt.subplots(figsize=(10, 6))
        status_counts = df['Status'].value_counts()
        sns.barplot(x=status_counts.index, y=status_counts.values, ax=ax)
        ax.set_title("Status Distribution", fontsize=16)
        ax.set_xlabel("Status", fontsize=12)
        ax.set_ylabel("Count", fontsize=12)
        st.pyplot(fig)

        # Pie chart of Status
        st.subheader("Pie Chart: Status Distribution")
        fig2, ax2 = plt.subplots(figsize=(8, 8))
        ax2.pie(
            status_counts,
            labels=status_counts.index,
            autopct="%1.1f%%",
            startangle=90,
            colors=sns.color_palette("pastel"),
        )
        ax2.set_title("Status Distribution", fontsize=16)
        st.pyplot(fig2)

        # Bar chart showing performance per model
        st.subheader("Model-wise Status Distribution")
        fig4, ax4 = plt.subplots(figsize=(12, 6))
        model_status = (
            df.groupby("Model")["Status"].value_counts().unstack().fillna(0)
        )
        model_status.plot(kind="bar", stacked=True, ax=ax4)
        ax4.set_title("Model-wise Performance", fontsize=16)
        ax4.set_xlabel("Models", fontsize=12)
        ax4.set_ylabel("Count of Status", fontsize=12)
        plt.legend(title="Status", bbox_to_anchor=(1.05, 1), loc='upper left')
        st.pyplot(fig4)

        # Heatmap of model performance
        st.subheader("Heatmap: Model Performance")
        fig5, ax5 = plt.subplots(figsize=(10, 8))
        heatmap_data = df.pivot_table(index="Model", columns="Status", values="Test Case", aggfunc="count", fill_value=0)
        sns.heatmap(heatmap_data, annot=True, cmap="Blues", ax=ax5)
        ax5.set_title("Model Performance Heatmap", fontsize=16)
        st.pyplot(fig5)

