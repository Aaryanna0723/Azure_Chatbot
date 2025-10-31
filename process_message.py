import requests
from global_var import global_state
from read_files import read_word_files
from gemini_call import (
    summarize_relevant_data,
    suggest_solution,
    generate_question,
    evaluate_information,generate_incident_desc
)
import json
from generate_incident import generate_incident_number
from service_now import create_incident,get_oauth_token


def process_user_message(message, history):
    if not message.strip():
        return history, ""

    history.append([message, None])

    MAX_QUESTIONS=3

    if global_state.chat_state == "waiting_for_issue":
        issue = message.strip()
        global_state.issue = issue  # Store the original issue

        #folder_path = "sample documents"
        folder_path = "C:/Users/AA926UC/OneDrive - EY/Documents/Python/Gemini_chatbot/sample documents"
        word_files = read_word_files(folder_path, issue)
 
        global_state.summary_context = summarize_relevant_data(word_files, issue, global_state.chat_history)
        print(global_state.summary_context, type(global_state.summary_context))

        if any("no information" in word.lower() or "null" in word.lower() for word in global_state.summary_context.split()):
            short_desc,long_desc = generate_incident_desc(issue)
            incident_number = create_incident(short_desc,long_desc)
            #description = generate_incident_desc(issue)
            #short_description, detailed_description = description.split('\n', 1) if '\n' in description else (description, "")  
            incident_number = create_incident(short_desc,long_desc)
            bot_response = (
                f"⚠️ No relevant information found in our knowledge base for your issue.\n\n"
                f"📋 I've created a support ticket for you: **Incident Number {incident_number}**\n\n"
                f"Our support team will get back to you soon. Is there anything else I can help you with?"
            )
            global_state.chat_state = "completed"
            history[-1][1] = bot_response
            return history, ""
        else:
            global_state.chat_state = "asking_questions"

    if global_state.chat_state == "asking_questions":
        # Handle answers to previous questions or start new questions
        if global_state.question_list and len(global_state.response_list) < len(global_state.question_list):
            # This is an answer to the previous question
            global_state.response_list.append(message.strip())
            #global_state.chat_history["question"] = global_state.question_list[len(global_state.response_list) - 1]
            #global_state.chat_history["answer"] = message.strip()
            new_entry = {
                          "question": global_state.question_list[len(global_state.response_list) - 1],
                         "answer": message.strip()}

            global_state.chat_history.append(new_entry)
            

        # Always evaluate current information after each interaction
        evaluation = evaluate_information(global_state.issue, global_state.summary_context, global_state.chat_history)
        print("Evaluation:", evaluation)

        if evaluation.get("sufficient_info", False) or len(global_state.question_list) >= MAX_QUESTIONS:
            print(evaluation)
            print(global_state.question_list)
            solution = suggest_solution(global_state.summary_context, global_state.chat_history)
            bot_response = f"✅ **Here's what you should do:**\n{solution}\n\nDo you need help with anything else?"
            global_state.chat_state = "completed"
            history[-1][1] = bot_response
            return history, ""

        else:
            # Generate the next follow-up question
            question = generate_question(global_state.issue, global_state.summary_context, global_state.chat_history)
            global_state.question_list.append(question)
             #f"I found relevant information in our knowledge base for your issue.\n"
              #  f"Let's go through a few quick checks.\n\n"

            bot_response = (
               
                f"**Question {len(global_state.question_list)}:**\n{question}"
            )
            new_entry = {
                          "question": global_state.question_list[-1],
                         "answer": message.strip()}

            global_state.chat_history.append(new_entry)

            #global_state.chat_history["question"] = global_state.question_list[-1]
            #global_state.chat_history["answer"] = message.strip()
            history[-1][1] = bot_response
            return history, ""

    # If state is not recognized, reset and restart
    
    bot_response = (
        "Let's start over. Could you please describe your issue again?"
    )
    reset_global_state()
    history[-1][1] = bot_response
    return history, ""


# --- Helper: Reset Global State ---
def reset_global_state():
    global_state.chat_state = "waiting_for_issue"
    global_state.question_list = []
    global_state.response_list = []
    global_state.current_index = 0
    global_state.summary_context = ""
    global_state.chat_history = []