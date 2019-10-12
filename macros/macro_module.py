"""Syntactic sugar for monadic comprehensions with ZIO for Python.

Here is an example of how the desugaring works.  Consider the following
program written as a monad comprehension:

with monad(result):
    w = 'asdf'
    ~print_line("Good morning!")
    print("Meow")
    x = ~read_line("Enter your name: ")
    y = 42
    print("Woof woof")
    ~print_line(f"Good to meet you, {x} {y} {w}!")
    print("That's all")

============================================================================

First thing we do in macro expansion is get a list of these statements:
tree = [
    w = 'asdf',
    ~print_line("Good morning!"),
    print("Meow"),
    x = ~read_line("Enter your name: "),
    y = 42,
    print("Woof woof"),
    ~print_line(f"Good to meet you, {x} {y} {w}!"),
    print("That's all")
]

We start at the end of the list, finding the first monadic thingy (having '~'),
and we turn that into either a `map` or `flat_map`:

    statement:
      ~print_line(f"Good to meet you, {x} {y} {w}!"),
    remainder:
      [print("That's all")]

    result:
      def fun1(var1):
          return print("That's all")
      print_line(f"Good to meet you, {x} {y} {w}!").map(fun1)

Now get the next previous collection of statements beginning with a '~' term:

    statement:
      x = ~read_line("Enter your name: "),
    remainder:
      [
        y = 42,
        print("Woof woof"),
        def fun1(var1):
          return print("That's all")
        print_line(f"Good to meet you, {x} {y} {w}!").map(fun1)
      ]

    result:
      def fun2(x):
          y = 42
          print("Woof woof")
          def fun1(var1):
              return print("That's all")
          return print_line(f"Good to meet you, {x} {y} {w}!").map(fun1)
      read_line("Enter your name: ").flat_map(fun2)

And get the next previous collection beginning with '~':

    statement:
      ~print_line("Good morning!")
    remainder:
      [
          print("Meow"),
          def fun2(x):,
              y = 42,
              print("Woof woof"),
              def fun1(var1):,
                  return print("That's all"),
              return print_line(f"Good to meet you, {x} {y} {w}!").map(fun1),
          read_line("Enter your name: ").flat_map(fun2)
      ]

    result:
      def fun3(var2):
          print("Meow")
          def fun2(x):
              y = 42
              print("Woof woof")
              def fun1(var1):
                  return print("That's all")
              return print_line(f"Good to meet you, {x} {y} {w}!").map(fun1)
          return read_line("Enter your name: ").flat_map(fun2)
      print_line("Good morning!").flat_map(fun3)

Finally, we have to prepend any lines that come before the first '~', and bind
the final value to the `with monad(result)` variable:

  statement:
    <none>
  remainder:
      w = 'asdf'
      def fun3(var2):
          print("Meow")
          def fun2(x):
              y = 42
              print("Woof woof")
              def fun1(var1):
                  return print("That's all")
              return print_line(f"Good to meet you, {x} {y} {w}!").map(fun1)
          return read_line("Enter your name: ").flat_map(fun2)
      print_line("Good morning!").flat_map(fun3)

  result:
      def fun4(var3):
          w = 'asdf'
          def fun3(var2):
              print("Meow")
              def fun2(x):
                  y = 42
                  print("Woof woof")
                  def fun1(var1):
                      return print("That's all")
                  return print_line(f"Good to meet you, {x} {y} {w}!").map(fun1)
              return read_line("Enter your name: ").flat_map(fun2)
          return print_line("Good morning!").flat_map(fun3)
      result = ZIO.succeed(None).flat_map(fun4)
"""

import ast
from macropy.core import real_repr, unparse
from macropy.core.macros import Macros
from macropy.core.quotes import macros, q, ast_literal, u, name
from typing import Any, Tuple, Optional, List

macros = Macros()

@macros.block
def monad(tree, args, gen_sym, **kw):

    def make_remainder_function(func_name: str, var_name: str, body: List):
        if not body:
            body = [ast.Return(q[name[var_name]])]  # mypy: ignore
        else:
            body.append(ast.Return(body.pop().value))
        return ast.FunctionDef(func_name, ast.arguments([ast.arg(var_name, None)], None, [], [], None, []), body, [], None)

    # Check for `foo = ~bar`
    def is_bind_throwaway(node) -> bool:
        return isinstance(node, ast.Expr) \
            and isinstance(node.value, ast.UnaryOp) \
            and isinstance(node.value.op, ast.Invert)

    # Check for `~bar`
    def is_bind(node) -> bool:
        return isinstance(node, ast.Assign) \
            and isinstance(node.value, ast.UnaryOp) \
            and isinstance(node.value.op, ast.Invert)

    def last_index_of(xs, pred):
        for i in reversed(range(len(xs))):
            if pred(xs[i]):
                return i
        return None

    use_map = True
    while(True):
        idx_last_bind = last_index_of(tree, lambda x: is_bind_throwaway(x) or is_bind(x))
        if idx_last_bind is None:
            func_name = gen_sym()
            if use_map:
                use_map = False
                expr = q[ZIOStatic.succeed(None).map(name[func_name])]
            else:
                expr = q[ZIOStatic.succeed(None).flat_map(name[func_name])]
            last_statement = ast.Assign([ast.Name(args[0].id, ast.Store())], expr)
            func = make_remainder_function(func_name, gen_sym(), tree)
            ret = [func, last_statement]
            return ret
        else:
            func_name = gen_sym()
            var_name = gen_sym() if is_bind_throwaway(tree[idx_last_bind]) else tree[idx_last_bind].targets[0].id
            remainder = tree[(idx_last_bind + 1):]
            func = make_remainder_function(func_name, var_name, remainder)
            if use_map:
                use_map = False
                expr = ast.Expr(q[ast_literal[tree[idx_last_bind].value.operand].map(name[func_name])])
            else:
                expr = ast.Expr(q[ast_literal[tree[idx_last_bind].value.operand].flat_map(name[func_name])])

            tree = tree[0:idx_last_bind] + [func, expr]
            continue
