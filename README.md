ZIO-py
======
ZIO for Python (see https://github.com/zio/zio).

This is a fairly straightforward (unofficial and plucky) port of the ingenious
[Scala ZIO](https://github.com/zio/zio) library.

About the ZIO monad
-------------------
This particular implementation of the ZIO data structure is based on the
[functional effects](https://github.com/jdegoes/functional-effects/blob/master/src/main/scala/net/degoes/zio/00-intro.scala) training provided by [John De Goes](https://degoes.net/). It
is a vastly simplified version of the amazing official Scala library, but is
still quite useful.

The `ZIO[R, E, A]` monad is basically three monads rolled into one:
- An "IO monad" for writing pure functional programs. A value of type `ZIO[R, E, A]` is a program, which when evaluated given input of type `R`, either fails with a value of type `E` or succeeds with a value of type `A`.

- An [either monad](https://www.freecodecamp.org/news/a-survival-guide-to-the-either-monad-in-scala-7293a680006/) that allows you to "code to the happy path." If an error is encountered anywhere in a sequence of `ZIO` operations, it is returned early.

- A [reader monad](https://en.wikipedia.org/wiki/Monad_(functional_programming)#Environment_monad) for providing inputs to your program.

Unlike Scala's ZIO, this implementation does not include functionality for parallel/concurrent programming. Since we are stuck in Python with the Global Interpreter Lock, we can't have nice things...so this functionality won't be missed anyways. However, future work will certainly explore
supporting this part of the Scala ZIO API.

Perhaps the most important feature of ZIO-py that sets it apart from all other
functional programming libraries is its support for type-safe, ergonomic, and
quite natural "monadic do notation."

Notable Features
----------------
* **New in 2021!** ZIO-py features a clever (novel?) mechanism for programming
with a kind of generalized [monadic do notation](https://stackoverflow.com/questions/57192516/is-do-notation-used-necessarily-in-the-context-of-monad), what appears to be a
significant advancement in bringing ergonomic functional programming to
mainstream languages.  It looks like this general idea was explored in 2018 in
[Exceptionally Monadic Error Handling](https://arxiv.org/pdf/1810.13430.pdf),
albeit from the Haskell side. Interesting, I have not seen the idea applied
anywhere in the wild.

Benefits
--------
* Faster and safer test writing: No more mocking and other monkeypatching tomfoolery. Ok, maybe there is some hyperbole here. But it should significantly reduce the amount of mocking needed. Instead of mocking things, you simply `my_program.provide(x)` your program a test environment, `x`, before calling `unsafe_run(my_program)`. When running code in production, you will `.provide` an instance of a live (real) environment.

* Clear distinction of [side-effecting](https://en.wikipedia.org/wiki/Side_effect_(computer_science)) code based on function type signatures. If a function returns a value of type `ZIO[R, E, A`], you know exactly what that function takes as input, how it can fail, and what it will return if it succeeds. You also know that the function may cause side effects. Any other function can, with some reasonable discipline, be considered free of side effects.

* Code to the happy path while safely handling errors. Since `ZIO` behaves like a (right-biased) Either monad, it is super easy to do [railway-oriented programming](https://swlaschin.gitbooks.io/fsharpforfunandprofit/content/posts/recipe-part2.html).

* Type safety. Everything is statically-checked by mypy. If you get the types wrong, then there is probably a bug in your program. The mypy type checker will find the bugs before they make it to production.

* It's pure, it's functional. It's pure functional programming. It's Pythonic.
It shouldn't be possible. (And someone somewhere is upset that these meddling
kids have made it possible.)

Installation
------------
At the command line:
```bash
$ pip install zio-py
```

Alternatively, you can install `zio-py` from source by cloning this repo and
running the provided `setup.sh` script.

If you are using [mypy](https://github.com/python/mypy) to typecheck your Python
code (and you should be!), add `ziopy.mypy_plugin` to your project's `mypy.ini`
configuration file. For example:
```
[mypy]
plugins = ziopy.mypy_plugin
```

The plugin offers some improved type inference around function type signatures,
and also imposes some type constraints related to the "generalized monadic do"
notation. You won't want to use ZIO-py without it.

How to Use It
-------------
Check out the [Scala ZIO documentation](https://zio.dev/) for the definitive
guide on basic usage of ZIO.  In Scala. :)

Here, we will introduce you to the style of programming that uses the generalized
monadic do notation that is unique to ZIO-py.

Using the "Monadic Do Notation"
-------------------------------
ZIO-py features a kind of type-safe monadic do notation that obviates the need
to festoon your pure functional programs with unruly nested `.flat_map` calls.
Unlike other "monadic do notation as a library" implementations, this one is
100% type-safe.

To use it within the body of a function:

1. Decorate your function as `@ziopy.zio.monadic`.
2. Accept a parameter `do: ziopy.zio.ZIOMonad[A, B]`. (Currently the parameter has
to be called "do", but that can be more flexible later on.)
3. Return a value of type `ziopy.zio.ZIO[A, B, _]` from your function.

The types `A` and `B` have to coincide for type safety. The mypy plugin enforces
that all of these types are consistent with each other. Eventually, mypy _should_
support this kind of type checking it when it gets better support for function
decorators. For now, we use a plugin.

Then, instead of writing
```python
a.flat_map(lambda b: ...)
```
you can write
```python
b = do << a
...
```

That's pretty much it! The type safety guarantees that, if any statement in your monadic code that passed through a `do <<` produces an error, the `@monadic` function has to be capable of returning that error. The same safety idea is used for accessing stuff out of the environment (the `R` in `ZIO[R, E, A]`).

It turns out to be a lot easier to use than Scala's "for comprehension" and Haskell's "do notation" because it's just a regular statement. So you can mix it with loops, conditional logic, etc., which is not possible in those other languages.

How the Monadic Do Notation Works
---------------------------------
Each `do << program` invocation calls the private (and potentially impure) `program._run` function, which returns a value of type `Either[E, A]`. More specifically, it returns either an instance of `Left[E]` or an instance of `Right[A]`. If `left: Left[E]` is returned, we wrap `left.value` in a special exception called `_RaiseLeft`.

Meanwhile, the `@monadic` function decorator adds an exception handler to the decorated function. It catches `raise_left: _RaiseLeft` exceptions, and returns the wrapped value as a ZIO program `ZIO.fail(lambda: raise_left.value)`.

The end result is a control flow mechanism for early return of `Left[E]` values
from your decorated functions.

Example Programs
----------------
```python
from typing import NoReturn, Union

import ziopy.services.console as console
import ziopy.services.system as system
from ziopy.environments import ConsoleSystemEnvironment
from ziopy.services.console import Console, LiveConsole
from ziopy.zio import ZIO, ZIOMonad, monadic, unsafe_run, Environment


@monadic
def program(
    do: ZIOMonad[Console, Union[EOFError, KeyboardInterrupt]]
) -> ZIO[
    Console,
    Union[EOFError, KeyboardInterrupt],
    str
]:
    con = do << Environment()

    do << con.print("Hello, what is your name?")
    name = do << con.input()
    do << con.print(f"Your name is: {name}")
    x = do << ZIO.succeed(1)

    while x < 20:
        x = do << (
            ZIO.succeed(x)
            .map(lambda p: p + 1)
            .flat_map(lambda q: ZIO.succeed(q - 1))
            .flat_map(lambda r: ZIO.succeed(r + 1))
        )

    do << con.print(f"The value of x is: {x}")
    return ZIO.succeed(f"Hello, {name}!")


p = program().provide(LiveConsole())
final_result = unsafe_run(p)
print(f"Final result (1) is: {final_result}")

# You can run the same program (value) over and over again.
final_result_2 = unsafe_run(p)
print(f"Final result (2) is: {final_result_2}")


@monadic
def prog(
    do: ZIOMonad[ConsoleSystemEnvironment, NoReturn]
) -> ZIO[ConsoleSystemEnvironment, NoReturn, int]:
    age = do << console.get_input_from_console(
        prompt="How old are you?\n",
        parse_value=ZIO.from_callable(str).map(int).catch(ValueError).either().to_callable(),
        default_value=21
    )
    do << console.print(f"You are {age} years old.")
    return ZIO.succeed(age)


unsafe_run(
    prog().provide(
        ConsoleSystemEnvironment(console=LiveConsole(), system=system.LiveSystem())
    )
)
```

History
-------
ZIO-py grew out of a 2019 [Root Insurance Company](https://www.joinroot.com/) Hack Days project which experimented with porting ZIO to Python. The barrier to adoption was the fact that Python did not have a good mechanism for handling monadic programming, such as Scala's [for comprehension](https://docs.scala-lang.org/tour/for-comprehensions.html) or Haskell's [do notation](https://en.wikibooks.org/wiki/Haskell/do_notation). I implemented the beginnings of an AST transformer that made it possible to use a kind of primitive do notation [here](https://github.com/harveywi/ziopy#monad-comprehension-syntactic-sugar), but generalizing it to work with general Python AST transformations was extremely difficult. Without a better syntax for monadic programming, nobody would ever want to use it in Python. Nested `.flat_map` everywhere is a mess.

After letting the problem simmer in my head for more than a year, I suddenly had an epiphany one morning:

> "Solve the inversion of control flow problem, and you'll have a better monadic "do" notation than any programming language currently offers."

So that's what I did. I tried out a few different designs, trying to emulate something analogous to [call/cc](https://en.wikipedia.org/wiki/Call-with-current-continuation) in a typesafe way in Python. Next, I used a [fork/exec](https://en.wikipedia.org/wiki/Fork%E2%80%93exec) strategy to simulate call/cc. Ultimately I was able to construct a design that eschewed call/cc, using only `try`/`catch` and an additional thunk in the `@monadic` decorator to achieve the desired control flow.

One of the limiting reagents was that mypy still [has some problems](https://github.com/python/mypy/issues/3157) with type inference with code that uses decorators. So, for the short term, I whipped together a simple `mypy` plugin that properly checks/modifies the type signature of functions that are decorated as `@monadic`.

Figuring out a way to use the library in a type safe way was tricky. I had to subconsciously think for a few days about how to maintain the type safety. The `@monadic` decorator, `do: ZIOMonad[R, E]` argument, and mypy plugin solved that problem pretty well methinks...but YMMV.

Statement of Public Good
------------------------
This project is made possible by:
* The Mathematics and Informatics Institute of Ohio, a nonprofit whose mission is to enrich the citzenry of the State of Ohio via education and public domain contributions to advanced mathematics, computer science, informatics, information theory, data science, and other analytical disciplines.
* [Root Insurance Company](https://www.joinroot.com/). This library is an open source version of one of our widely-used internal Python libraries.
* [John De Goes](https://degoes.net/) and the many [Scala ZIO](https://github.com/zio/zio) contributors.
