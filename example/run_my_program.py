"""Runs the program defined in `example/my_program.py`

Note that you must `import macropy.activate` at the top of the file.
"""

import macropy.activate
from example.my_program import program

from zio.console import LiveConsole
from zio.runtime import Runtime

if __name__ == "__main__":
    runtime = Runtime[LiveConsole]()
    live_console = LiveConsole()
    print("Running...")
    print(runtime.unsafe_run_sync(program.provide(live_console)))
    print("Done.")
