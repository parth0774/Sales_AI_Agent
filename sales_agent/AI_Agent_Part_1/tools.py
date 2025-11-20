import os
import pandas as pd
from pathlib import Path
import warnings
from langchain_experimental.utilities import PythonREPL
from langchain_core.tools import Tool
from pydantic import BaseModel, Field
import logging

warnings.filterwarnings("ignore", message=".*Python REPL can execute arbitrary code.*")
warnings.filterwarnings("ignore", category=UserWarning, module="langchain_experimental.utilities.python")

def get_dataframe_info(csv_path: str) -> dict:
    """
    Load DataFrame and extract schema information for debugging and preamble.
    """
    try:
        path = Path(csv_path).resolve()
        logging.info(f"Loading CSV file from: {path}")
        
        if not path.exists():
            raise FileNotFoundError(f"CSV file not found: {path}")
        
        df = pd.read_csv(path)
        logging.info(f"CSV loaded successfully, total rows: {len(df)}, columns: {list(df.columns)}")
        
        columns_info = []
        for col in df.columns:
            dtype = str(df[col].dtype)
            columns_info.append({'name': col, 'dtype': dtype})
        
        return {
            'columns': columns_info,
            'total_rows': len(df),
            'column_names': list(df.columns)
        }
    except Exception as e:
        logging.error(f"Error loading DataFrame: {e}")
        return {'error': str(e)}


def create_dataframe_preamble(csv_path: str) -> str:
    """
    Generate a preamble describing the DataFrame schema for the model,
    including data types and unique sample values.
    """
    df_info = get_dataframe_info(csv_path)

    if 'error' in df_info:
        return f"Error loading DataFrame info: {df_info['error']}"

    # Load the actual dataframe to compute unique values
    df = pd.read_csv(csv_path)

    preamble = (
        "You are working with a pandas DataFrame named 'df'.\n"
        "**DataFrame Structure:**\n"
        f"- Total rows: {df_info['total_rows']}\n"
        f"- Columns: {', '.join(df_info['column_names'])}\n\n"
        "**Column Details:**\n"
    )

    for col_info in df_info['columns']:
        col = col_info['name']
        dtype = col_info['dtype']

        # Get unique values (safe & truncated)
        uniques = df[col].dropna().unique()
        unique_list = uniques[:10].tolist()  # limit to first 10 unique values

        more = f" (+{len(uniques) - 10} more)" if len(uniques) > 10 else ""

        preamble += (
            f"- {col} ({dtype})\n"
            f"    • Unique values: {unique_list}{more}\n"
        )

    preamble += (
        "\n**Instructions:**\n"
        "- DataFrame 'df' is pre-loaded and ready to use.\n"
        "- Date columns, if any, are converted to datetime.\n"
        "- Boolean columns, if any, are converted to True/False.\n"
        "- Always return or print the result of your Python code.\n"
    )

    return preamble


def create_python_repl_tool(csv_path: str) -> Tool:
    """
    Create a PythonREPL tool with detailed logging for subscription data.
    """
    path = Path(csv_path).resolve()
    df_info = get_dataframe_info(csv_path)
    df_preamble = create_dataframe_preamble(csv_path)
    
    # Initialization code: runs once per execution
    init_code = f"""import pandas as pd
import json
from datetime import datetime

# Load CSV
csv_path = r"{path}"
df = pd.read_csv(csv_path)

# Convert date columns automatically
for col in df.columns:
    if 'date' in col.lower():
        df[col] = pd.to_datetime(df[col], errors='coerce')

# Convert boolean columns
for col in df.columns:
    if df[col].dropna().unique().tolist() == [True, False] or df[col].dropna().unique().tolist() == [False, True]:
        df[col] = df[col].astype(bool)

# Logging for debug
print("DataFrame loaded successfully with shape:", df.shape)
"""

    python_repl = PythonREPL()
    
    def run_python_code(code: str) -> str:
        """
        Run user code in PythonREPL with DataFrame pre-loaded.
        Includes detailed logs for debugging.
        """
        logging.debug("Executing user code...")
        full_code = init_code + "\n\n" + code
        try:
            result = python_repl.run(full_code)
            logging.debug("Execution successful")
            return str(result)
        except FileNotFoundError as e:
            logging.error(f"CSV file not found at {csv_path}")
            return f"Error: CSV file not found at {csv_path}\nOriginal error: {str(e)}"
        except Exception as e:
            logging.error(f"Error executing Python code: {e}")
            return f"Error executing Python code: {str(e)}\nCheck your syntax and DataFrame column names."
    
    # Tool description
    column_list = ', '.join(df_info['column_names'])
    tool_description = f"""Python shell for querying subscription data. DataFrame 'df' has {df_info['total_rows']} rows. Available columns: {column_list}."""
    
    # Define tool input schema
    class ToolInput(BaseModel):
        code: str = Field(
            description=f"Python code to execute using the 'df' DataFrame.\n\n{df_preamble}"
        )
    
    python_tool = Tool(
        name="query_subscription_data",
        description=tool_description,
        func=run_python_code
    )
    
    python_tool.args_schema = ToolInput
    return python_tool


def get_subscription_tool(csv_path: str) -> Tool:
    """
    Return the fully configured PythonREPL tool for subscription data.
    """
    return create_python_repl_tool(csv_path)


# Example usage
if __name__ == "__main__":
    csv_file = "data/subscription_data.csv"
    tool = get_subscription_tool(csv_file)
    
    # Example query
    test_code = """
print(df.head())
"""
    output = tool.func(test_code)
    print("Output:\n", output)
