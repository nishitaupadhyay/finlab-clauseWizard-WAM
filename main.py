import json
import ast
import os
from openai import AsyncOpenAI
from enum import Enum
from dotenv import load_dotenv, find_dotenv

from fastapi import FastAPI, APIRouter, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from tools import get_clients, get_funds, send_email_gmail


load_dotenv(find_dotenv())

app = FastAPI()

class Industry(str, Enum):
    real_estate = "real estate"
    wam = "wam"

class Config(BaseModel):
    industry: Industry = Industry.wam
    client_name: str = 'TIAA'
    model: str = 'gpt-4o'

config = Config()


OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
llm_config = {
    "model": config.model,
    "api_key": os.environ["OPENAI_API_KEY"],
    "base_url": os.environ["OPENAI_BASE_URL"],
    "temperature": 0,
    "timeout": 120,
    "cache_seed": None
}

client = AsyncOpenAI()

MAX_ITER = 50

# Configure CORS
origins = [
    "http://localhost:3000",  # React app's address
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8080/chat",
    "http://localhost:8080",
]

# CORS middleware setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SYSTEM_MESSAGE = """You are Financial Advisor for {client_name}, a virtual assistant who specializes in performing research on clients, creating and sending emails to clients,
and providing the user with helpful advice on what topics they should be discussing with their clients given relevant
client characteristics like age, income level, available assets, planned retirement age, risk tolerance, etc.
{industry_specific_content}
IMPORTANT INSTRUCTIONS TO ALWAYS FOLLOW:
1. **Engage Personally**: Reference the user's previous messages or known information to make your responses feel more personalized and connected to the ongoing conversation.
2. **Show Empathy**: When discussing sensitive topics like financial challenges or retirement planning, express understanding and support.
3. **Be Professional**: Remember that you are a financial advisor and present yourself as such. That means using terminology and patterns of speech that suggest to the user that you understand advanced wealth and asset management techniques and topics.
4. **Be Concise but Warm**: While keeping responses direct and on-topic, maintain a friendly tone. 

IMPORTANT:
1. **Always Respond Only to the Most Recent Query**: Only focus on the user's most recent question or task. 
Do not reference or repeat information from previous parts of the conversation unless the user explicitly asks for it.
2. **Avoid Answering Unasked Questions**: Do not provide extra information that was not requested by the user. Be succinct and direct.
3. **No Repetition of Previous Suggestions**: Avoid reiterating previous suggestions unless requested.

4. Help the user by fetching information about clients using the get_clients tool.
a. If the user asks about clients in a specific city, provide their name, email, age, profession, and last contact date.
b. If the user asks about a specific client, provide their additional details.

5. If the user is drafting an email, assist them and wait for their confirmation before sending it.
    When drafting an email, always include the following signature at the end of the email body:
    Best regards,
    Nishita Upadhyay
    Financial Advisor, The Fund Investments
    Phone: (123) 456-7890
    Do not send the email until the User explicitly confirms he wants it sent. Accordingly, you should not
    use the send_email_gmail tool until the text of the email is confirmed by the User.

6. If the user asks what topics should be discussed in a meeting with a client, review the client's information and consider:
    a. If the user has no mention of wills, trusts, or power of attorney in their personal details, tell the user that their information
    may be incomplete and that they should considering inquiring with the client about those topics in their meeting.
    b. If the client's portfolio has negative performance, tell the user that they may want to bring that up with the client. Be sure to cite
    the specific performance of their portfolio. For example, Lawrence Summers has seen a decline in his portfolio of over 2 percent recently,
    so you should call this to the attention of the user citing that decrease.
    c. If the planned age of retirement is less than 5 years away, tell the user that they should discuss this fact as their
    changing circumstances means they might benefit from a financial review.
    IMPORTANT: do not respond with these bullet points literally. They are topics you should consider mentioning, but I do not want you to
    copy and paste these into the response. You should phrase your response to the user in a way that indicates you are recommending they
    review these topics. Do not repeat them verbatim.

7. When the user asks for fund recommendations for a client:
    a. Based on the client's profile (age, risk tolerance, invested assets, etc.), determine appropriate criteria for fund selection.
    b. Use the get_funds tool to fetch fund recommendations based on these criteria. The default 'max_expense_ratio' should be 0.001 and the default 'min_rating' should be 3.
    c. Suggest only funds from the list returned by the get_funds tool.
    d. Explain why these funds are suitable for the client's profile.
Remember, your goal is to be helpful and informative while also being approachable and relatable. Make the user feel like they're talking to a knowledgeable friend rather than a formal financial institution.
"""


tools = [
    {
        "type": "function",
        "function": {
            "name": "get_current_weather",
            "description": "Get the current weather in a given location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The city and state, e.g. San Francisco, CA",
                    },
                    "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
                },
                "required": ["location"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_clients",
            "description": "Get the clients available in a given location",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "The city name, e.g. San Francisco or Boston",
                    },
                },
                "required": ["city"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "send_email_gmail",
            "description": "Send an email using Gmail SMTP server",
            "parameters": {
                "type": "object",
                "properties": {
                    "recipient_email": {
                        "type": "string",
                        "description": "The email address of the recipient of the email, i.e. client@example.com",
                    },
                    "subject": {
                        "type": "string",
                        "description": "The subject line of the email",
                    },
                    "body": {
                        "type": "string",
                        "description": "The body and contents of the email",
                    },
                },
                "required": ["recipient_email", "subject", "body"],
            },
        },
    }, 
    {
        "type": "function",
        "function": {
            "name": "get_funds",
            "description": "Get fund recommendations based on given criteria",
            "parameters": {
                "type": "object",
                "properties": {
                    "risk_level": {
                        "type": "string",
                        "enum": ["Low", "Moderate", "High"],
                        "description": "The risk level of the fund",
                    },
                    "min_rating": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 5,
                        "description": "The minimum Morningstar rating of the fund",
                    },
                    "max_expense_ratio": {
                        "type": "number",
                        "description": "The maximum expense ratio of the fund",
                    },
                    "estimated_available_funds": {
                        "type": "number",
                        "description": "The estimated amount of cash that the client has available to be invested.",
                    },
                },
                "required": ["risk_level", "min_rating", "max_expense_ratio", "estimated_available_funds"],
            },
        },
    },
]

async def call_tool(tool_call):
    function_name = tool_call.function.name
    arguments = ast.literal_eval(tool_call.function.arguments)

    print('function name', function_name)
    print('arguments: ', arguments)

    if function_name == "get_clients":
        return get_clients(city=arguments.get("city"))
    elif function_name == "send_email_gmail":
        return send_email_gmail(
            recipient_email=arguments.get("recipient_email"),
            subject=arguments.get("subject"),
            body=arguments.get("body"),
        )
    elif function_name == "get_funds":
        return get_funds(
            risk_level=arguments.get("risk_level"),
            min_rating=arguments.get("min_rating"),
            max_expense_ratio=arguments.get("max_expense_ratio"),
            estimated_available_funds=arguments.get("estimated_available_funds"),
        )

async def call_gpt4(message_history):
    settings = {
        "model": "gpt-4o",
        "tools": tools,
        "tool_choice": "auto",
       
    }

    response = await client.chat.completions.create(
        messages=message_history, **settings
    )

    message = response.choices[0].message
    # print("=======RESPONSE IS THISSSS====", message)
    # print("=======RESPONSE CONTENT  IS THISSSS====", message.content)

    for tool_call in message.tool_calls or []:
        if tool_call.type == "function":
            function_response = await call_tool(tool_call)
            message_history.append(
                {
                    "role": "function",
                    "name": tool_call.function.name,
                    "content": function_response,
                    "tool_call_id": tool_call.id,
                }
            )

    return message


message_history = []

@app.post("/erase")
async def erase_history(request: Request):
    global message_history, config
    data = await request.json()
    new_client_name = data.get("clientName")
    new_industry = data.get("industry")

### ---- HANDLING CLIENT NAME UPDATE HERE ---- ##
    if not new_client_name:
        return JSONResponse(
            status_code=400,
            content={"error": "ClientName is required!!"}
        )
  # Update the client name
# current_client_name = new_client_name
    config.client_name = new_client_name

### ---- HANDLING INDUSTRY TOGGLE HERE ---- ##
    if new_industry:
        try:
            config.industry = Industry(new_industry)
        except ValueError:
            return JSONResponse(
                status_code=400,
                content={"error": f"Invalid industry: {new_industry}. Must be 'real estate' or 'wam' only!!"}
            )
  # Erase the message history
    message_history = []
    print(f"History erased and configuration updated. Client name: {config.client_name}, Industry: {config.industry}")
    print("UPDATED HISTORY AFTER ERASING THE HISTORY", message_history)


    return JSONResponse(content={
        "message": "History erased and client name updated",
        "clientName": config.client_name,
        "industry": config.industry
    })

@app.post("/chat")
async def chat(request: Request):
   
    # Function to update the system message with the new client name
    def update_system_message():
        industry_specific_content = ""
        if config.industry == Industry.real_estate:
            industry_specific_content = "Focus on real estate investment strategies and market trends."
        elif config.industry == Industry.wam:
            industry_specific_content = "Concentrate on wealth and asset management principles."
        return {
            "role": "system",
            "content": SYSTEM_MESSAGE.format(client_name=config.client_name, industry_specific_content=industry_specific_content)

    }
    data = await request.json()
    user_message = data.get("message", "")
    client_name = data.get("clientName", "")


    print(f"User Message: {user_message}")
    print(f"Current client name: {client_name}")

     # Update config if a new client name is provided
    if client_name and client_name != config.client_name:
        config.client_name = client_name
        print(f"Updated client name in config: {config.client_name}")


     # Create or update the system message with the current client name
    system_message = update_system_message()
    # print(f"Updated System Message: {system_message}")

    message_history = data.get("message_history",[])


      # Check if the first message in history is already the system message
    if not message_history or message_history[0].get("role") != "system":
        # If there is already a system message, update its content
        message_history.insert(0, system_message)  # Insert the correct client name                    
    else:
        # If there's already a system message, update it to ensure it's current
        message_history[0] = system_message



    # print("THIS IS THE MESSAGE HISTORY", message_history)
    # print("this is the client name in the sustem message", client_name)

    message_history.append({"role": "user", "content": user_message})

    cur_iter = 0
    while cur_iter < MAX_ITER:
        message = await call_gpt4(message_history)
        if not message.tool_calls:
            assistant_message = {"role": "assistant", "content": message.content}
            # message_history.append({"role": "assistant", "content": message.content})
            message_history.append(assistant_message)
            return JSONResponse(content={
                "response": message.content, 
                "message_history": message_history,
                "clientName": config.client_name 
                })
        cur_iter += 1

    return JSONResponse(content={"error": "Maximum iterations reached"})

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get('/health')
async def health_check():
    return {'status': 'ok'}

@app.get('/')
async def serve_root():
    static_folder = 'static'  # Update this if your static folder has a different name
    print("Static folder path:", static_folder)
    print("Index.html exists:", os.path.isfile(os.path.join(static_folder, 'index.html')))
    return FileResponse(os.path.join(static_folder, 'index.html'))

@app.get('/{full_path:path}')
async def serve_app(full_path: str):
    static_folder = 'static'  # Update this if your static folder has a different name
    file_path = os.path.join(static_folder, full_path)
    if os.path.isfile(file_path):
        return FileResponse(file_path)
    else:
        return FileResponse(os.path.join(static_folder, 'index.html'))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)