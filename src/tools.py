import cohere
from pathlib import Path

def client(key: str) -> cohere.AsyncClient:
    return cohere.AsyncClient(key)

def get_file_contents(file: Path) -> dict:
    """
    Retrieves the text contents of the file into memory.
    """
    with open(file, 'r') as f:
        return {
            "file": file,
            "contents": f.read(),
        }

functions_map = {
    "get_file_contents": get_file_contents,
}

TOOLS = [
    {
        "name": get_file_contents.__name__,
        "description": get_file_contents.__doc__,
        "parameter_definitions": {
            "file": {
                "description": "File path to grab contents from",
                "type": "Path",
                "required": True
            }
        }
    },
]

async def query(client: cohere.AsyncClient, message: str, preamble: str = "", args: dict = {}) -> str:
    tool_check = await client.chat(
            message=message + f"\n {args=}",
            force_single_step=True,
            tools=TOOLS,
            preamble=preamble,
            model="command-r"
            )

    tool_results = [
            {
            "call": tool_call,
            "outputs": [functions_map[tool_call.name](**tool_call.parameters)]
            }
            for tool_call in tool_check.tool_calls
            ]

    model_results = await client.chat(
        message=message,
        force_single_step=True,
        tools=TOOLS,
        tool_results=tool_results,
        preamble=preamble,
        model="command-r",
        temperature=0.3
    )

    if model_results.finish_reason == 'COMPLETE':
        return model_results.text
    else:
        return f"Failed with {model_results.finish_reason=}"

