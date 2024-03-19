import os
import db
import googleapiclient.discovery
import googleapiclient.errors
from dotenv import load_dotenv
from openai import OpenAI
import json
import base64
import os
from settings import OPENAI_MODEL
load_dotenv()

OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
client = OpenAI(api_key=OPENAI_API_KEY)
model = OPENAI_MODEL


# Function to encode the image
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def get_query_from_image(query, image_path):
    """GPT-4 Vision model to get the query from the image."""
    # Getting the base64 string
    base64_image = encode_image(image_path)
    response = client.chat.completions.create(
        model="gpt-4-vision-preview",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f'Given the image and user query: `{query}`, use the query as context and  describe the image properly so that the information can be fed to a text-based model to respond to the user query. Do not answer the query.'
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}",
                        },
                    },
                ],
            }
        ],
        max_tokens=300,
    )
    # query = json.loads(response.choices[0].message.content)["query"]
    print("Image description:", response.choices[0].message.content)
    return response.choices[0].message.content


def youtube_search(query):
    """Performs youtube search based on the query."""
    print("Searching youtube for:", query)
    api_service_name = "youtube"
    api_version = "v3"
    api_key = os.environ["YOUTUBE_API_KEY"]

    youtube = googleapiclient.discovery.build(
        api_service_name, api_version, developerKey=api_key
    )

    # enable safe search
    request = youtube.search().list(
        part="snippet", maxResults=1, q=query, safeSearch="strict"
    )
    response = request.execute()
    video_links = [f"https://www.youtube.com/watch?v={item["id"]["videoId"]}" for item in response["items"]]
    print("Video links:", video_links)
    return video_links


def get_tool_youtube_search():
    """Returns the tool definition for youtube search."""
    return {
        "type": "function",
        "function": {
            "name": "youtube_search",
            "description": "Searches for relevant youtube videos based on the query.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The query to search for.",
                    },
                },
                "required": ["query"],
            },
        },
    }


def get_system_message():
    """Returns the system message for the tutor."""
    return {
        "role": "system",
        "content": "You are a tutor. You are helping a student with their queries. Along with query, user can also upload images, and if it does so, you will be provided with the image description for more clarity. You also have access to the following tools: youtube_search. Try to include videos as much as possible in your answers.",
    }


def save_file(file):
    """Saves the file and returns the filename."""
    with open(file.filename, "wb") as f:
        f.write(file.file.read())
    return file.filename


def run_tools(messages, tool_calls):
    """Runs the tools and returns the messages."""
    available_functions = {
        "youtube_search": youtube_search,
    }
    for tool_call in tool_calls:
        function_name = tool_call.function.name
        function_to_call = available_functions[function_name]
        function_args = json.loads(tool_call.function.arguments)
        function_response = function_to_call(**function_args)
        messages.append(
            {
                "tool_call_id": tool_call.id,
                "role": "tool",
                "name": function_name,
                "content": str(function_response),
            }
        )
    return messages


def run_conversation(query, image_path=None, conversation_id=None):
    """Main agent, runs the conversation and returns the response."""

    # Handle conversation
    conversation = None
    if conversation_id is not None:
        conversation = db.get_conversation(conversation_id)

    if conversation:
        messages = conversation["messages"]
    else:
        messages = [get_system_message()]
        conversation_id = db.create_conversation(messages)

    # Create user query
    messages.append({"role": "user", "content": query})

    # Processs image input if provided
    if image_path:
        image_content = get_query_from_image(query, image_path)
        messages.append({"role": "user", "content": f"Here is the description of image provided: {image_content}"})

    # Add search tools
    tools = [get_tool_youtube_search()]

    # Get initial response
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        tools=tools,
        tool_choice="auto",
    )
    response_message = response.choices[0].message
    messages.append(response_message)

    tool_calls = response_message.tool_calls
    # Process tools called
    if tool_calls:
        messages = run_tools(messages, tool_calls)

        # Get final response
        second_response = client.chat.completions.create(
            model=model,
            messages=messages,
        )
        response_message = second_response.choices[0].message
        messages.append(response_message)

    # Update conversation
    db.update_conversation(conversation_id, messages)
    return {"response": response_message.content, "conversation_id": conversation_id}
