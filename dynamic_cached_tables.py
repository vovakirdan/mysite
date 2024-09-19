import ast
import operator
import math
import re
from typing import Any, Dict, List, Optional, Set, Union
import numpy as np

def preprocess_expression(expr: str) -> str:
    # Replace logical operators
    expr = expr.replace('&&', ' and ')
    expr = expr.replace('||', ' or ')
    expr = expr.replace('!', ' not ')
    # Replace equality operators
    expr = expr.replace('==', '==')
    expr = expr.replace('!=', '!=')
    # Replace ternary operator
    # pattern: 'condition ? expr_if_true : expr_if_false'
    # replace with: 'expr_if_true if condition else expr_if_false'
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

def safe_eval(expr: str, context: Dict[str, Any]) -> Any:
    node = ast.parse(expr, mode='eval').body

    operators = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
        ast.Eq: operator.eq,
        ast.NotEq: operator.ne,
        ast.Lt: operator.lt,
        ast.LtE: operator.le,
        ast.Gt: operator.gt,
        ast.GtE: operator.ge,
        ast.And: operator.and_,
        ast.Or: operator.or_,
        ast.Not: operator.not_,
    }

    functions = {
        'sqrt': math.sqrt,
        # Add other allowed functions if needed
    }

    def _eval(node):
        if isinstance(node, ast.Num):  # <number>
            return node.n
        elif isinstance(node, ast.Constant):  # For Python 3.6+
            return node.value
        elif isinstance(node, ast.BinOp):
            left = _eval(node.left)
            right = _eval(node.right)
            return operators[type(node.op)](left, right)
        elif isinstance(node, ast.UnaryOp):
            operand = _eval(node.operand)
            return operators[type(node.op)](operand)
        elif isinstance(node, ast.Compare):
            left = _eval(node.left)
            result = True
            for op, comparator in zip(node.ops, node.comparators):
                right = _eval(comparator)
                result = operators[type(op)](left, right)
                left = right
                if not result:
                    break
            return result
        elif isinstance(node, ast.BoolOp):
            if isinstance(node.op, ast.And):
                for value in node.values:
                    if not _eval(value):
                        return False
                return True
            elif isinstance(node.op, ast.Or):
                for value in node.values:
                    if _eval(value):
                        return True
                return False
        elif isinstance(node, ast.IfExp):
            test = _eval(node.test)
            if test:
                return _eval(node.body)
            else:
                return _eval(node.orelse)
        elif isinstance(node, ast.Name):
            if node.id in context:
                return context[node.id]
            elif node.id in functions:
                return functions[node.id]
            else:
                raise NameError(f"Undefined variable or function: {node.id}")
        elif isinstance(node, ast.Call):
            func = _eval(node.func)
            args = [_eval(arg) for arg in node.args]
            return func(*args)
        elif isinstance(node, ast.Subscript):
            value = _eval(node.value)
            slice_value = _eval(node.slice)
            return value[slice_value]
        elif isinstance(node, ast.Index):  # For Python <3.9
            return _eval(node.value)
        else:
            raise TypeError(f"Unsupported type: {type(node)}")

    return _eval(node)

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
        self.conditions = [preprocess_expression(cond) for cond in (conditions or [])]

    def compute_value(self, context: Dict[str, Any]) -> Any:
        # Compute the initial value
        value = safe_eval(self.formula, context)
        # Apply conditions in order
        for condition in self.conditions:
            # Update context with current value
            local_context = {**context, self.name: value}
            value = safe_eval(condition, local_context)
        return value

class Table:
    def __init__(
        self,
        columns: Dict[str, Column],
        reference_table: Dict[str, Union[List[Any], np.ndarray]],
        parameters: Dict[str, Any],
        table_condition: Optional[str] = None
    ) -> None:
        self.columns = columns
        self.reference_table = reference_table
        self.parameters = parameters
        self.table_condition = preprocess_expression(table_condition) if table_condition else None
        self.order = self.topological_sort()

    def __iter__(self):
        num_rows = self.get_num_rows()
        for idx in range(num_rows):
            row_context = {}
            # Build context with reference data and parameters
            context = self.get_row_context(idx)
            for column_name in self.order:
                column = self.columns[column_name]
                # Include previously computed columns
                context.update(row_context)
                # Compute the column value
                value = column.compute_value(context)
                row_context[column_name] = value
            # Check the table condition
            if self.table_condition:
                condition_result = safe_eval(self.table_condition, {**context, **row_context})
                if condition_result:
                    break  # Stop iteration
            yield row_context

    def get_row_context(self, idx: int) -> Dict[str, Any]:
        context = {}
        # Get reference data at index idx
        for key, value in self.reference_table.items():
            if isinstance(value, (list, tuple, np.ndarray)):
                context[key] = value[idx]
            else:
                context[key] = value  # scalar
        # Include parameters
        context.update(self.parameters)
        return context

    def get_num_rows(self) -> int:
        lengths = [len(v) for v in self.reference_table.values() if isinstance(v, (list, tuple, np.ndarray))]
        if lengths:
            num_rows = min(lengths)  # Use the shortest length
        else:
            num_rows = 1
        return num_rows

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

# Example configuration
column_configs = {
    'a': {  # Copy of col1, with condition
        'formula': 'reference_table["col1"]',
        'dependencies': [],
        'conditions': ['(0) if (a < 2) else reference_table["col2"]']
    },
    'b': {  # Column a multiplied by 2
        'formula': 'a * 2',
        'dependencies': ['a'],
        'conditions': []
    },
    'c': {  # Column b multiplied by parameter_x, with conditions
        'formula': 'b * parameter_x',
        'dependencies': ['b', 'parameter_x'],
        'conditions': ['(0) if (c > epsilon) else c', '(-1) if (c == 10) else c']
    }
}

# Build columns
columns = {}
for col_name, config in column_configs.items():
    column = Column(
        name=col_name,
        formula=config['formula'],
        dependencies=config.get('dependencies', []),
        conditions=config.get('conditions', [])
    )
    columns[col_name] = column

# Suppose we have some reference data and parameters
reference_table = {
    'col1': np.array([1, 2, 3, 4, 5]),
    'col2': np.array([10, 20, 30, 40, 50])
}
parameters = {'parameter_x': 10, 'epsilon': 100}

# Table condition
table_condition = 'a > 5 ? True : False'  # Stop if 'a' is greater than 5

# Build the table
table = Table(
    columns=columns,
    reference_table=reference_table,
    parameters=parameters,
    table_condition=table_condition
)

# Iterate over the table and print rows
for row in table:
    print(row)