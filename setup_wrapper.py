import sys
import os

# Add the directory containing your setup.py to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Monkey patch the collections module
import collections
if not hasattr(collections, 'Sequence'):
    from collections import abc
    collections.Sequence = abc.Sequence

# Monkey patch more_itertools
import more_itertools.more
if 'Sequence' not in more_itertools.more.__dict__:
    from collections.abc import Sequence
    more_itertools.more.Sequence = Sequence

# Now run the actual setup.py
import setup