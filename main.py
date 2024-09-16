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

# Initialize agents

# Draft agent to draft an email
draft_agent = AssistantAgent(
    llm_config=llm_config,
    name="Draft Agent",
    system_message="You are the Draft Agent. Your task is to draft an email based on the user's input."
)
# Edit agent to edit the email based on user's feedback
edit_agent = AssistantAgent(
    llm_config=llm_config,
    name="Edit Agent",
    system_message="You are the Edit Agent. You will review the draft and apply any user-provided edits. Add "
)
# Send agent to send the email
send_agent = AssistantAgent(
    llm_config=llm_config,
    name="Send Agent",
    system_message="You are the Send Agent. Once the email is finalized and approved, you will send it."
)

user_proxy_agent = UserProxyAgent(
        name="user",
        llm_config=llm_config,
        description="""
            A human user capable of interacting with AI agents.,
        """,
        system_message="""
            Always appends the word 'TERMINATE' at the end of each message.
        """,
        human_input_mode="NEVER",
        code_execution_config={
            "last_n_messages": 10,
            "work_dir": "market",
            "use_docker": False,
        },
     
    )



register_function(
    send_email_gmail,
    caller=send_agent,  # The assistant agent can suggest calls to the calculator.
    executor=user_proxy_agent,  # The user proxy agent can execute the calculator calls.
    name="send_email_gmail",  # By default, the function name is used as the tool name.
    description="A tool for sending emails.",  # A description of the tool.
  )

# Create a group chat manager
group_chat = GroupChat([draft_agent, edit_agent, send_agent],  messages=[], max_round=120)
group_chat_manager = GroupChatManager(group_chat)



@app.route('/chat', methods=['POST'])
def chat():
    message = request.json["message"]
    response = user_proxy_agent.initiate_chat(group_chat_manager, message=message, clear_history=False)
    print(response)
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
