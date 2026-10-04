"""Secure JUnit XML parser.

Uses defusedxml, which forbids DTDs/entity declarations, protecting
against XXE and entity-expansion (billion-laughs) attacks. Malformed or
unsupported documents raise :class:`JUnitParseError` with a useful message.

Status normalization:
    <error>    -> error
    <failure>  -> failed
    <skipped>  -> skipped
    (no child) -> passed
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass, field

from defusedxml.common import DefusedXmlException
from defusedxml.ElementTree import fromstring as _secure_fromstring

from app.ingestion.schemas import TestCaseResult

MAX_JUNIT_BYTES = 5 * 1024 * 1024
MAX_FAILURE_MESSAGE_CHARS = 4000
MAX_FAILURE_TYPE_CHARS = 255
MAX_IDENTITY_CHARS = 1024


class JUnitParseError(ValueError):
    """Raised when JUnit XML is malformed, unsafe, or unsupported."""


@dataclass
class ParsedJUnit:
    cases: list[TestCaseResult] = field(default_factory=list)


def _localname(tag: str) -> str:
    return tag.split("}", 1)[-1] if "}" in tag else tag


def _iter_suites(root: ET.Element) -> list[ET.Element]:
    name = _localname(root.tag)
    if name == "testsuite":
        return [root]
    if name == "testsuites":
        return [el for el in root.iter() if _localname(el.tag) == "testsuite"]
    raise JUnitParseError(f"unsupported root element <{name}>: expected <testsuite(s)>")


def _element_children(element: ET.Element, local: str) -> list[ET.Element]:
    return [el for el in element if _localname(el.tag) == local]


def _parse_duration(raw: str | None) -> float:
    if raw is None:
        return 0.0
    try:
        return max(0.0, float(raw))
    except (TypeError, ValueError):
        return 0.0


def _failure_detail(case_el: ET.Element) -> tuple[str, str | None, str | None]:
    """Return (status, failure_message, failure_type) for one testcase."""
    errors = _element_children(case_el, "error")
    failures = _element_children(case_el, "failure")
    skipped = _element_children(case_el, "skipped")
    if errors:
        node, status = errors[0], "error"
    elif failures:
        node, status = failures[0], "failed"
    elif skipped:
        return "skipped", None, None
    else:
        return "passed", None, None
    text = (node.text or "").strip()
    message = text or node.get("message") or None
    if message is not None and len(message) > MAX_FAILURE_MESSAGE_CHARS:
        message = message[:MAX_FAILURE_MESSAGE_CHARS] + "…[truncated]"
    failure_type = node.get("type") or _localname(node.tag)
    if len(failure_type) > MAX_FAILURE_TYPE_CHARS:
        failure_type = failure_type[:MAX_FAILURE_TYPE_CHARS]
    return status, message, failure_type


def parse_junit(xml_bytes: bytes) -> ParsedJUnit:
    if not xml_bytes or not xml_bytes.strip():
        raise JUnitParseError("uploaded file is empty")
    if len(xml_bytes) > MAX_JUNIT_BYTES:
        raise JUnitParseError(
            f"JUnit file too large ({len(xml_bytes)} bytes, limit is {MAX_JUNIT_BYTES})"
        )
    try:
        root = _secure_fromstring(xml_bytes)
    except DefusedXmlException as exc:
        raise JUnitParseError(f"rejected unsafe XML: {exc}") from exc
    except ET.ParseError as exc:
        raise JUnitParseError(f"malformed XML: {exc}") from exc
    except RecursionError as exc:
        raise JUnitParseError("XML nesting too deep to parse safely") from exc

    suites = _iter_suites(root)
    cases: list[TestCaseResult] = []
    for suite in suites:
        suite_name = suite.get("name") or "unknown"
        for case_el in _element_children(suite, "testcase"):
            test_name = case_el.get("name")
            if not test_name:
                raise JUnitParseError(
                    f"testcase missing required 'name' attribute (suite='{suite_name}')"
                )
            classname = case_el.get("classname") or suite_name or "unknown"
            if len(test_name) > MAX_IDENTITY_CHARS or len(classname) > MAX_IDENTITY_CHARS:
                raise JUnitParseError("test identity exceeds 1024 characters")
            if suite_name != "unknown" and len(suite_name) > 255:
                raise JUnitParseError("suite name exceeds 255 characters")
            status, failure_message, failure_type = _failure_detail(case_el)
            cases.append(
                TestCaseResult(
                    suite_name=None if suite_name == "unknown" else suite_name,
                    classname=classname,
                    test_name=test_name,
                    status=status,  # type: ignore[arg-type]
                    duration=_parse_duration(case_el.get("time")),
                    failure_message=failure_message,
                    failure_type=failure_type,
                )
            )
    if not cases:
        raise JUnitParseError("no test cases found in JUnit file")
    return ParsedJUnit(cases=cases)
