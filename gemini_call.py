import os
#import google.generativeai as genai
import json
import re
from difflib import SequenceMatcher
import time
# Utility function to run prompts
import requests
#start = time.time()
from dotenv import load_dotenv

load_dotenv()
# ServiceNow instance details

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")  # Or hardcode for testing


def run_gemini_prompt(prompt):
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent"
    headers = {
        "Content-Type": "application/json"
    }
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    params = {
        "key": GEMINI_API_KEY
    }

    response = requests.post(url, headers=headers, params=params, json=payload,verify=False)
    if response.status_code == 200:
        try:
            return response.json()['candidates'][0]['content']['parts'][0]['text'].strip()
        except Exception as e:
            return f"Error parsing response: {str(e)}"
    else:
        return f"Error: {response.status_code} - {response.text}"



# Function 1: Summarize relevant data
def summarize_relevant_data(word_text, issue, history):
    start = time.time()
    prompt = f"""
    You are a BlueYonder WMS assistant. Analyze the provided Word file contents and summarize only parts that are relevant to the 
    user's reported issue: "{issue}" and chat history: "{history}".

    Focus on:
    - Root causes, troubleshooting steps, or error-handling instructions related to the issue.
    - Ignore unrelated data or generic process descriptions.

    Word Data:
    {word_text}

    Provide a clear, concise summary in plain text (8–10 sentences maximum).
    If no relevant data is found, return only the word NULL.
    """
    summary_text = run_gemini_prompt(prompt)
    print("Time taken for summarization:", time.time() - start)
    return summary_text
    

# Function 2: Suggest solution
def suggest_solution(summary, responses):
    start = time.time()
    prompt = f"""
    You are a BlueYonder WMS assistant. Based on the provided context and user's responses, create a concise, actionable step-by-step resolution.
    
    Context from SOPs: {summary}

    User's Responses: {responses}

    Provide:
    1. A 1-2 line diagnosis of the issue.
    2. 3-5 clear, numbered resolution steps (each step <= 2 lines).
    3. Optional: 1-2 preventive recommendations if applicable.

    Format:
    **Diagnosis:** <short sentence>
    **Resolution Steps:**
    1. ...
    2. ...
    3. ...
    **Prevention (if any):**
    - ...
    """

    return run_gemini_prompt(prompt)


# Function 3: Generate follow-up question
def generate_question(issue, summary, history):
    prompt = f"""
    You are a BlueYonder WMS troubleshooting assistant.

    Your goal is to help resolve the issue: **{issue}**

    You have access to the following:
    - Summary of relevant information from the knowledge base: **{summary}**
    - Previous chat history with the user: **{history}**

    Based on this context, generate the most appropriate and specific follow-up question that will help gather missing information needed to resolve the issue.
    Please consider all previously asked questions and avoid repetition and paraphrasing.

    Only return the question as plain text. Do not include any explanations or formatting.
    """
    return run_gemini_prompt(prompt)

# Function 4: Evaluate information sufficiency
def evaluate_information(issue, summary_context, chat_history):
    start = time.time()
    if not summary_context or "no information" in " ".join(summary_context).lower():
        return {
            "sufficient_info": False,
            "confidence": 0.0,
            "missing_details": ["relevant documentation not found"]
        }

    num_answers = len(chat_history)
    info_score = 0.0

    if any(issue.lower() in item.lower() for item in summary_context):
        info_score += 0.3

    if num_answers >= 3:
        info_score += 0.4
    elif num_answers >= 1:
        info_score += 0.2

    info_score = min(info_score, 1.0)
    sufficient_info = info_score >= 0.6

    if info_score <= 0.4 or info_score >= 0.8:
        missing = []
        if not sufficient_info:
            if num_answers < 2:
                missing.append("more details about the problem")
        return {
            "sufficient_info": sufficient_info,
            "confidence": round(info_score, 2),
            "missing_details": missing
        }

    # Borderline case: Ask GPT4All for deeper reasoning
    prompt = f"""
    You are a technical support assistant.
    Decide if the available context is enough to confidently provide a solution.

    Issue: {issue}

    Documentation Summary:
    {summary_context}

    Conversation so far:
    {json.dumps(chat_history, indent=2)}

    Respond ONLY in JSON:
    {{
      "sufficient_info": true or false,
      "confidence": float between 0 and 1,
      "reason": "brief explanation",
      "missing_details": ["list of missing elements if any"]
    }}
    """
    try:
        result = run_gemini_prompt(prompt)
        evaluation = json.loads(result)
        print("Time taken for evaluation:", time.time() - start)
        return evaluation
    except Exception as e:
        return {
            "sufficient_info": sufficient_info,
            "confidence": round(info_score, 2),
            "missing_details": ["GPT4All evaluation failed, using rule-based estimate"]
        }
    

'''
def generate_incident_desc(issue):
    
    prompt = f"""You are an assistant helping generate ServiceNow ticket descriptions.

    Given the issue: "{issue}", generate a one-line sentence that clearly describes the problem for a support ticket."""
    
    response = run_gemini_prompt(prompt)
    print('response of generate_incident_desc:', response)
    return response
'''

def generate_incident_desc(issue):
    prompt = f"""
    You are helping generate ServiceNow ticket descriptions based on the issue: {issue}.
    Please return the output strictly in JSON format with the following keys:
    {{
      "ShortDescription": "A concise summary of the issue (max 100 characters)",
      "DetailedDescription": "A detailed explanation of the issue"
    }}
    Example of the output:
    {{
      "ShortDescription": "Email service outage for multiple users",
      "DetailedDescription": "Several users are unable to access email services. The issue started this morning and affects both sending and receiving emails. Immediate investigation is required to restore functionality."
    }}
    Do not include any extra text, comments, or explanations outside the JSON.
    """
    response = run_gemini_prompt(prompt).strip()
    if response.startswith("```"):
    # Split by newline and remove first and last lines
        lines = response.splitlines()
    # Remove lines that start with ``` (like ```json or ```)
        lines = [line for line in lines if not line.strip().startswith("```")]
        response = "\n".join(lines).strip()
        ticket_data = json.loads(response)
        try:
            ticket_data = json.loads(response)
            print("Parsed JSON:", ticket_data)
        
            short_desc = ticket_data.get("ShortDescription", "")
            long_desc = ticket_data.get("DetailedDescription", "")
            print("ShortDescription:", short_desc)
            print("DetailedDescription:", long_desc)
            return short_desc, long_desc
        
        except json.JSONDecodeError:
            print("Invalid JSON returned:", response)
            return "", ""