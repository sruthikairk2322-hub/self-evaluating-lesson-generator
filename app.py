
import os
from pathlib import Path

import streamlit as st

from lesson_agent.config import load_settings
from lesson_agent.graph import Pipeline


st.set_page_config(
    page_title="AI Lesson Content Generator",
    page_icon="📚",
    layout="wide"
)

st.title("📚 AI Lesson Content Generator")
st.caption(
    "Generate, evaluate, reject and improve lesson content "
    "using LangGraph and Ollama."
)

st.sidebar.header("Configuration")

provider = "ollama"

model = st.sidebar.text_input(
    "Ollama Model",
    value="llama3.2"
)

max_retries = st.sidebar.slider(
    "Maximum retries",
    min_value=1,
    max_value=2,
    value=2
)

st.sidebar.success("Using local Ollama model")

st.header("Generate a Lesson")

topic = st.text_input(
    "Enter your lesson topic",
    value="Introduction to RAG (Retrieval-Augmented Generation)"
)

tamper_option = st.selectbox(
    "Demonstration mode",
    [
        "No deliberate error",
        "Inject subtle factual error"
    ]
)

generate_button = st.button(
    "Generate Lesson",
    type="primary",
    use_container_width=True
)

if generate_button:

    if not topic.strip():
        st.error("Please enter a lesson topic.")
        st.stop()

    os.environ["LLM_PROVIDER"] = provider
    os.environ["GENERATOR_MODEL"] = model
    os.environ["EVALUATOR_MODEL"] = model

    settings = load_settings(
        provider=provider,
        max_retries=max_retries
    )

    logs = []
    log_area = st.empty()

    def capture_log(message):
        logs.append(str(message))
        log_area.code(
            "\n".join(logs[-100:]),
            language="text"
        )

    tamper = (
        "subtle_fact"
        if tamper_option == "Inject subtle factual error"
        else None
    )

    try:
        with st.status(
            "Running the LangGraph workflow...",
            expanded=True
        ) as workflow_status:

            pipeline = Pipeline(
                settings,
                log=capture_log
            )

            result = pipeline.run(
                topic,
                tamper=tamper
            )

            workflow_status.update(
                label="Workflow completed",
                state="complete",
                expanded=False
            )

        st.divider()
        st.header("Evaluation Results")

        history = result.get("history", [])

        if history:
            last = history[-1]

            col1, col2, col3 = st.columns(3)

            col1.metric(
                "Attempts",
                len(history)
            )

            col2.metric(
                "Checks passed",
                len(last["checks"]) - last["n_failed"]
            )

            col3.metric(
                "Checks failed",
                last["n_failed"]
            )

            if result["status"] == "shipped":
                st.success("Lesson approved and shipped!")
            else:
                st.warning(
                    "Lesson requires human review. "
                    "It has not been approved."
                )

            st.subheader("Rubric Evaluation")

            for check in last["checks"]:
                if check["passed"]:
                    st.success(
                        f"✓ {check['id']} — Passed"
                    )
                else:
                    st.error(
                        f"✗ {check['id']} — {check['reason']}"
                    )

        st.divider()
        st.header("Generated Lesson")

        lesson = result.get("final_lesson", "")

        st.markdown(lesson)

        if lesson:
            st.download_button(
                "Download Lesson",
                data=lesson,
                file_name="lesson.md",
                mime="text/markdown"
            )

        out_dir = Path(result["out_dir"])

        rejection_file = out_dir / "rejection_log.md"

        if rejection_file.exists():
            rejection_log = rejection_file.read_text(
                encoding="utf-8"
            )

            with st.expander("View Rejection Log"):
                st.markdown(rejection_log)

            st.download_button(
                "Download Rejection Log",
                data=rejection_log,
                file_name="rejection_log.md",
                mime="text/markdown"
            )

        st.caption(f"Run ID: {result['run_id']}")
        st.caption(f"Output folder: {out_dir}")

    except Exception as error:
        st.error(f"Workflow failed: {error}")
        st.exception(error)


st.divider()

st.caption(
    "Powered by Python, LangGraph, Ollama and Streamlit"
)
