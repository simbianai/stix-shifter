import asyncio
import re
from stix_shifter_utils.modules.base.stix_transmission.base_connector import (
    BaseQueryConnector,
)
from stix_shifter_utils.utils.error_response import ErrorResponder
from stix_shifter_utils.utils import logger
import json


class QueryConnector(BaseQueryConnector):
    def __init__(self, api_client):
        self.api_client = api_client
        self.logger = logger.set_logger(__name__)
        self.connector = __name__.split(".")[1]

    async def create_query_connection(self, query):
        self.logger.debug("Creating query connection...")

        max_retries = 2  # Maximum number of retries
        retry_delay = 20  # Seconds to wait before retrying
        raw_query = query

        query = await clean_query(self.api_client, raw_query)

        for attempt in range(1, max_retries + 1):
            try:
                # Grab the response, extract the response code, and convert it to readable json
                response = await self.api_client.create_search(query)
                response_code = response.code
                response_text = response.read()

                error = None
                response_dict = dict()
                self.logger.debug(f"Query response: {response_code}")

                try:
                    response_dict = json.loads(response_text)
                except ValueError as ex:
                    self.logger.debug(response_text)
                    error = Exception(f"Cannot parse response: {ex} : {response_text}")

                self.logger.debug(f"Query response: {response_dict}")
                self.logger.debug(f"Query error: {error}")

                # Construct a response object
                return_obj = dict()

                if response_code == 201:
                    return_obj["success"] = True
                    return_obj["search_id"] = response_dict["search_id"]
                else:
                    ErrorResponder.fill_error(
                        return_obj,
                        response_dict,
                        ["message"],
                        error=error,
                        connector=self.connector,
                    )
                    if response_code == 422:
                        if query != raw_query:
                            query = raw_query
                            if attempt < max_retries:
                                await asyncio.sleep(retry_delay)  # Wait before retrying
                                raise Exception("Error in getting search status")
                        else:
                            return return_obj
                    elif response_code != 422 and 400 <= response_code <= 500:
                        return return_obj
                    else:
                        self.logger.warning(
                            f"Attempt {attempt}/{max_retries} failed with error: {error}"
                        )
                        if attempt < max_retries:
                            await asyncio.sleep(retry_delay)  # Wait before retrying
                            raise Exception("Error in getting search status")
                self.logger.debug(f"Query result: {return_obj}")
                return return_obj

            except Exception as e:
                self.logger.warning(
                    f"Attempt {attempt}/{max_retries} failed with error: {e}"
                )
                if attempt < max_retries:
                    await asyncio.sleep(retry_delay)  # Wait before retrying
                else:
                    self.logger.error(f"Max retries reached for query: {query}")
                    raise  # Re-raise the exception after max retries


async def clean_query(apiclient, raw_query: str) -> str:
    """
    Clean up a raw AQL query with enhanced support for function calls like QIDNAME():
      1) Identify valid columns and functions from the table
      2) Preserve function calls in SELECT (e.g. QIDNAME(qid))
      3) Handle quoted columns with spaces
      4) Clean up WHERE conditions
    """
    try:
        # --- STEP 1: Determine which table is being queried ---
        if "FROM events".lower() in raw_query.lower():
            table_name = "events"
        elif "FROM flows".lower() in raw_query.lower():
            table_name = "flows"
        else:
            return raw_query

        # Fetch valid columns
        columns_info = await apiclient.get_table_columns(table_name)
        valid_columns = {col["name"].lower() for col in columns_info}

        # Known valid function patterns
        valid_functions = {
            "QIDNAME": ["qid"],
            "CATEGORYNAME": ["category", "highlevelcategory"],
            "LOGSOURCETYPENAME": ["devicetype"],
            "LOGSOURCENAME": ["logsourceid"],
            "PROTOCOLNAME": ["protocolid"],
            "UTF8": ["payload"],
            "DOMAINNAME": ["domainid"],
            "rulename": ["creeventlist"],
        }

        if not valid_columns:
            return raw_query

        # --- STEP 2: Parse query parts ---
        upper_q = raw_query.upper()
        select_index = upper_q.find("SELECT")
        from_index = upper_q.find("FROM")

        if select_index == -1 or from_index == -1:
            return raw_query

        select_part = raw_query[select_index + len("SELECT") : from_index].strip()
        from_part = raw_query[from_index:].strip()

        # Handle WHERE clause
        match_where = re.search(r"\bWHERE\b", from_part, flags=re.IGNORECASE)
        if match_where:
            where_index = match_where.start()
            where_part = from_part[where_index + len("WHERE") :].strip()

            match_end = re.search(
                r"\b(LIMIT|START|STOP|PARAMETERS)\b",
                where_part,
                flags=re.IGNORECASE,
            )
            if match_end:
                where_end_index = match_end.start()
                where_conditions = where_part[:where_end_index].strip()
                after_where = where_part[where_end_index:].strip()
            else:
                where_conditions = where_part
                after_where = ""

            from_part_without_where = from_part[:where_index].strip()
        else:
            where_conditions = ""
            after_where = ""
            from_part_without_where = from_part

        # --- STEP 3: Clean SELECT with enhanced function support ---
        def parse_function_call(item):
            # Match pattern: FUNCTIONNAME(column) [as alias]
            pattern = r"^(\w+)\(([\w.]+)\)(?:\s+as\s+(\w+))?$"
            match = re.match(pattern, item, flags=re.IGNORECASE)
            if match:
                func_name = match.group(1).upper()
                col_name = match.group(2).lower()
                alias = match.group(3)

                # Check if it's a valid function call
                if (
                    func_name in valid_functions
                    and col_name in valid_functions[func_name]
                ):
                    if alias:
                        return f"{func_name}({col_name}) as {alias}"
                    return f"{func_name}({col_name})"
            return None

        select_items = [s.strip() for s in select_part.split(",")]
        cleaned_select_items = []

        for item in select_items:
            if item == "*":
                cleaned_select_items.append(item)
                continue

            # Try to parse as function call first
            func_result = parse_function_call(item)
            if func_result:
                cleaned_select_items.append(func_result)
                continue

            # Handle regular columns
            m_as = re.match(r"^(.*?)\s+as\s+(.*)$", item, flags=re.IGNORECASE)
            if m_as:
                col_part = m_as.group(1).strip()
                alias_part = m_as.group(2).strip()
            else:
                col_part = item.strip()
                alias_part = None

            # Remove surrounding quotes if present
            if col_part.startswith('"') and col_part.endswith('"'):
                col_part = col_part[1:-1]

            # Check if valid column
            if col_part.lower() in valid_columns:
                if " " in col_part:
                    col_part = f'"{col_part}"'

                if alias_part:
                    cleaned_item = f"{col_part} as {alias_part}"
                else:
                    cleaned_item = col_part

                cleaned_select_items.append(cleaned_item)

        # Rebuild SELECT
        cleaned_select_part = ", ".join(cleaned_select_items)

        # --- STEP 4: Clean WHERE clause ---
        cleaned_where = where_conditions
        pattern = re.compile(r"(\w+)\s*(=|LIKE)\s*('[^']*')", flags=re.IGNORECASE)

        def replace_condition(m):
            colname = m.group(1)
            op = m.group(2)
            val = m.group(3)
            if colname.lower() in valid_columns:
                return f"{colname} {op} {val}"
            return "1=0"

        cleaned_where = re.sub(pattern, replace_condition, cleaned_where)

        # Rebuild WHERE portion
        if where_conditions:
            final_where_clause = f"WHERE {cleaned_where} {after_where}".strip()
        else:
            final_where_clause = ""

        # --- STEP 5: Combine everything ---
        final_query = (
            f"SELECT {cleaned_select_part} "
            f"{from_part_without_where} "
            f"{final_where_clause}"
        ).strip()

        return final_query

    except Exception as e:
        return raw_query
