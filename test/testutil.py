"""Context manager for environment variables.

Taken from https://gist.github.com/sidprak/a3571943bcf6df0565c09471ab2f90b8

Usage:
    os.environ['MYVAR'] = 'oldvalue'
    with EnvironmentVariable('MYVAR', 'myvalue'):
        print os.getenv('MYVAR')    # Should print myvalue.
    print os.getenv('MYVAR')        # Should print oldvalue.
"""
import os


class EnvironmentVariable(object):
    """Context manager for creating a temporary environment variable.

    :param key: Environment variable name.
    :param value: Value to set in environment variable.
    """
    def __init__(self, key, value):
        self.key = key
        self.new_value = value

    def __enter__(self):
        """Sets the environment variable and saves the old value.
        """
        self.old_value = os.environ.get(self.key)
        os.environ[self.key] = self.new_value
        return self

    def __exit__(self, *args):
        """Sets the environment variable back to the way it was before.
        """
        if self.old_value:
            os.environ[self.key] = self.old_value
        else:
            del os.environ[self.key]
