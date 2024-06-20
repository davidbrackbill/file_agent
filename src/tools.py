import cohere
import json

with open("./data.json") as f:
    j = json.load(f)
    key = j["key"]
    sales_database = j["sales_database"]
    product_catalog = j["product_catalog"]

co = cohere.Client(key)
response = co.chat(message="hello world!")


def query_daily_sales_report(day: str) -> dict:
    """
    Function to retrieve the sales report for the given day
    """
    report = sales_database.get(day)
    return {
        "date": day,
        "summary": (
            f"Total Sales Amount: {report['total_sales_amount']}, Total Units Sold: {report['total_units_sold']}"
            if report
            else "No sales data available for this day."
        ),
    }


def query_product_catalog(category: str) -> dict:
    """
    Function to retrieve products for the given category
    """
    products = product_catalog.get(category, [])
    return {"category": category, "products": products}


functions_map = {
    "query_daily_sales_report": query_daily_sales_report,
    "query_product_catalog": query_product_catalog,
}

tools = [
    {
        "name": "query_daily_sales_report",
        "description": "Connects to a database to retrieve overall sales volumes and sales information for a given day.",
        "parameter_definitions": {
            "day": {
                "description": "Retrieves sales data for this day, formatted as YYYY-MM-DD.",
                "type": "str",
                "required": True
            }
        }
    },
    {
        "name": "query_product_catalog",
        "description": "Connects to a a product catalog with information about all the products being sold, including categories, prices, and stock levels.",
        "parameter_definitions": {
            "category": {
                "description": "Retrieves product information data for all products in this category.",
                "type": "str",
                "required": True
            }
        }
    }
]

preamble = """
## Task & Context
You help people answer their questions and other requests interactively. You will be asked a very wide array of requests on all kinds of topics. You will be equipped with a wide range of search engines or similar tools to help you, which you use to research your answer. You should focus on serving the user's needs as best you can, which will be wide-ranging.

## Style Guide
Unless the user asks for a different style of answer, you should answer in full sentences, using proper grammar and spelling.
"""

message = "Can you provide a sales summary for 29th September 2023, and also give me some details about the products in the 'Electronics' category, for example their prices and stock levels?"

response = co.chat(
    message=message,
    tools=tools,
    preamble=preamble,
    model="command-r"
)

tool_results = [
        {
        "call": tool_call,
        "outputs": [functions_map[tool_call.name](**tool_call.parameters)]
        }
        for tool_call in response.tool_calls
        ]

