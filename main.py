import json
import ast
import os
from openai import AsyncOpenAI
from dotenv import load_dotenv, find_dotenv
from email_sender import send_email_gmail
from dummy_funds import get_funds
from fastapi import FastAPI, APIRouter, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

load_dotenv(find_dotenv())

app = FastAPI()



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
            'details': 'Lawrence appears to be 3 years from retirement and is estimated to have $40k in investable assets that are not invested in The Fund. Lawrence has been with The Fund for over three years and favors an high risk profile and passive management. Of the assets with The Fund, they appear to draw from a broad array of fund managers, including both The Fund-affiliated and outside funds. However, his current investment mix is stock-heavy, which may pose a risk at his age. It is recommended that Lawrence switch to a more bond-heavy investment strategy to better align with his risk tolerance and nearing retirement.',
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
                    "max_investment": {
                        "type": "number",
                        "description": "The maximum minimum investment amount for the fund",
                    },
                },
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
    elif function_name == "get_current_weather":
        return get_current_weather(location=arguments.get("location"), unit=arguments.get("unit"))
    elif function_name == "send_email_gmail":
        return send_email_gmail(
            recipient_email=arguments.get("recipient_email"),
            subject=arguments.get("subject"),
            body=arguments.get("body"),
        )
    elif function_name == "get_funds":
        return get_funds(criteria=arguments)

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

current_client_name = ""
message_history = []

@app.post("/erase")
async def erase_history(request: Request):
    global current_client_name, message_history
    data = await request.json()
    new_client_name = data.get("clientName")

    if not new_client_name:
        return JSONResponse(
            status_code=400,
            content={"error": "clientName is required"}
        )
  # Update the client name
    current_client_name = new_client_name
  # Erase the message history
    message_history = []
    print(f"History erased and client name updated to {current_client_name}")
    print("UPDATED HISTORY AFTER ERASING THE HISTORY", message_history)


    return JSONResponse(content={
        "message": "History erased and client name updated",
        "clientName": current_client_name
    })

@app.post("/chat")
async def chat(request: Request):
    global current_client_name
    # Function to update the system message with the new client name
    def update_system_message(client_name):
        return {
        "role": "system",
        "content": f"""You are Financial Advisor for {client_name}, a virtual assistant who specializes in performing research on clients, creating and sending emails to clients,
        and providing the user with helpful advice on what topics they should be discussing with their clients given relevant
        client characteristics like age, income level, available assets, planned retirement age, risk tolerance, etc.
        IMPORTANT INSTRUCTIONS TO ALWAYS FOLLOW:
        1. **Friendly and Personalized Communication**: Always respond in a warm, conversational tone. Use casual language, contractions, and even a touch of humor when appropriate. Imagine you're chatting with a colleague you know well.
        2. **Engage Personally**: Reference the user's previous messages or known information to make your responses feel more personalized and connected to the ongoing conversation.
        3. **Show Empathy**: When discussing sensitive topics like financial challenges or retirement planning, express understanding and support.
        4. **Be Encouraging**: Offer positive reinforcement when the user is making good financial decisions or asking insightful questions.
        5. **Use Relatable Examples**: When explaining complex financial concepts, use everyday analogies or examples that make the information more accessible and engaging.
        7. **Be Concise but Warm**: While keeping responses direct and on-topic, maintain a friendly tone. It's okay to add a brief personal comment or question to build rapport.

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
            b. Based on the client's profile (age, risk tolerance, invested assets, etc.), determine appropriate criteria for fund selection.
            c. Use the get_funds tool to fetch fund recommendations based on these criteria.
            d. Suggest only funds from the list returned by the get_funds tool.
            e. Explain why these funds are suitable for the client's profile.
        Remember, your goal is to be helpful and informative while also being approachable and relatable. Make the user feel like they're talking to a knowledgeable friend rather than a formal financial institution.
        """
    }
    data = await request.json()
    user_message = data.get("message", "")
    client_name = data.get("clientName", "")


    print(f"User Message: {user_message}")
    print(f"Current client name: {client_name}")

     # Create or update the system message with the current client name
    system_message = update_system_message(client_name)
    print(f"Updated System Message: {system_message}")

    message_history = data.get("message_history",[])


      # Check if the first message in history is already the system message
    if not message_history or message_history[0].get("role") != "system":
        # If there is already a system message, update its content
        message_history.insert(0, system_message)  # Insert the correct client name                    
    else:
        # If there's already a system message, update it to ensure it's current
        message_history[0] = system_message



    print("THIS IS THE MESSAGE HISTORY", message_history)
    print("this is the client name in the sustem message", client_name)

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
                "clientName": client_name 
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