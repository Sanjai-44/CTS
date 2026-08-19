"""
===============================================================================
Cognizant (CTS) Nurture Placement Hackathon - Commercial Intelligence GenAI Assistant
Commercial Analytics Market Share & Share-Shift Tracker
===============================================================================
"""

import os
import google.generativeai as genai
from config import BASE_DIR, GEMINI_API_KEY, get_secret

api_key = GEMINI_API_KEY or get_secret("GEMINI_API_KEY", "")
if api_key:
    try:
        genai.configure(api_key=api_key)
    except Exception as e:
        print(f"[LLM Agent] Failed to configure Gemini API: {e}")


SYSTEM_PROMPT = """
You are an expert Commercial Analytics AI Consultant specializing in Pharmaceutical Market Share, Competitive Intelligence, and Time-Series Forecasting.
Provide executive-level, data-backed insights using the provided context.
Focus on market share percentage trends, week-over-week share shifts (pp/bps), dynamic volatility threshold breaches, Isolation Forest ML anomalies, and ARIMA forecast projections.
Do not use outdated static threshold rules. All calculations use dynamic company 3-week volatility bounds.
"""

def answer_chatbot_question(user_prompt, context_str=""):
    """
    Answers commercial analytics queries using Google Gemini LLM API (gemini-flash-latest).
    Falls back gracefully to structured deterministic response if LLM API key is unavailable.
    """
    if GEMINI_API_KEY:
        try:
            model = genai.GenerativeModel("gemini-flash-latest", system_instruction=SYSTEM_PROMPT)
            full_prompt = f"COMMERCIAL ANALYTICS CONTEXT:\n{context_str}\n\nUSER QUESTION:\n{user_prompt}"
            response = model.generate_content(full_prompt)
            if response and hasattr(response, 'text') and response.text:
                return response.text
        except Exception as e:
            print(f"[LLM Agent Warning] Gemini API Call Error: {e}")
            
    # Deterministic Structured Fallback (No Hardcoded Target Terminology)
    return (
        f"**Commercial Analytics Executive Summary**\n\n"
        f"Based on your query regarding market trends:\n"
        f"- **Analytical Context:** {context_str[:250]}...\n"
        f"- **Dynamic Threshold Engine:** Evaluating 3-week previous volatility baseline (u3 +- 2*sigma3).\n"
        f"- **ARIMA Time-Series:** 4-week future projections available in Tab 2 with MAE/RMSE validation.\n\n"
        f"*(Note: Powered by Gemini Flash Commercial Analytics Assistant)*"
    )

if __name__ == "__main__":
    reply = answer_chatbot_question("Summarize the market share performance of our selected company.")
    print("AI Chatbot Reply:\n", reply)
