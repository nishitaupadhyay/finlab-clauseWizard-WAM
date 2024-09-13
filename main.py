import os
from flask import Flask, request, jsonify, send_from_directory
from autogen import ConversableAgent, AssistantAgent, UserProxyAgent
from dotenv import load_dotenv, find_dotenv
from autogen import register_function
from tools import get_clients
from email_sender import send_email_gmail
from autogen import GroupChat, GroupChatManager
from flask_cors import CORS

app = Flask(__name__, static_folder='static', template_folder='static')
CORS(app, supports_credentials=True)

# Load environment variables
load_dotenv(find_dotenv())

# LLM configuration
llm_config = {
    "model": "gpt-3.5-turbo",
    "api_key": os.environ["OPENAI_API_KEY"],
    "base_url": os.environ["OPENAI_BASE_URL"],
    "temperature": 0,
    "timeout": 120,
    "cache_seed": None
}

# Message history tracking
message_history = {
    "wealth_management_advisor": [],
    "user_proxy_agent": [],
    "email_agent": []
}


# Function to check for termination message
def should_terminate_user(message):
    print("Message received:", message)
    # return "tool_calls" not in message and message["role"] != "tool"
    return 'TERMINATE' in message['content'] 

def save_history(history):
    global message_history
    message_history = history

def get_history():
    global message_history
    return message_history

@app.route('/chat', methods=['POST'])
def chat():
    print("Request Object:", request)
    message = request.json["message"]

    wealth_management_advisor = AssistantAgent(
    name="wealth_management_advisor",
    llm_config=llm_config,
    system_message="""
        You are a wealth management advisor who provides financial advice. 
        1. When asked to find clients in a specific city, use the `get_clients` tool to retrieve the clients in that city.
        2. If the user asks for more information about a specific client (for example, "Tell me more about Lawrence"), do not search for new clients. Instead, look through the clients you have already retrieved and provide more detailed information from the 'details' section about the specific client.
        3. Only call the `get_clients` tool if the user is asking for clients in a new city or if the city hasn't been mentioned yet.
        4. If the user asks you about drafting or sending emails, don't respond to the user and instead ask the 'email_agent' to handle that.
        Each time you respond to the user end your message with the word 'TERMINATE', unless you are going to invoke the 'email_agent'.
    """,
    human_input_mode="NEVER",
    is_termination_msg=should_terminate_user,
)

    print("Registering get_clients tool")
    wealth_management_advisor.register_for_llm(name="get_clients", description="This tool is used to look up for clients and their information using the get_clients tool.")(get_clients)

    email_agent = AssistantAgent(
        name="email_agent",
        llm_config=llm_config,
        system_message="""
            You are responsible for drafting, editing, and sending emails to clients.
            First, draft the email and present it to the user without sending. 
            Ask if they want to make changes or are ready to send. 
            Update the draft as needed until approval. 
            Once approved, get explicit confirmation before using the send_email_gmail function to send the email. 
            Afterward, confirm the email has been sent successfully by sending appropriate success message. 
            Always wait for user input before proceeding.
            Each time you respond to the chat_manager end your message with the word 'TERMINATE'
        """,
        is_termination_msg=should_terminate_user,
    )


    # Register the email workflow and sending function
    email_agent.register_for_llm(name="send_email_gmail", description="Sends the email using send_email_gmail tool. Only use this after explicit user confirmation.")(send_email_gmail)

    # Create user proxy agent
    user_proxy_agent = UserProxyAgent(
        name="user",
        llm_config=llm_config,
        description="""
            A human user capable of interacting with AI agents.,
        """,
        system_message=""""
            Always appends the word 'TERMINATE' at the end of each message.
        """,
        human_input_mode="NEVER",
        code_execution_config={
            "last_n_messages": 10,
            "work_dir": "market",
            "use_docker": False,
        },
        is_termination_msg=should_terminate_user,
    )

    # Register functions with the user proxy agent
 
    user_proxy_agent.register_for_execution(name="get_clients")(get_clients)
    user_proxy_agent.register_for_execution(name="send_email_gmail")(send_email_gmail)

    # Create group chat
    group_chat = GroupChat(agents=[user_proxy_agent, email_agent, wealth_management_advisor], messages=[], max_round=120)

    group_manager = GroupChatManager(
        groupchat=group_chat,
        llm_config=llm_config,
        human_input_mode="NEVER"
    )

    # Set histories
    history = get_history()
    wealth_management_advisor._oai_messages = {group_manager: history['wealth_management_advisor']}
    user_proxy_agent._oai_messages = {group_manager: history['user_proxy_agent']}
    email_agent._oai_messages = {group_manager: history['email_agent']}

    # Initiate the group chat
    user_proxy_agent.initiate_chat(group_manager, message=message, clear_history=False)


    # Save updated history
    # Save updated history after the chat
    save_history({
        "wealth_management_advisor": wealth_management_advisor.chat_messages.get(group_manager),
        "user_proxy_agent": user_proxy_agent.chat_messages.get(group_manager),
        "email_agent": email_agent.chat_messages.get(group_manager)
    })

    # Return the latest response from the chat
    print('RETURNING ========================================================================================================')
    print(group_chat.messages[-1])
    return jsonify(group_chat.messages[-1])


@app.route('/reset', methods=['GET'])
def reset_conversation():
    UserProxyAgent.reset()
   
    return jsonify({"message": "Conversation reset successfully"})


@app.route('/health', methods=['GET'])
def health_check():
    return '', 200


@app.route('/')
def serve_root():
    print("Static folder path:", app.static_folder)  # Check the folder
    print("Index.html exists:", os.path.isfile(os.path.join(app.static_folder, 'index.html')))  # Check the file
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:full_path>')
def serve_app(full_path):
    file_path = os.path.join(app.static_folder, full_path)
    if os.path.isfile(file_path):
        return send_from_directory(app.static_folder, full_path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    app.run(debug=True, port=8080)
