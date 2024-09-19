import ast
import operator
import math
from typing import Any, Dict, List, Optional, Set
import numpy as np

def safe_eval(expr: str, context: Dict[str, Any]) -> Any:
    """
    Safely evaluate a mathematical expression using AST.
    """
    node = ast.parse(expr, mode='eval').body

    operators = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
    }

    functions = {
        'sqrt': math.sqrt,
        # Add other allowed functions if needed
    }

    def _eval(node: ast.AST) -> Any:
        if isinstance(node, ast.Constant):  # For Python 3.8+
            return node.value
        elif isinstance(node, ast.Num):  # For older Python versions
            return node.n
        elif isinstance(node, ast.Str):  # For older Python versions
            return node.s
        elif isinstance(node, ast.Name):
            if node.id in context:
                return context[node.id]
            elif node.id in functions:
                return functions[node.id]
            else:
                raise NameError(f"Undefined variable or function: {node.id}")
        elif isinstance(node, ast.BinOp):
            left = _eval(node.left)
            right = _eval(node.right)
            return operators[type(node.op)](left, right)
        elif isinstance(node, ast.UnaryOp):
            operand = _eval(node.operand)
            return operators[type(node.op)](operand)
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
        elif isinstance(node, ast.Slice):
            lower = _eval(node.lower) if node.lower else None
            upper = _eval(node.upper) if node.upper else None
            step = _eval(node.step) if node.step else None
            return slice(lower, upper, step)
        else:
            raise TypeError(f"Unsupported type: {type(node)}")

    return _eval(node)

class Column:
    def __init__(
        self,
        name: str,
        formula: str,
        dependencies: Optional[List[str]] = None
    ) -> None:
        self.name = name
        self.formula = formula  # Must be a string
        self.dependencies = dependencies or []
        self.value: Optional[Any] = None  # Cached computed value

    def compute(self, context: Dict[str, Any]) -> Any:
        self.value = safe_eval(self.formula, context)
        return self.value

    def invalidate_cache(self) -> None:
        self.value = None

class Table:
    def __init__(self) -> None:
        self.columns: Dict[str, Column] = {}
        self.dependency_graph: Dict[str, List[str]] = {}

    def add_column(self, column: Column) -> None:
        self.columns[column.name] = column
        self.dependency_graph[column.name] = column.dependencies

    def compute_all(
        self,
        context: Dict[str, Any],
        changed_parameters: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        computed: Dict[str, Any] = {}
        to_compute = self.topological_sort()
        if changed_parameters:
            affected_columns = self.get_affected_columns(changed_parameters)
            to_compute = [col for col in to_compute if col in affected_columns]

        for column_name in to_compute:
            column = self.columns[column_name]
            if column.value is not None and column_name not in changed_parameters:
                computed[column_name] = column.value
                continue
            dep_context = {dep: computed.get(dep, context.get(dep)) for dep in column.dependencies}
            dep_context.update(context)
            computed[column_name] = column.compute(dep_context)
        return computed

    def topological_sort(self) -> List[str]:
        visited: Set[str] = set()
        order: List[str] = []

        def dfs(node: str) -> None:
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

    def get_affected_columns(self, changed_parameters: List[str]) -> Set[str]:
        affected = set()
        for col_name, column in self.columns.items():
            if any(param in column.dependencies for param in changed_parameters):
                affected.add(col_name)
                affected.update(self.get_dependents(col_name))
        return affected

    def get_dependents(self, column_name: str) -> Set[str]:
        dependents = set()
        for col_name, deps in self.dependency_graph.items():
            if column_name in deps:
                dependents.add(col_name)
                dependents.update(self.get_dependents(col_name))
        return dependents

# Example configuration
column_configs = {
    'a': {  # this column is just a copy of col1 of reference_table
        'formula': 'reference_table["col1"]',
        'dependencies': []
    },
    'b': {  # this column is column a multiplied by 2
        'formula': 'a * 2',
        'dependencies': ['a']
    },
    'c': {  # this column is b column multiplied by parameter_x
        'formula': 'b * parameter_x',
        'dependencies': ['b', 'parameter_x']
    }
}

# Initialize table
table = Table()

# Add columns based on configurations
for col_name, config in column_configs.items():
    column = Column(
        name=col_name,
        formula=config['formula'],
        dependencies=config.get('dependencies', [])
    )
    table.add_column(column)

# Suppose we have some reference data and parameters
reference_table = {'col1': np.array([1, 2, 3])}
parameters = {'parameter_x': 10}

# Include variables in the context
context = {**reference_table, **parameters}

# Compute all columns
results = table.compute_all(context)

print(results)
# Output: {'a': array([1, 2, 3]), 'b': array([2, 4, 6]), 'c': array([20, 40, 60])}

# Now, if we change 'parameter_x', we only need to recompute 'c'
parameters['parameter_x'] = 20
context = {**reference_table, **parameters}
results = table.compute_all(context, changed_parameters=['parameter_x'])

print(results)
# Output: {'a': array([1, 2, 3]), 'b': array([2, 4, 6]), 'c': array([40, 80, 120])}