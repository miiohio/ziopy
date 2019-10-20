"""Runs the program defined in `example/my_program.py`

Note that you must `import macropy.activate` at the top of the file.
"""

import macropy.activate  # noqa: F401
from example.my_program import my_program
from zio_py.console import LiveConsole
from zio_py.runtime import Runtime

if __name__ == "__main__":
    runtime = Runtime[LiveConsole]()
    live_console = LiveConsole()
    print("Running...")
    print(runtime.unsafe_run_sync(my_program().provide(live_console)))
    print("Done.")
