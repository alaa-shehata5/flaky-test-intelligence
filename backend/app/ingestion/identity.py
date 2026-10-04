"""Deterministic test identity.

A logical test is identified across runs by::

    {project}::{classname}::{test_name}

The same test in different runs yields the same key; different tests
yield different keys.
"""

MAX_UNIQUE_KEY_CHARS = 2048


def build_unique_key(project: str, classname: str, test_name: str) -> str:
    return f"{project}::{classname}::{test_name}"
