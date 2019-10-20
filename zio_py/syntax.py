import ast
from typing import List, cast

from macropy.core.macros import Macros
from macropy.core.quotes import macros, q, ast_literal, name

macros = Macros()  # noqa: F811


@macros.decorator
def monadic(tree, gen_sym, **kw):
    if isinstance(tree, ast.FunctionDef):
        return desugar_statement_list([tree], gen_sym)[0]
    else:
        raise Exception("@monad decorator can only be used for function definitions")

# Transforms one of these:
#
#    def my_function(...):
#        bar = 42
#        import whatever
#        ...
#        bippy = ~(x)
#        [...more statements...]
#
# into one of these:
#    bar = 42
#    import whatever
#    ...
#    def rest(bippy):
#        [...more statements...]


def desugar_statement_list(stmts: List[ast.stmt], gen_sym) -> List[ast.stmt]:
    idx = len(stmts)
    while idx >= 0:
        remainder = stmts[idx:]
        remainder_desugared = desugar_remainder(remainder, gen_sym)
        stmts = stmts[:idx] + remainder_desugared
        idx -= 1
    return stmts


def desugar_remainder(remainder: List[ast.stmt], gen_sym) -> List[ast.stmt]:
    if not remainder:
        return []

    stmt = remainder[0]
    if isinstance(stmt, ast.FunctionDef):
        stmt.body = desugar_statement_list(stmt.body, gen_sym)
        return remainder
    elif isinstance(stmt, ast.AsyncFunctionDef):
        stmt.body = desugar_statement_list(stmt.body, gen_sym)
        return remainder
    elif isinstance(stmt, ast.ClassDef):
        return remainder
    elif isinstance(stmt, ast.Return):
        return remainder
    elif isinstance(stmt, ast.Delete):
        return remainder
    elif isinstance(stmt, ast.Assign):
        assign = cast(ast.Assign, stmt)
        if (isinstance(assign.value, ast.UnaryOp) and isinstance(assign.value.op, ast.Invert)):
            # Input:
            #   foo = ~bar
            #   [...rest...]
            #   return 42
            # Output:
            #   def temp(bar_bind_result):
            #      foo = bar_bind_result  # (handles various assignment stuff)
            #      [...rest...]
            #      return 42
            #   bar.{map, flat_map}(temp)
            unary_op = cast(ast.UnaryOp, assign.value)
            func_name = gen_sym()

            flat_map_arg_name = gen_sym()
            assign.value = q[name[flat_map_arg_name]]

            flat_map_function_def = ast.FunctionDef(
                func_name,
                ast.arguments([ast.arg(flat_map_arg_name, None)], None, [], [], None, []),
                remainder if remainder else [],  # TODO
                [], None)
            flat_map_call = q[ast_literal[unary_op.operand].flat_map(name[func_name])]

            return_call = ast.Return(flat_map_call)

            return [flat_map_function_def, return_call]
        else:
            return remainder
    elif isinstance(stmt, ast.AugAssign):
        return remainder
    elif isinstance(stmt, ast.AnnAssign):
        return remainder
    elif isinstance(stmt, ast.For):
        return remainder
    elif isinstance(stmt, ast.AsyncFor):
        return remainder
    elif isinstance(stmt, ast.While):
        return remainder
    elif isinstance(stmt, ast.If):
        stmt.body = desugar_statement_list(stmt.body, gen_sym)
        stmt.orelse = desugar_statement_list(stmt.orelse, gen_sym)
        return remainder
    elif isinstance(stmt, ast.With):
        stmt.body = desugar_statement_list(stmt.body, gen_sym)
        return remainder
    elif isinstance(stmt, ast.AsyncWith):
        stmt.body = desugar_statement_list(stmt.body, gen_sym)
        return remainder
    elif isinstance(stmt, ast.Raise):
        return remainder
    elif isinstance(stmt, ast.Try):
        stmt.body = desugar_statement_list(stmt.body, gen_sym)
        # NOTE: Semantics are not clear here.  Should try to tie this into
        # ZIO's error types.

        stmt.orelse = desugar_statement_list(stmt.orelse, gen_sym)
        stmt.finalbody = desugar_statement_list(stmt.finalbody, gen_sym)

        for handler in stmt.handlers:
            handler.body = desugar_statement_list(handler.body, gen_sym)
        return remainder
    elif isinstance(stmt, ast.Assert):
        return remainder
    elif isinstance(stmt, ast.Import):
        return remainder
    elif isinstance(stmt, ast.ImportFrom):
        return remainder
    elif isinstance(stmt, ast.Global):
        return remainder
    elif isinstance(stmt, ast.Nonlocal):
        return remainder
    elif isinstance(stmt, ast.Expr):
        expr = cast(ast.Expr, stmt.value)
        if isinstance(expr, ast.BoolOp):
            return remainder
        elif isinstance(expr, ast.BinOp):
            return remainder
        elif isinstance(expr, ast.UnaryOp):
            if isinstance(expr.op, ast.Invert):
                unary_op = stmt.value

                # Input:
                #   ~bar
                #   [...rest...]
                #   return 42
                # Output:
                #   def temp(throwaway):
                #      [...rest...]
                #      return 42
                #   bar.{map, flat_map}(temp)
                func_name = gen_sym()

                flat_map_arg_name = gen_sym()

                flat_map_function_def = ast.FunctionDef(
                    func_name,
                    ast.arguments([ast.arg(flat_map_arg_name, None)], None, [], [], None, []),
                    remainder[1:] if remainder[1:] else [],  # TODO
                    [], None)
                flat_map_call = q[ast_literal[unary_op.operand].flat_map(name[func_name])]
                return_call = ast.Return(flat_map_call)

                return [flat_map_function_def, return_call]
            else:
                return remainder
        elif isinstance(expr, ast.Lambda):
            return remainder
        elif isinstance(expr, ast.IfExp):
            return remainder
        elif isinstance(expr, ast.Dict):
            return remainder
        elif isinstance(expr, ast.Set):
            return remainder
        elif isinstance(expr, ast.ListComp):
            return remainder
        elif isinstance(expr, ast.SetComp):
            return remainder
        elif isinstance(expr, ast.DictComp):
            return remainder
        elif isinstance(expr, ast.GeneratorExp):
            return remainder
        elif isinstance(expr, ast.Await):
            return remainder
        elif isinstance(expr, ast.Yield):
            return remainder
        elif isinstance(expr, ast.YieldFrom):
            return remainder
        elif isinstance(expr, ast.Compare):
            return remainder
        elif isinstance(expr, ast.Call):
            return remainder
        elif isinstance(expr, ast.Compare):
            return remainder
        elif isinstance(expr, ast.Num):
            return remainder
        elif isinstance(expr, ast.Str):
            return remainder
        elif isinstance(expr, ast.FormattedValue):
            return remainder
        elif isinstance(expr, ast.JoinedStr):
            return remainder
        elif isinstance(expr, ast.Bytes):
            return remainder
        elif isinstance(expr, ast.NameConstant):
            return remainder
        elif isinstance(expr, ast.Ellipsis):
            return remainder
        elif isinstance(expr, ast.Attribute):
            return remainder
        elif isinstance(expr, ast.Subscript):
            return remainder
        elif isinstance(expr, ast.Starred):
            return remainder
        elif isinstance(expr, ast.Name):
            return remainder
        elif isinstance(expr, ast.List):
            return remainder
        elif isinstance(expr, ast.Tuple):
            return remainder
        else:
            return remainder
    elif isinstance(stmt, ast.Pass):
        return remainder
    elif isinstance(stmt, ast.Break):
        return remainder
    elif isinstance(stmt, ast.Continue):
        return remainder
    else:
        raise TypeError(f"Unexpected ast statement type: {stmt}")
