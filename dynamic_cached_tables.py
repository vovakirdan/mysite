import ast
import operator
import math
import re
from typing import Any, Callable, Dict, List, Optional, Set, Union
import numpy as np

def preprocess_expression(expr: str) -> str:
    # Replace logical operators
    expr = expr.replace('&&', ' and ')
    expr = expr.replace('||', ' or ')
    expr = expr.replace('!', ' not ')
    # Replace equality operators
    expr = expr.replace('==', '==')
    expr = expr.replace('!=', '!=')
    # Replace 'STOP' and 'CONTINUE' with True and False
    expr = expr.replace('STOP', 'True')
    expr = expr.replace('CONTINUE', 'False')
    # Replace ternary operator
    # pattern: 'condition ? expr_if_true : expr_if_false'
    pattern = r'([^?]+?)\?([^:]+?):(.+)'
    while '?' in expr:
        match = re.search(pattern, expr)
        if not match:
            break
        condition = match.group(1).strip()
        expr_if_true = match.group(2).strip()
        expr_if_false = match.group(3).strip()
        python_expr = f'({expr_if_true}) if ({condition}) else ({expr_if_false})'
        expr = expr[:match.start()] + python_expr + expr[match.end():]
    return expr

class Column:
    def __init__(
        self,
        name: str,
        formula: str,
        dependencies: Optional[List[str]] = None,
        conditions: Optional[List[str]] = None
    ) -> None:
        self.name = name
        self.formula = preprocess_expression(formula)
        self.dependencies = dependencies or []
        self.conditions = conditions or []
        # Compile the formula
        self.formula_code = compile(self.formula, '<string>', 'eval')
        # Compile the conditions
        self.condition_codes = [compile(preprocess_expression(cond), '<string>', 'eval') for cond in self.conditions]

    def compute_value(self, context: Dict[str, Any]) -> Any:
        # Evaluate the formula
        value = eval(self.formula_code, {}, context)
        # Apply conditions sequentially
        local_context = context.copy()
        local_context[self.name] = value
        for code in self.condition_codes:
            # Evaluate the condition, which may modify the value
            value = eval(code, {}, local_context)
            local_context[self.name] = value
        return value

class Table:
    def __init__(
        self,
        table_config: Dict[str, Any],
        parameters: Dict[str, Any]
    ) -> None:
        self.parameters = parameters
        self.reference_table = parameters.get('reference_table', {})
        self.columns = {}
        column_configs = {k: v for k, v in table_config.items() if k != 'condition'}
        self.table_condition = table_config.get('condition', None)
        if self.table_condition:
            # Assuming condition is a string
            self.table_condition_callable = self.parse_table_condition(self.table_condition)
        else:
            self.table_condition_callable = None
        # Build columns
        for col_name, config in column_configs.items():
            column = Column(
                name=col_name,
                formula=config['formula'],
                dependencies=config.get('dependencies', []),
                conditions=config.get('conditions', [])
            )
            self.columns[col_name] = column
        # Determine computation order
        self.order = self.topological_sort()
        # Compute number of rows
        self.num_rows = self.get_num_rows()

    def parse_table_condition(self, condition: str) -> Callable[[Dict[str, Any]], bool]:
        processed_condition = preprocess_expression(condition)
        # Compile the condition into a code object
        code = compile(processed_condition, '<string>', 'eval')
        def evaluate_condition(context: Dict[str, Any]) -> bool:
            return eval(code, {}, context)
        return evaluate_condition

    def get_num_rows(self) -> int:
        lengths = [len(v) for v in self.reference_table.values() if isinstance(v, (list, tuple, np.ndarray))]
        if lengths:
            num_rows = min(lengths)  # Use the shortest length
        else:
            num_rows = 1
        return num_rows

    def __iter__(self):
        for idx in range(self.num_rows):
            context = {}
            # Include parameters
            context.update(self.parameters)
            # Include 'reference_table' with data for this row
            ref_table_row = {}
            for key, value in self.reference_table.items():
                if isinstance(value, (list, tuple, np.ndarray)):
                    ref_table_row[key] = value[idx]
                else:
                    ref_table_row[key] = value  # scalar
            context['reference_table'] = ref_table_row
            # Compute columns in order
            for col_name in self.order:
                column = self.columns[col_name]
                # Build local context including dependencies
                local_context = context.copy()
                # Include dependencies
                local_context.update({dep: context.get(dep) for dep in column.dependencies})
                value = column.compute_value(local_context)
                context[col_name] = value
            # Evaluate table condition if any
            if self.table_condition_callable:
                if self.table_condition_callable(context):
                    break  # Stop iteration
            # Build row
            row = {col_name: context[col_name] for col_name in self.columns}
            yield row

    def compute_all(self) -> List[Dict[str, Any]]:
        return list(self)

    def topological_sort(self) -> List[str]:
        visited: Set[str] = set()
        order: List[str] = []

        def dfs(node: str):
            if node in visited:
                return
            visited.add(node)
            for dep in self.columns[node].dependencies:
                if dep in self.columns:
                    dfs(dep)
            order.append(node)

        for column_name in self.columns:
            dfs(column_name)
        return order

# Example usage:

# Example configuration
column_configs = {
    'a': {
        'formula': 'reference_table["col1"]',
        'dependencies': [],
        'conditions': ['(reference_table["col1"]) if (a < 2) else (reference_table["col2"])']
    },
    'b': {
        'formula': 'a * 2',
        'dependencies': ['a'],
        'conditions': []
    },
    'c': {
        'formula': 'b * parameter_x',
        'dependencies': ['b', 'parameter_x'],
        'conditions': ['(0) if (c > epsilon) else (c)', '(-1) if (c == 10) else (c)']
    }
}

table_config = {
    **column_configs,
    'condition': 'a > 5 ? STOP : CONTINUE'
}

parameters = {
    'parameter_x': 10,
    'epsilon': 100,
    'reference_table': {
        'col1': np.array([1, 2, 3, 4, 5]),
        'col2': np.array([10, 20, 30, 40, 50])
    }
}

# Build the table
table = Table(table_config, parameters)

# Iterate over the table and print rows
for row in table:
    print(row)

# If you want to compute all rows at once
all_rows = table.compute_all()
print(all_rows)