# ZIO.py
ZIO for Python (see https://github.com/zio/zio)

This is a fairly straightforward (unofficial and plucky) port of the
ingenious Scala ZIO library.  Work in progress.

# Running the examples

First, set up a Python virtual environment:
```
$ pipenv install
$ pipenv shell
```

To run the basic example:

```
$ python -m example.example

Good morning!
What is your name? William
Good to meet you, William!
Result: None
The end!
```

To run the example that uses monad comprehension syntax:
```
python -m example.run_my_program

Running...
Good morning sunshine!
It's a fantastic day to write ZIO programs in Python.
Enter your name: William
Good to meet you, William!
Your age is 42.
That's all folks.
1000
Done.
```

# Using ZIO

Check out the [Scala ZIO documentation](https://zio.dev/) for the definitive
guide on using ZIO.  In Scala. :)

Here is a basic console I/O program using ZIO for Python:

```python
from zio.zio import ZIO, ZIOStatic
from zio.console import Console

def print_line(line: str) -> ZIO[Console, NoReturn, None]:
    return ZIOStatic.access_m(lambda env: env.print(line))

def read_line(prompt: str) -> ZIO[Console, Exception, str]:
    return ZIOStatic.access_m(lambda env: env.input(prompt))

program: ZIO[Console, Exception, None] = \
    print_line("Good morning!") \
    .flat_map(lambda _: read_line("What is your name? ")
    .flat_map(lambda name: print_line(f"Good to meet you, {name}!")))  # noqa
```

Note that `program` is just a data structure that describes the effects of 
reading and writing to/from the console.  To run the program you have to first
construct a `runtime` (instance of `Runtime`).  Below we create a runtime that
that can run programs whose _environment_ is of type `LiveConsole`.

```python
from zio.runtime import Runtime
from zio.console import LiveConsole

runtime = Runtime[LiveConsole]()
```

Next, construct a `LiveConsole` environment:

```python
live_console = LiveConsole()
```

Finally, _provide_ the environment to `program`, and have the runtime run the
program using `unsafe_run_sync`, producing a value called `result`:

```python
result = runtime.unsafe_run_sync(program.provide(live_console))
```

# Monad comprehension syntactic sugar
(A Pythonista somewhere squirms and writhes in agony.  Shrug!)

Using `flat_map` and `map` throughout Python code quickly becomes unruly.  ZIO
for Python uses [macropy](https://github.com/lihaoyi/macropy) to enable an
alternative syntax that is much flatter AND THEREFORE MORE PYTHONIC.  (You 
cannot argue with me here, don't even try.)

To use it, first import the following at the top of your source file:

```python
from zio.syntax import macros, monad
```

This will load the macro tooling, which you can invoke by creating a `with` block
to create a monadic value that is bound to the variable called `program` (you
can call it whatever you want):

```python
# To keep the IDE happy, declare `program` here.  Technically this
# is not necessary, as it is instantiated/bound via the `with monad`
# block below.
program: ZIO[Console, Exception, int]

with monad(program):
    ...
```

Now put your ZIO code in place of the ellipsis and sprinkle on some syntactic
sugar.  Simple!

```python
with monad(program):
    ~print_line("Good morning!")
    name = ~read_line("What is your name? ")
    ~print_line(f"Good to meet you, {name}!")
```

You might be wondering about the `~` operators (a.k.a. 
[Emacs turds](https://news.slashdot.org/comments.pl?sid=1021471&cid=25675361)).
Inside of a `with monad` block, the `~` operator indicates that its operand
is a `ZIO` value and must be either `flat_map`'d or `map`'d over.  It's analogous
to the following "for comprehension" syntax in Scala, but without the superfluous
underscores:

```scala
for {
  _    <- printLine("Good morning!")
  name <- readLine("What is your name? ")
  _    <- printLine(s"Good to meet you, {name}!")
} yield ()
```

Currently, the macro only desugars expressions where the statement starts with
a `~` operator (e.g., `~print_line('foo')`), or is an assignment with the `~`
immediately to the right of the equals sign (e.g., `foo = ~read_line('bar')`).

Future work will make the desugaring process a little less ad-hoc, and maybe
even move the macro into a separate library that can be used with other
Python monads.

Here is a more sophisticated program:
```python
with monad(program):
    # You can declare variables that are not lifted into a monadic context.
    w = 'sunshine'

    # This is a monadic bind where we bind to a throwaway variable.
    # Desugars to `print_line(...).flat_map(...)`
    ~print_line(f'Good morning {w}!')

    # You *can* include effectful lines.  That's fine.
    print("It's a fantastic day to write ZIO programs in Python.")

    # This is a monadic bind where the variable is called `name`.
    # Desugars (approximately) to `read_line(...).flat_map(lambda name: ...)`
    name = ~read_line("Enter your name: ")
    your_age = 42
    ~print_line(f"Good to meet you, {name}!")
    ~print_line(f"Your age is {your_age}.")

    # The `~ZIOStatic.succeed(1000)` is like `return 1000` in Haskell, or
    # `yield 1000` in Scala.
    print("That's all folks.")
    ~ZIOStatic.succeed(1000)
```