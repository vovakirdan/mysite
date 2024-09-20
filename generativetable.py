import numpy as np
import math

class GenerativeTable:
    def __init__(self, table_config, **reference_tables):
        self.table_config = table_config
        self.reference_tables = reference_tables
        self.row_count = 0  # Start row count
        self.columns = table_config['columns']
        self.end_condition = table_config.get('table_end_condition', "")
        self.current_row = {col: None for col in self.columns}

    def __iter__(self):
        return self

    def __next__(self):
        # Check if the table end condition is met
        if self.end_condition and self.eval_expression(self.end_condition):
            raise StopIteration
        
        # Generate next row
        row_data = {}
        for col_name, col_details in self.columns.items():
            formula = col_details['formula']
            conditions = col_details['conditions']
            
            # Apply conditions if any
            value = None
            for condition in conditions:
                value = self.eval_expression(condition)
                if value is not None:
                    break

            # If no conditions apply, calculate the value from the formula
            if value is None:
                value = self.eval_expression(formula)
            
            row_data[col_name] = value

        self.current_row = row_data
        self.row_count += 1
        return row_data

    def eval_expression(self, expr):
        if not expr:
            return None
        
        # Local context for eval
        context = {
            'row': self.row_count,
            'column': self.current_row,
            'math': math,
            **self.reference_tables
        }

        # Catch possible eval errors
        try:
            return eval(expr, {"__builtins__": {}}, context)
        except Exception as e:
            print(f"Error evaluating expression: {expr}, Error: {e}")
            return None

# Example Usage

table_config = {
    "columns": {
        "a": {
            "formula": "10", 
            "dependencies": [], 
            "conditions": []
        },
        "b": {
            "formula": "column['a'] * 2", 
            "dependencies": ["a"], 
            "conditions": ["0 if row % 2 == 0 else 1"]
        }
    },
    "table_end_condition": "column['a'] > 500 or row > 100"
}

# Create the table object
table = GenerativeTable(table_config)

# Iterate over the generated rows
for row in table:
    print(row)