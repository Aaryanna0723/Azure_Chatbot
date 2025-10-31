import os
import pandas as pd
from docx import Document
import random
import string
import google.generativeai as genai
import gradio as gr
import spacy
from spacy.matcher import PhraseMatcher
from spacy.lang.en.stop_words import STOP_WORDS
from read_files import read_word_files
from gemini_call import summarize_relevant_data
from global_var import global_state
from process_message import process_user_message
from generate_incident import generate_incident_number



def initialize_chat():
    return [["", "👋 **Hello! I'm Nova - your Virtual Assistant.**\n\nI'm here to help you troubleshoot issues by analyzing our knowledge base and asking you targeted questions.\n\n**Please describe the issue you're experiencing:**"]]
    
def greet_on_reload():
    global_state.question_list = []
    global_state.current_index=0
    global_state.response_list = []
    global_state.summary_context = ""
    global_state.chat_state = "waiting_for_issue"
    global_state.chat_history=[]
    greeting = "👋 **Hello! I'm Nova - your Virtual Assistant.**\n\nI'm here to help you troubleshoot issues by analyzing our knowledge base and asking you targeted questions.\n\n**Please describe the issue you're experiencing:**"
    return [(None, greeting)], [("User", greeting)]

def respond(message, history):
    return process_user_message(message, history)


# Gradio UI

with gr.Blocks(title="NOVA", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🔷 NOVA")
    gr.Markdown("*Next-gen Operations Virtual Assistant*")

    chatbot = gr.Chatbot(
             value=initialize_chat(),
             height=500,
             show_label=False,
             container=True,
             bubble_full_width=False
    )
    state = gr.State([])
    with gr.Row():
        msg = gr.Textbox(
            placeholder="Type your message here...",
            show_label=False,
            scale=4,
            container=False
        )
        send_btn = gr.Button("Send", variant="primary", scale=1)
    
    # Handle send button click
    send_btn.click(
        respond,
        inputs=[msg, chatbot],
        outputs=[chatbot, msg]
    )
    
    # Handle Enter key press
    msg.submit(
        respond,
        inputs=[msg, chatbot],
        outputs=[chatbot, msg]
    )

    demo.load(fn=greet_on_reload, inputs=None, outputs=[chatbot, state])

if __name__ == "__main__":
    #demo.launch(server_name="0.0.0.0",server_port=int(os.environ.get("PORT", 8000)))
    demo.launch(server_port=int(os.environ.get("PORT", 8000)), share=True)