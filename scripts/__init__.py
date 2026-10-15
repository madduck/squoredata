"""Build and release helpers.

The package marker makes ``scripts.generate_ts`` a single, unambiguous module
name, so mypy does not see the generator under two names when a test imports
it.
"""
