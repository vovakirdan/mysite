from typing import TypeVar, Iterable, Callable, AnyStr

Condition = TypeVar('Condition', int, float, str)

def parse_condition(cond: Condition) -> Callable[[int, float, AnyStr], bool]:
    if isinstance(cond, int) or isinstance(cond, float):
        def _(var):
            return var == cond
        return _
    elif isinstance(cond, str):
        if any(("=" in cond, ">" in cond, "<" in cond)):
            modified_cond = cond.replace("<", "").replace(">", "").replace("=", "")
            if "." in modified_cond:
                modified_cond = float(modified_cond)
            else:
                modified_cond = int(modified_cond)
            def ge(var):
                return var >= modified_cond
            def g(var):
                return var > modified_cond
            def l(var):
                return var < modified_cond
            def le(var):
                return var <= modified_cond
            def noteq(var):
                return var != modified_cond
            return {
                ">=": ge,
                ">": g,
                "<": l,
                "<=": le,
                "<>": noteq
            }[cond.replace(str(modified_cond), "")]
            
        else:
            return lambda x: x==cond

def count_if(values: Iterable, criteria: Condition):
    return len(list(filter(parse_condition(criteria), values)))
    
def sum_if(values: Iterable, criteria: Condition):
    return sum(filter(parse_condition(criteria), values))

def average_if(values: Iterable, criteria: Condition):
    a = list(filter(parse_condition(criteria), values))
    return sum(a)/len(a)
