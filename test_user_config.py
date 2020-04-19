"""
Just a short script you can use to reassure yourself that your options/env are set up correctly.
"""

import util

print("Parsed options file:")
print(util.parse_options_file())

print("Final config:")
print(util.get_user_config())
