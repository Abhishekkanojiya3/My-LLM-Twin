import os
import sys
from pathlib import Path

# To mimic using multiple Python modules, such as 'core' and 'feature_pipeline',
# we will add the './src' directory to the PYTHONPATH. This is not intended for
# production use cases but for development and educational purposes.
ROOT_DIR = str(Path(__file__).parent.parent)
sys.path.append(ROOT_DIR)

# core.db.mongo connects eagerly at import time, so settings.patch_localhost()
# (which runs after the core.config import below) is too late to affect it.
# Set the localhost overrides as env vars before core is imported at all.
os.environ.setdefault(
    "MONGO_DATABASE_HOST",
    "mongodb://localhost:30001,localhost:30002,localhost:30003/?replicaSet=my-replica-set",
)
os.environ.setdefault("QDRANT_DATABASE_HOST", "localhost")
os.environ.setdefault("RABBITMQ_HOST", "localhost")

from core.config import settings
from llm_twin import LLMTwin

settings.patch_localhost()


import gradio as gr
from inference_pipeline.llm_twin import LLMTwin

llm_twin = LLMTwin(mock=False)


def predict(message: str, history: list[dict], author: str) -> str:
    """
    Generates a response using the LLM Twin, simulating a conversation with your digital twin.

    Args:
        message (str): The user's input message or question.
        history (list[dict]): Previous conversation history between user and twin.
        author (str): Personal context about the user to help personalize responses.

    Returns:
        str: The LLM Twin's generated response.
    """

    query = f"I am {author}. Write about: {message}"
    try:
        response = llm_twin.generate(
            query=query, enable_rag=True, sample_for_evaluation=False
        )
    except Exception as exc:
        return (
            "The local UI is running, but the model request failed. "
            "Check that GROQ_API_KEY is set to a valid Groq API key in your .env file. "
            f"Details: {exc}"
        )

    return response["answer"]


THEME = gr.themes.Soft(
    primary_hue="indigo",
    secondary_hue="purple",
    neutral_hue="slate",
    radius_size="lg",
    font=[gr.themes.GoogleFont("Inter"), "ui-sans-serif", "system-ui", "sans-serif"],
).set(
    body_background_fill="linear-gradient(135deg, #f5f3ff 0%, #ede9fe 100%)",
    body_background_fill_dark="linear-gradient(135deg, #0f0a2e 0%, #1e1b4b 100%)",
    block_background_fill="rgba(255, 255, 255, 0.85)",
    block_radius="20px",
    block_shadow="0 10px 30px rgba(79, 70, 229, 0.18)",
    button_primary_background_fill="linear-gradient(90deg, #6366f1, #a855f7)",
    button_primary_background_fill_hover="linear-gradient(90deg, #4f46e5, #9333ea)",
    button_primary_shadow="0 6px 16px rgba(99, 102, 241, 0.4)",
    button_primary_text_color="white",
    input_background_fill="rgba(255, 255, 255, 0.9)",
    input_radius="14px",
    input_shadow="0 2px 8px rgba(79, 70, 229, 0.12)",
)

CSS = """
.gradio-container {
    max-width: 880px !important;
    margin: 0 auto !important;
}
#twin-header {
    text-align: center;
    padding: 0.5em 0 0.2em 0;
}
#twin-header h1 {
    font-size: 2.1rem;
    font-weight: 800;
    background: linear-gradient(90deg, #6366f1, #a855f7);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.15em;
}
#twin-header p {
    color: #6b7280;
    font-size: 1rem;
}
#twin-chatbot {
    border-radius: 20px !important;
    box-shadow: 0 14px 34px rgba(79, 70, 229, 0.2) !important;
}
#twin-chatbot .message.user {
    background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
    color: white !important;
    border-radius: 18px 18px 4px 18px !important;
    box-shadow: 0 4px 12px rgba(99, 102, 241, 0.35);
}
#twin-chatbot .message.bot {
    background: rgba(255, 255, 255, 0.95) !important;
    border-radius: 18px 18px 18px 4px !important;
    box-shadow: 0 4px 12px rgba(15, 23, 42, 0.1);
}
"""

with gr.Blocks(theme=THEME, css=CSS, title="LLM Twin") as demo:
    gr.HTML(
        """
        <div id="twin-header">
            <h1>&#129302; Abhishek's LLM Twin</h1>
            <p>Chat with a personalized AI clone that writes in your style and voice.</p>
        </div>
        """
    )

    chat = gr.ChatInterface(
        predict,
        type="messages",
        chatbot=gr.Chatbot(
            elem_id="twin-chatbot",
            type="messages",
            height=520,
            show_copy_button=True,
        ),
        textbox=gr.Textbox(
            placeholder="Ask your LLM Twin to draft something...",
            label="Message",
            container=False,
            scale=7,
        ),
        additional_inputs=[
            gr.Textbox(
                "Abhishek Kanojiya",
                label="Who are you?",
            )
        ],
        examples=[
            [
                "Draft a post about RAG systems.",
                "Abhishek Kanojiya",
            ],
            [
                "Draft an article paragraph about vector databases.",
                "Abhishek Kanojiya",
            ],
            [
                "Draft a post about LLM chatbots.",
                "Abhishek Kanojiya",
            ],
        ],
        cache_examples=False,
    )


if __name__ == "__main__":
    demo.queue().launch(
        server_name="127.0.0.1",
        server_port=7860,
        share=False,
        prevent_thread_lock=False,
    )
