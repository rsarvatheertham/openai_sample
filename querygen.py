import os
import openai
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class SQLQueryGenerator:
    def __init__(self, schema_file):
        """
        Initialize the SQLQueryGenerator with a schema loaded from a JSON file.
        :param schema_file: Path to the JSON file containing the schema.
        """
        with open(schema_file, 'r') as file:
            self.schema = json.load(file)

    def generate_query(self, table_name, columns, conditions=None):
        """
        Generate an SQL SELECT query based on the input.
        :param table_name: Name of the table.
        :param columns: List of columns to select.
        :param conditions: Dictionary of conditions for the WHERE clause (optional).
        :return: SQL query string.
        """
        if table_name not in self.schema["tables"]:
            raise ValueError(f"Table '{table_name}' does not exist in the schema.")

        # Validate columns
        for column in columns:
            if column not in self.schema["tables"][table_name]["fields"]:
                raise ValueError(f"Column '{column}' does not exist in table '{table_name}'.")

        # Start building the query
        query = f"SELECT {', '.join(columns)} FROM {table_name}"

        # Add conditions if provided
        if conditions:
            condition_clauses = [f"{col} = '{val}'" for col, val in conditions.items()]
            query += f" WHERE {' AND '.join(condition_clauses)}"

        return query

    def generate_query_from_natural_language(self, user_input):
        """
        Generate an SQL query based on natural language input using OpenAI.
        :param user_input: Natural language description of the query.
        :return: SQL query string.
        """
        # Load OpenAI API config from environment variables
        openai_api_key = os.getenv("AZURE_OPENAI_API_KEY")
        openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        openai_deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
        openai_model = os.getenv("AZURE_OPENAI_MODEL")
        openai_api_version = os.getenv("AZURE_OPENAI_API_VERSION")

        if not all([openai_api_key, openai_endpoint, openai_deployment_name, openai_model, openai_api_version]):
            raise EnvironmentError("One or more OpenAI environment variables are missing.")

        # Configure OpenAI client for Azure
        openai.api_type = "azure"
        openai.api_key = openai_api_key
        openai.api_base = openai_endpoint
        openai.api_version = openai_api_version

        prompt = f"""
        You are an SQL query generator. Based on the following schema:
        {json.dumps(self.schema['tables'], indent=2)}

        Generate an SQL query for the following request:
        "{user_input}"
        """

        try:
            response = openai.ChatCompletion.create(
                deployment_id=openai_deployment_name,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that generates SQL queries."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0,
                max_tokens=150
            )
            return response['choices'][0]['message']['content'].strip()
        except Exception as e:
            return f"Error generating query: {e}"


# Example usage
if __name__ == "__main__":
    schema_file = "employee_schema.json"  # Make sure this file exists in your working directory

    query_generator = SQLQueryGenerator(schema_file)

    # Example 1: Structured query generation
    table_name = "employees"
    columns = ["first_name", "department_id"]
    conditions = {"department_id": "2", "is_active": "true"}
    try:
        sql_query = query_generator.generate_query(table_name, columns, conditions)
        print("Generated SQL Query (Structured Input):")
        print(sql_query)
    except ValueError as e:
        print(f"Error: {e}")

    # Example 2: Natural language input from the user
    while True:
        print("\nEnter your query in natural language (e.g., 'Get the first names and department IDs of all active employees in department 2.'):")
        print("Type 'exit' to quit the program.")
        user_input = input("Your query: ")  # Prompt the user for input

        if user_input.lower() == "exit":
            print("Exiting the program. Goodbye!")
            break

        try:
            sql_query_nl = query_generator.generate_query_from_natural_language(user_input)
            print("\nGenerated SQL Query (Natural Language Input):")
            print(sql_query_nl)
        except EnvironmentError as e:
            print(f"Error: {e}")
