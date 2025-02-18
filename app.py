import json
import google.generativeai as genai
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging

# Load your personal data
with open("mumbere_darius_profile.json", "r") as file:
    personal_data = json.load(file)

# Directly set your API key here
api_key = "AIzaSyAN23PVrXsIBkYO43JVrXa69hdbRvBqkoY"  # Replace with your actual key

# Configure Gemini API
genai.configure(api_key=api_key)

# Initialize conversation history
conversation_history = []

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Function to generate AI responses with context
def ask_gemini(question, history):
    model = genai.GenerativeModel("gemini-pro")  # Use free-tier model if available

    # Build the prompt including conversation history and personal data
    prompt = (
        "You are a helpful assistant. You have access to the following personal data:\n"
        f"{personal_data_to_string(personal_data)}\n\n"
        "If the user's question is related to the above data, use it to answer. "
        "If the question is unrelated, use your general knowledge to answer.\n\n"
        "Format your responses clearly. Use bullet points or numbered lists only when listing multiple items or steps. "
        "For conversational or paragraph-style responses, avoid unnecessary bullet points.\n\n"
    )

    # Add conversation history for context
    if history:
        prompt += "Conversation History:\n"
        for turn in history:
            prompt += f"User: {turn['user']}\nAI: {turn['ai']}\n"
    
    prompt += f"Question: {question}\nAnswer:"

    try:
        response = model.generate_content(prompt)
        if response:
            # Format the response for better readability
            formatted_response = format_response(response.text)
            return formatted_response
        else:
            return "I don't know the answer."
    except Exception as e:
        logging.error(f"Error generating response: {e}")
        return "Sorry, I encountered an error while processing your question."

def personal_data_to_string(data):
    # Convert personal data to a string, handling nested structures
    def flatten(d, parent_key="", sep="_"):
        items = []
        for k, v in d.items():
            new_key = parent_key + sep + k if parent_key else k
            if isinstance(v, dict):
                items.extend(flatten(v, new_key, sep=sep).items())
            elif isinstance(v, list):
                for i, item in enumerate(v):
                    items.extend(flatten({str(i): item}, new_key, sep=sep).items())  # Handle lists by index
            else:
                items.append((new_key, v))
        return dict(items)
    
    flat_data = flatten(data)
    return "\n".join([f"{k}: {v}" for k, v in flat_data.items()])

def format_response(response):
    # Split the response into lines
    lines = response.split("\n")
    
    formatted_response = ""
    for line in lines:
        line = line.strip()
        if line.startswith(("* ", "- ", "1. ", "2. ", "3. ", "4. ", "5. ", "6. ", "7. ", "8. ", "9. ")):
            # This is a bullet point or numbered list, keep it as is
            formatted_response += f"{line}\n"
        elif line.endswith(":"):
            # This is a heading, make it bold
            formatted_response += f"**{line}**\n\n"
        elif line:
            # This is a regular line of text, add it as a paragraph
            formatted_response += f"{line}\n\n"
    
    return formatted_response.strip()

# Flask API
app = Flask(__name__)
CORS(app)  # Allow cross-origin requests

@app.route("/ask", methods=["POST"])
def ask_question():
    user_question = request.json.get("question")
    if not user_question:
        return jsonify({"error": "No question provided"}), 400

    answer = ask_gemini(user_question, conversation_history)

    # Update conversation history
    conversation_history.append({"user": user_question, "ai": answer})
    # Limit history length to avoid excessive context
    if len(conversation_history) > 5:  # Keep the last 5 exchanges
        conversation_history.pop(0)

    return jsonify({"answer": answer})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)