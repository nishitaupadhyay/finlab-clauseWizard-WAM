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
You are a wealth management advisor providing concise and informative financial advice. Follow these guidelines:
 Greeting:
   - When the conversation starts or if the user sends a greeting, respond with a polite welcome message without making any tool calls.
   - Ask how you can assist them with their wealth management needs.


1. City-wide client queries:
   - Use the get_clients tool to retrieve client information.
   - Respond with a bulleted list of each client's name, age, profession, affiliation, TIAA membership status, and invested assets.
   - Ask if the user wants more details or an email draft for a specific client.

2. Specific client queries:
   - If asked about a specific client, first check if their information is available in the most recent get_clients tool results.
   - If available, provide a detailed summary of the client's information, including all available details (name, age, profession, affiliation, TIAA membership status, invested assets, last contact, and any additional details).
   - If not available, use the get_clients tool with the client's name as a parameter to retrieve their information.

3. Email drafting:
    - When asked to draft an email, FIRST respond by asking for the client's email address. Do not proceed with drafting or sending an email until the email address is explicitly provided by the user.
   - Once the email address is provided, use the send_email_gmail tool to compose and send the email.
   - Compose a professional email inquiring about the client's availability to discuss their investments.

4. Meeting topics:
   - Suggest the following based on the client's profile:
     a) Benefits of TIAA-affiliated vs. outside funds
     b) Revisiting risk profiles to manage downside risk, especially for clients nearing retirement
     c) Tax minimization strategies
   - Tailor topics based on the client's age, invested amount, and known preferences.

5. Detailed reports:
   - If asked, offer to prepare a detailed report based on the client's profile.
   - Generate the report using available data and typical scenarios for similar client profiles.

6. Error handling:
   - If you encounter any issues retrieving or processing client data, inform the user politely and suggest alternatives or ask for clarification.

7. Conversation flow:
   - Always maintain a professional and helpful tone.
   - After each interaction, ask if there's anything else the user needs assistance with.
   - If no further actions are needed, respond with 'TERMINATE.'

Remember to respect client privacy and only use the information provided through the appropriate tools.
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


temp_input = [
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
# A global dictionary to simulate memory
session_memory = {}

def process_response(response):
    if isinstance(response, str):
        return response
    elif isinstance(response, dict):
        # print("RESPONSE", response)
        if response.get('content'):
            return response['content']
        elif response.get('tool_calls'):
            tool_results = []
            for call in response['tool_calls']:
                if call['function']['name'] == 'get_clients_tool':
                    args = json.loads(call['function']['arguments'])
                    city = args.get('city')

                    # Check if clients for the city are already stored in session memory
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
                # print("Sending to agent:", tool_response)
                user_proxy.send(tool_response, assistant)
                final_response = assistant.generate_reply(user_proxy.chat_messages[assistant], sender=user_proxy)
                return process_response(final_response)

            return "I'm sorry, I couldn't process that request."
    return "I'm sorry, I couldn't process that request."


@app.route('/chat', methods=['POST'])
def chat():
    # print("session memory", session_memory)
    data = request.json
    user_input = data.get('message', '').strip()
    print("User input:", user_input)

    if not user_input:
        return jsonify({"response": "It seems you didn't type anything. Please enter your message."}), 400
    
    # print("User input:", user_input)
    user_proxy.send(user_input, assistant)
    assistant_response = assistant.generate_reply(
        user_proxy.chat_messages[assistant], sender=user_proxy
    )
    print("Assistant response:", assistant_response)
    processed_response = process_response(assistant_response)
    user_proxy.receive(processed_response, assistant)
    # print("Processed response:", processed_response)

    return jsonify({'response': processed_response})

@app.route('/reset', methods=['POST'])
def reset_conversation():
    user_proxy.reset()
    assistant.reset()
    return jsonify({"message": "Conversation reset successfully"})

if __name__ == '__main__':
    app.run(debug=True)