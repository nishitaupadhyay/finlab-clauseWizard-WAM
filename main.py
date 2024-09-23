import json
import ast
import os
from openai import AsyncOpenAI
from dotenv import load_dotenv, find_dotenv
from email_sender import send_email_gmail
from fastapi import FastAPI, APIRouter, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

load_dotenv(find_dotenv())

app = FastAPI()

SYSTEM_MESSAGE = {
    "role": "system",
    "content": """You are Financial Advisor, a virtual assistant who specializes in performing research on clients, creating and sending emails to clients,
    and providing the user with helpful advice on what topics they should be discussing with their clients given relevant
    client characteristics like age, income level, available assets, planned retirement age, risk tolerance, etc.

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
        use the send_email_gmail tool until the text of the email is confirmed by the User."""
}

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
llm_config = {
    "model": "gpt-4o",
    "api_key": os.environ["OPENAI_API_KEY"],
    "base_url": os.environ["OPENAI_BASE_URL"],
    "temperature": 0,
    "timeout": 120,
    "cache_seed": None
}

client = AsyncOpenAI()

MAX_ITER = 5

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

# Example dummy function hard coded to return the same weather
def get_current_weather(location, unit):
    """Get the current weather in a given location"""
    print('tool selected')
    unit = unit or "Fahrenheit"
    weather_info = {
        "location": location,
        "temperature": "72",
        "unit": unit,
        "forecast": ["sunny", "windy"],
    }
    return json.dumps(weather_info)

def get_clients(city: str = None) -> str:
    """Look in the database to see if there are any clients at a specified city for the User to review"""
    database = {
    "Boston": [
        {
            'name': 'Lawrence Summers', 
            'email':'nishita84@gmail.com', 
            'age': 60, 
            'profession': 'Professor', 
            'affiliation': 'Harvard University',  
            'invested_assets': 180000, 
            'last_contacted_days': 15, 
            'details': 'Lawrence appears to be 10 years from retirement and is estimated to have $40k in investable assets that are not invested in The Fund. Lawrence has been with The Fund for over three years and favors an aggressive risk profile and passive management. Of the assets with The Fund, they appear to draw from a broad array of fund managers, including both The Fund-affiliated and outside funds. However, his current investment mix is stock-heavy, which may pose a risk at his age. It is recommended that Lawrence switch to a more bond-heavy investment strategy to better align with his risk tolerance and nearing retirement.',
            'meeting_notes': 'In the last meeting, Lawrence expressed interest in knowing about trusts and wills for his family, and also increasing his 401k contribution. During our review this week, it was noted that one of the funds Lawrence is heavily invested in experienced a 2% decline in value over the past month.'
        },
        {
            'name': 'Peter Galison', 
            'email':'Lawrence@example.com',
            'age': 64, 
            'profession': 'Professor', 
            'affiliation': 'Harvard University', 
            'invested_assets': 130000, 
            'last_contacted_days': 20, 
            'details': 'Peter has been with The Fund for two years and he favors a conservative strategy that maximizes long term profits while avoiding risk.',
            'meeting_notes': 'Peter was concerned about the current inflation rates and wanted to explore safer investment strategies. He also requested an update on his retirement plan projections.'
        },
        {
            'name': 'Eric Maskin', 
            'email':'Lawrence@example.com', 
            'age': 35, 
            'profession': 'Professor', 
            'affiliation': 'Boston University',  
            'invested_assets': 200000, 
            'last_contacted_days': 10, 
            'details': '',
            'meeting_notes': 'Eric asked for an analysis of cryptocurrency investments. He is also considering increasing his contribution to his 401(k) plan next year.'
        },
        {
            'name': 'Catherine Dulac', 
            'email':'Lawrence@example.com',
            'age': 42, 
            'profession': 'Professor', 
            'affiliation': 'Boston College', 
            'invested_assets': 0, 
            'last_contacted_days': 0, 
            'details': '',
            'meeting_notes': 'Catherine discussed opening a 529 college savings plan for her children. She also wants advice on balancing savings and student loans.'
        },
        {
            'name': 'Gary King',
            'email':'Lawrence@example.com', 
            'age': 62, 
            'profession': 'Professor', 
            'affiliation': 'MIT', 
            'invested_assets': 80000, 
            'last_contacted_days': 50, 
            'details': '',
            'meeting_notes': 'Gary reviewed his current portfolio and discussed reallocating funds from stocks to bonds in anticipation of retirement in the next five years.'
        }
    ],
    "Chicago": [
        {
            'name': 'John Doe', 
            'email':'Lawrence@example.com',
            'age': 55, 
            'profession': 'Professor', 
            'affiliation': 'Harvard University', 
            'active_The Fund_member': True, 
            'invested_assets': 180000, 
            'last_contacted_days': 15, 
            'details': '',
            'meeting_notes': 'John expressed concern about the volatility in the tech sector and is considering shifting some assets to safer bonds. He also asked for updates on ESG (environmental, social, and governance) funds.'
        }
    ],
}

    try:
        if city:
            print("Fetching clients from", database.get(city, []))
            return json.dumps(database.get(city, []))
    except Exception as e:
        print("Error fetching client data", str(e))
        return json.dumps([])

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
    }
]

async def call_tool(tool_call):
    function_name = tool_call.function.name
    arguments = ast.literal_eval(tool_call.function.arguments)

    print('function name', function_name)
    print('arguments: ', arguments)

    if function_name == "get_clients":
        return get_clients(city=arguments.get("city"))
    elif function_name == "get_current_weather":
        return get_current_weather(location=arguments.get("location"), unit=arguments.get("unit"))
    elif function_name == "send_email_gmail":
        return send_email_gmail(
            recipient_email=arguments.get("recipient_email"),
            subject=arguments.get("subject"),
            body=arguments.get("body"),
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
    print("=======RESPONSE IS THISSSS====", message)
    print("=======RESPONSE CONTENT  IS THISSSS====", message.content)

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

@app.post("/chat")
async def chat(request: Request):
    data = await request.json()
    user_message = data.get("message", "")

    print(f"User Message: {user_message}")
    message_history = data.get("message_history",[])

    # Always ensure the system message is the first message in the history
    if not message_history or message_history[0].get("role") != "system":
        message_history.insert(0, SYSTEM_MESSAGE)
    else:
        # If there's already a system message, update it to ensure it's current
        message_history[0] = SYSTEM_MESSAGE
                               
                               
    print("THIS IS THE MESSAGE HISTORY", message_history)

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
                "message_history": message_history
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