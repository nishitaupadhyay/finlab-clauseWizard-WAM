from flask import Flask, request, jsonify
from flask_cors import CORS
from autogen import AssistantAgent, UserProxyAgent, ConversableAgent
from dotenv import load_dotenv, find_dotenv
from tools import get_clients  # Import the data access function
from autogen import register_function
from email_sender import send_email_gmail  # Import the email function
import os
import json

load_dotenv(find_dotenv())

app = Flask(__name__)
CORS(app, supports_credentials=True)

llm_config = {
    "model": "gpt-3.5-turbo",
    "api_key": os.environ["OPENAI_API_KEY"],
    "base_url": os.environ["OPENAI_BASE_URL"],
    "temperature": 0,
    "timeout": 120,
}

simple_input = [
  {
    "name": "Lawrence Summers",
    "age": 55,
    "profession": "Professor",
    "affiliation": "Harvard University",
    "active_tiaa_member": True,
    "invested_assets": 180000,
    "last_contacted_days": 15,
    "details": "Lawrence appears to be 10 years from retirement and is estimated to have $40k in investable assets that are not invested in TIAA. Lawrence has been with TIAA for over three years an favors an aggressive risk profile and passive management. Of the assets with TIAA, they appear to draw from a broad array of fund managers, including both TIAA-affiliated and outside funds."
  }
]


# Create the assistant agent
assistant = AssistantAgent(
    name="wealth_management_advisor",
    llm_config=llm_config,
    system_message="""
    You are a wealth management advisor who provides financial advice. Your responses should be concise and informative.
    You are capable of understanding and responding to a wide range of financial queries when asked about a specific client.
    Follow these guidelines:

    1. Client Queries:
        - City-wide: Use get_clients tool. List client name, age, profession, affiliation, TIAA status, invested assets. Offer more details/email draft.
        - Specific: Check recent tool results first. If unavailable, use get_clients tool with name. Provide full client details.

     2. Email Process:
        -When asked to draft an email: use get_clients tool to get client email.
        - Include tailored topics: TIAA vs. outside funds, risk profiles, tax strategies in the drafted email 
        - Present draft to the user with "Here's a draft of the email:" prefix.
        - Ask user for edits, incorporate if provided.
        - Get explicit confirmation before sending.
        - Use send_email_gmail tool only after receiving explicit confirmation.
        - Inform user of successful sending.

    3. General:
        - Handle errors politely, suggest alternatives.
        - Maintain professional tone.
        - Ask if user needs more assistance after each interaction.
        - When discussing investments with clients:
          * Emphasize that to achieve desired rates of return, investing solely in bonds may not be sufficient.
          * If clients express concerns about diversification, highlight that TIAA engages in extensive diversification efforts through its investments, ensuring that TIAA funds can meet portfolio risk diversification goals.
          * Encourage clients to consider investing their remaining available assets into TIAA, emphasizing the benefits of consolidation and TIAA's diversification strategies.

    Respect client privacy. Use only provided tool information.
"""

)

# Create the user proxy agent
user_proxy = UserProxyAgent(
    name="user_proxy",
    human_input_mode="NEVER",
    max_consecutive_auto_reply=0,
    is_termination_msg=lambda x: x.get("content", "") and x.get("content", "").rstrip().endswith("TERMINATE"),
    code_execution_config={
        "work_dir": "market",
        "use_docker": False,
    },
)

register_function(
    get_clients,
    caller=assistant,
    executor=user_proxy,
    name="get_clients_tool",  
    description="This tool is used to look up the clients that the user should reach out to if they are visiting the provided city.",
)


register_function(
    send_email_gmail,
    caller=assistant,
    executor=user_proxy,
    name="send_email_gmail",
    description="This tool is used to send an email using Gmail SMTP, with the option to mask the sender as a company email.",
)


# A global dictionary to simulate memory
session_memory = {}



def process_response(response):
    if isinstance(response, str):
        return response
    elif isinstance(response, dict):
        if response.get('content'):
            return response['content']
        elif response.get('tool_calls'):
            tool_results = []
            for call in response['tool_calls']:
                if call['function']['name'] == 'get_clients_tool':
                    args = json.loads(call['function']['arguments'])
                    city = args.get('city')
                    if city in session_memory:
                        clients = session_memory[city]
                    else:
                        clients = get_clients(city=city)
                        session_memory[city] = clients  # Store in memory

                    tool_results.append(clients)

                elif call['function']['name'] == 'send_email_gmail':
                    args = json.loads(call['function']['arguments'])
                    recipient_email = args.get('recipient_email')
                    subject = args.get('subject')
                    body = args.get('body')

                    result = send_email_gmail(recipient_email, subject, body)
                    tool_results.append(result)
            if tool_results:
                tool_response = json.dumps(tool_results, indent=2)
                user_proxy.send(tool_response, assistant)
                final_response = assistant.generate_reply(user_proxy.chat_messages[assistant], sender=user_proxy)
                return process_response(final_response)
                

            return "I'm sorry, I couldn't process that request."
    return "I'm sorry, I couldn't process that request."


@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_input = data.get('message', '').strip()
    print("User input:", user_input)

    if not user_input:
        return jsonify({"response": "It seems you didn't type anything. Please enter your message."}), 400
    
    user_proxy.send(user_input, assistant)
    assistant_response = assistant.generate_reply(
        user_proxy.chat_messages[assistant], sender=user_proxy
    )
    print("Assistant response:", assistant_response)
    processed_response = process_response(assistant_response)
    user_proxy.receive(processed_response, assistant)

    return jsonify({'response': processed_response})

@app.route('/reset', methods=['POST'])
def reset_conversation():
    user_proxy.reset()
    assistant.reset()
    return jsonify({"message": "Conversation reset successfully"})

if __name__ == '__main__':
    app.run(debug=True)