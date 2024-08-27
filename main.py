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
    "model": "gpt-4",
    "api_key": os.environ["OPENAI_API_KEY"],
    "base_url": os.environ["OPENAI_BASE_URL"],
    "temperature": 0,
    "timeout": 120,
}

# Create the assistant agent
assistant = AssistantAgent(
    name="wealth_management_advisor",
    llm_config=llm_config,
    system_message="""
     You are a wealth management advisor who provides financial advice. Your responses should be concise and informative.
        You are capable of understanding and responding to a wide range of financial queries.
        When asked who to contact in a given city, use the get_clients tool in order to find clients.
        Once you have the clients, respond by showing the clients in a bulleted list telling the 
        user only their name, age, profession, affiliation, whether or not they are an active TIAA member, 
        and how much they have invested and you should then ask the user if they want to learn more about each client or 
        if they want you to draft an email to them.

        When asked about a specific client, use the get_clients_tool client's details.
        Once you have the client details, respond by showing the information in a clear, organized manner.

        If asked to draft an email, use the send_email_gmail tool to send a professional email to the clients.
        Note that you'll need to ask the user for the client's email address as it's not provided in the client data.
        The email should ask them what times they are available to discuss their financial investments. 
        
        If asked to tell the user more about a specific client, you should use the details section in the response you received earlier from the get_clients tool.
        If asked to suggest topics for a meeting, then tell the user that they should consider 
        1) Exploring the benefits of TIAA-affiliated funds over outside funds 
        2) Revisiting their high risk profile to manage downside risk as they approach decumulation 
        3) Tax minimization. You should tailor those topics to each client by paying attention to their age and the amount they have invested as well as their preferred strategies mentioned in their client details.
        Once you have suggested topics for a meeting, ask the user if they would like you to prepare materials for that meeting.
        If they say yes, generate a more detailed report on the topics suggested by assuming information that would be typical for that client given their profile.
        If they say there is nothing else to discuss or do then reply with 'TERMINATE'
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

# def process_response(response):
#     if isinstance(response, str):
#         return response
#     elif isinstance(response, dict):
#         if response.get('content'):
#             return response['content']
#         elif response.get('tool_calls'):
#             print("this is the response", response)
#             tool_results = []
#             for call in response['tool_calls']:
#                 if call['function']['name'] == 'get_clients_tool':
#                     args = json.loads(call['function']['arguments'])
#                     print("THIS IS ARGS", args)
#                     city = args.get('city')
#                     client_name = args.get('client_name')
#                     clients = get_clients(city=city, client_name=client_name)
#                     print("CLIENTS ARE THESE", clients)
#                     tool_results.append(clients)
#                     print("this is the tool results ", tool_results)
#                 elif call['function']['name'] == 'send_email_gmail':
#                     args = json.loads(call['function']['arguments'])
#                     recipient_email = args.get('recipient_email')
#                     subject = args.get('subject')
#                     body = args.get('body')
#                     result = send_email_gmail(recipient_email, subject, body)
#                     tool_results.append(result)
            
#             if tool_results:
#                 tool_response = json.dumps(tool_results, indent=2)
#                 print("this is tools response", tool_response)
#                 user_proxy.send(tool_response, assistant)
#                 #sending the tools response to the assistant so that they can generate correct info 
#                 final_response = assistant.generate_reply(user_proxy.chat_messages[assistant], sender=user_proxy)
#                 print("this is the final response", final_response)
#                 return process_response(final_response)
            
#             return "I'm sorry, I couldn't process that request."
#     return "I'm sorry, I couldn't process that request."

def process_response(response):
    if isinstance(response, str):
        return response
    elif isinstance(response, dict):
        print("RESPONSE", response)
        if response.get('content'):
            return response['content']
        elif response.get('tool_calls'):
            tool_results = []
            for call in response['tool_calls']:
                if call['function']['name'] == 'get_clients_tool':
                    args = json.loads(call['function']['arguments'])
                    city = args.get('city')
                    clients = get_clients(city=city)
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

    if not user_input:
        return jsonify({"response": "It seems you didn't type anything. Please enter your message."}), 400

    user_proxy.send(user_input, assistant)
    assistant_response = assistant.generate_reply(
        user_proxy.chat_messages[assistant], sender=user_proxy
    )

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
