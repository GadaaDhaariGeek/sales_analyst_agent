import os
import sqlite3
import pandas as pd
from dotenv import load_dotenv
load_dotenv()

import json

def load_csv_files_into_sqlitedb():
    """Load CSV files from the specified directory into an in-memory SQLite database."""

    conn = sqlite3.connect(os.environ["DB_NAME"])
    files_dict = {
        "cities": "cities.csv",
        "countries": "countries.csv",
        "customers": "customers.csv",
        "employees": "employees.csv",
        "products": "products.csv",
        "sales": "sales.csv"
    }
    
    for table, path in files_dict.items():
        full_path = os.path.join(os.environ["DATA_DIR"], path)
        df = pd.read_csv(full_path)
        df.to_sql(table, con=conn, index=False, if_exists='replace')


    conn.close()
    # return conn


def get_table_schema_and_sample_rows(DB_NAME: str):
    """Create the json formatted string having schema of tables and some sample rows of each table."""
    """
    {
    "tables": {
        "employees": {
        "schema": {
            "id": "INTEGER PRIMARY KEY",
            "name": "TEXT",
            "country": "TEXT",
            "sales": "INTEGER"
        },
        "sample_rows": [
            {"id": 1, "name": "Alice", "country": "India", "sales": 500},
            {"id": 2, "name": "Bob", "country": "USA", "sales": 300}
        ]
        },
        "orders": {
        "schema": {
            "order_id": "INTEGER PRIMARY KEY",
            "employee_id": "INTEGER",
            "amount": "REAL",
            "date": "TEXT"
        },
        "sample_rows": [
            {"order_id": 101, "employee_id": 1, "amount": 200.5, "date": "2023-07-10"},
            {"order_id": 102, "employee_id": 2, "amount": 150.0, "date": "2023-07-11"}
        ]
        }
    }
    }
    """
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # To access columns by name
    cursor = conn.cursor()
    print(type(conn))
    cursor.execute("select name from sqlite_master where type='table';")
    # print()
    tables = [tb[0] for tb in cursor.fetchall()]
    print(f"\n\nTables: ")
    print(tables)
    # print(cursor.fetchall())
    # schemas = {}
    # samples = {}
    schema_and_samples = {"tables": {}}
    for tb in tables:
        schema_and_samples["tables"][tb] = {"schema": {}, "sample_rows": []}
        cursor.execute(f"PRAGMA table_info({tb})")
        schema = cursor.fetchall()
        # print(type(schema))
        # schema = [{"column_name": col[1], "data_type": col[2]} for col in schema]
        schema = {col[1]: col[2] for col in schema}
        # print(f"\n\nTable: {tb} \nSchema:\n {schema}")
        # print(schema)
         # col = (cid, name, type, notnull, dflt_value, pk)
        # schemas[tb] = schema
        schema_and_samples["tables"][tb]["schema"] = schema
        
        cursor.execute(f"select * from {tb} limit 2")
        data_head = cursor.fetchall()
        # print(data_head)
        # sample_data = [{"column_name": schema[""]}]
        records_list = []
        for row in data_head:
            # one_record = [{
            #         "column_name": col_name["column_name"],
            #         "data_type": col_name["data_type"],
            #         "value": row[col_name["column_name"]]
            #     } for col_name in schema]
            one_record = {key: row[key] for key, _ in schema.items()}
            # for col_name in schema:
                # row_dict[col_name]
                # one_record.append()
            records_list.append(one_record)
        # print(records_list)
        # break
        # samples[tb] = records_list
        schema_and_samples["tables"][tb]["sample_rows"] = records_list
    
    conn.close()
    # for tb in tables:
    #     print(f"\n\nTable name: \n{tb}")
    #     print(f"\nSchema: \n{json.dumps(schemas[tb], indent=4)}")
    #     print(f"\nRecords: \n{json.dumps(samples[tb], indent=4)}")
    #     print("="*150)

    # return schemas, samples
    return schema_and_samples





