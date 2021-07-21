from logging import DEBUG, INFO
from typing import Text

from argument_getter import add_argument, get_arguments, pass_getter_arguments
from logger import set_level
from module_runner import run

DEBUG_KEY: Text = "Debug"
MODULE_KEY: Text = "Module"


if __name__ == '__main__':
    pass_getter_arguments(description="Load and run module.")

    debug_level_dest: Text = "logging_level"
    add_argument(DEBUG_KEY, 'debug', const_value=DEBUG, default=INFO, description="Show all debugging messages",
                 to_name=debug_level_dest)
    set_level(get_arguments(DEBUG_KEY)[debug_level_dest])

    module: Text = "module"
    add_argument(MODULE_KEY, module, description="The name of the module to be loaded.")
    run(get_arguments(MODULE_KEY)[module])

