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

# Agent 1: Client Management Agent
client_management_agent = AssistantAgent(
    name="client_management_agent",
    llm_config=llm_config,
    system_message="""
    You are responsible for managing client information. 
    Your tasks include retrieving and providing details about clients based on their location or specific name.
    Do that using the get_clients tool.
    Only share the name and age when asked about clinets in a city but include everything when asked about a specific client.
    """,
)

# Agent 2: Email Drafting Agent
email_drafting_agent = AssistantAgent(
    name="email_drafting_agent",
    llm_config=llm_config,
    system_message="""
    You are responsible for drafting, editing, and sending emails to clients based on their financial information and queries. 

    IMPORTANT!! ALWAYS FOLLOW THESE STEPS:

    1. Draft an email tailored to the client's specific needs, including topics such as:
       - TIAA vs. outside funds
       - Risk profiles
       - Tax strategies

    2. Present the draft to the user with the prefix "Here's a draft of the email:"

    3. Ask the user if they would like to make any edits to the draft.

    4. If the user provides edits, incorporate them into the email.

    5. Present the final version of the email and ask for explicit confirmation to send it.

    6. ONLY proceed with sending the email using the  send_email_gmail function after receiving explicit confirmation from the user.


    """,
)

# Agent 3: Investment Advice Agent
investment_advice_agent = AssistantAgent(
    name="investment_advice_agent",
    llm_config=llm_config,
    system_message="""
    You are responsible for providing investment advice to clients based on their financial details. 
    Get the client details from get_clients tool, and the suggest the below 
    Your primary goal is to convince clients to invest their remaining available assets into TIAA.
    Key points to emphasize:
    1. To achieve desired rates of return, clients can't rely solely on bonds.
    2. TIAA engages in extensive diversification efforts through its investments.
    3. TIAA funds can meet required portfolio risk diversification goals.
    4. Be prepared to address common client objections and concerns.
    Remember to be persuasive but also respectful of the client's concerns and financial goals.
    """,
)

# User Proxy Agent
user_proxy = UserProxyAgent(
    name="user_proxy",
    human_input_mode="NEVER",
     code_execution_config={
        "work_dir": "market",
        "use_docker": False,
    },
    max_consecutive_auto_reply=0,
    is_termination_msg=lambda x: x.get("content", "") and x.get("content", "").rstrip().endswith("TERMINATE"),
)

# Registering functions with specific agents
register_function(
    get_clients,
    caller=client_management_agent,
    executor=user_proxy,
    name="get_clients_tool",  
    description="This tool is used to look up clients based on the provided city or client name.",
)

register_function(
    send_email_gmail,
    caller=email_drafting_agent,
    executor=user_proxy,
    name="send_email_gmail",
    description="This tool is used to send an email using Gmail SMTP, with the option to mask the sender as a company email.",
)

# A global dictionary to simulate memory
session_memory = {}
email_state = {}
def process_response(agent, response, user_input):
    global email_state
    
    if isinstance(response, str):
        return response
    elif isinstance(response, dict):
        if response.get('content'):
            return response['content']
        elif response.get('tool_calls'):
            for call in response['tool_calls']:
                if call['function']['name'] == 'get_clients_tool':
                    args = json.loads(call['function']['arguments'])
                    city = args.get('city')
                    if city in session_memory:
                        clients = session_memory[city]
                    else:
                        clients = get_clients(city=city)
                        session_memory[city] = clients
                    return json.dumps(clients, indent=2)

                elif call['function']['name'] == 'send_email_gmail':
                    args = json.loads(call['function']['arguments'])
                    if not email_state.get('draft'):
                        email_state = {
                            'draft': True,
                            'recipient_email': args.get('recipient_email'),
                            'subject': args.get('subject'),
                            'body': args.get('body')
                        }
                        return f"Here's a draft of the email:\n\nTo: {email_state['recipient_email']}\nSubject: {email_state['subject']}\n\n{email_state['body']}\n\nWould you like to send this email? (Yes/No)"
    
    # Handle user confirmation outside of the response processing
    if email_state.get('draft'):
        if user_input.lower() == 'yes':
            try:
                result = send_email_gmail(email_state['recipient_email'], email_state['subject'], email_state['body'])
                email_state = {}  # Reset the email state
                return f"Email sent successfully. {result}"
            except Exception as e:
                email_state = {}  # Reset the email state
                return f"An error occurred while sending the email: {str(e)}"
        elif user_input.lower() == 'no':
            return "Okay, what would you like to change in the email?"
        else:
            return "Please respond with 'Yes' to send the email or 'No' to edit it."

    return "I'm sorry, I couldn't process that request."

# def process_response(agent, response, user_input):
#     global email_state
    
#     if isinstance(response, str):
#         return response
#     elif isinstance(response, dict):
#         if response.get('content'):
#             return response['content']
#         elif response.get('tool_calls'):
#             for call in response['tool_calls']:
#                 if call['function']['name'] == 'get_clients_tool':
#                     args = json.loads(call['function']['arguments'])
#                     city = args.get('city')
#                     if city in session_memory:
#                         clients = session_memory[city]
#                     else:
#                         clients = get_clients(city=city)
#                         session_memory[city] = clients
#                     return json.dumps(clients, indent=2)

#                 elif call['function']['name'] == 'send_email_gmail':
#                     args = json.loads(call['function']['arguments'])
#                     if not email_state.get('draft'):
#                         email_state = {
#                             'draft': True,
#                             'recipient_email': args.get('recipient_email'),
#                             'subject': args.get('subject'),
#                             'body': args.get('body')
#                         }
#                         return f"Here's a draft of the email:\n\nTo: {email_state['recipient_email']}\nSubject: {email_state['subject']}\n\n{email_state['body']}\n\nWould you like to send this email? (Yes/No)"
    
#     # Handle user confirmation outside of the response processing
#     if email_state.get('draft') and user_input.lower() == 'yes':
#         try:
#             result = send_email_gmail(email_state['recipient_email'], email_state['subject'], email_state['body'])
#             email_state = {}  # Reset the email state
#             return f"Email sent successfully. {result}"
#         except Exception as e:
#             email_state = {}  # Reset the email state
#             return f"An error occurred while sending the email: {str(e)}"
#     elif email_state.get('draft'):
#         email_state = {}  # Reset the email state
#         return "Email sending cancelled. What else can I help you with?"

#     return "I'm sorry, I couldn't process that request."

# Update the chat route
# @app.route('/chat', methods=['POST'])
# def chat():
    # global email_state
    # data = request.json
    # user_input = data.get('message', '').strip()
    # print("User input:", user_input)

    # if not user_input:
    #     return jsonify({"response": "It seems you didn't type anything. Please enter your message."}), 400

    # if email_state.get('draft'):
    #     # If we have a draft, we don't need to call the AI model again
    #     processed_response = process_response(None, None, user_input)
    # else:
    #     if "client" in user_input.lower():
    #         agent = client_management_agent
    #     elif "email" in user_input.lower():
    #         agent = email_drafting_agent
    #     elif "investment" in user_input.lower():
    #         agent = investment_advice_agent
    #     else:
    #         return jsonify({"response": "Please specify whether you're asking about a client, email, or investment."}), 400

    #     user_proxy.send(user_input, agent)
    #     agent_response = agent.generate_reply(
    #         user_proxy.chat_messages[agent], sender=user_proxy
    #     )
    #     print(f"{agent.name} response:", agent_response)
    #     processed_response = process_response(agent, agent_response, user_input)

    # user_proxy.receive(processed_response, agent)
    # return jsonify({'response': processed_response})

@app.route('/chat', methods=['POST'])
def chat():
    global email_state
    data = request.json
    user_input = data.get('message', '').strip()
    print("User input:", user_input)

    if not user_input:
        return jsonify({"response": "It seems you didn't type anything. Please enter your message."}), 400

    if email_state.get('draft'):
        # If we have a draft, we don't need to call the AI model again
        processed_response = process_response(None, None, user_input)
        # Clear the email state if the user doesn't want to send the email
        if user_input.lower() != 'yes':
            email_state = {}
        return jsonify({'response': processed_response})
    else:
        if "client" in user_input.lower() or "Boston" in user_input.lower():
            agent = client_management_agent
        elif "email" in user_input.lower():
            agent = email_drafting_agent
        elif "discussion" in user_input.lower() or "investment" in user_input.lower():
            agent = investment_advice_agent
        else:
            return jsonify({"response": "Please specify whether you're asking about a client, email, or investment."}), 400

        user_proxy.send(user_input, agent)
        agent_response = agent.generate_reply(
            user_proxy.chat_messages[agent], sender=user_proxy
        )
        print(f"{agent.name} response:", agent_response)
        processed_response = process_response(agent, agent_response, user_input)
        user_proxy.receive(processed_response, agent)
        return jsonify({'response': processed_response})

@app.route('/reset', methods=['GET'])
def reset_conversation():
    user_proxy.reset()
    client_management_agent.reset()
    email_drafting_agent.reset()
    investment_advice_agent.reset()
    return jsonify({"message": "Conversation reset successfully"})

if __name__ == '__main__':
    app.run(debug=True)
