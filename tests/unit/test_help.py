"""Unit tests for help route pure functions."""

from jira.routes.help import (
    condense_body_schema,
    condense_endpoint,
    condense_parameter,
    extract_enum_from_description,
    format_help_ai,
    format_help_text,
    resolve_ref,
)


class TestExtractEnumFromDescription:
    def test_colon_pattern(self):
        result = extract_enum_from_description("format: json, rich, ai")
        assert result == ["json", "rich", "ai"]

    def test_parenthesis_pattern(self):
        result = extract_enum_from_description("Output format (json, rich, ai)")
        assert result == ["json", "rich", "ai"]

    def test_no_match(self):
        assert extract_enum_from_description("A plain description") is None

    def test_none_input(self):
        assert extract_enum_from_description(None) is None

    def test_empty_string(self):
        assert extract_enum_from_description("") is None

    def test_single_value_returns_none(self):
        """Single value after colon doesn't match (regex requires comma-separated list)."""
        assert extract_enum_from_description("format: json") is None

    def test_colon_pattern_with_extra_spaces(self):
        result = extract_enum_from_description("output: one,  two,   three")
        assert result == ["one", "two", "three"]


class TestCondenseParameter:
    def test_basic_string_param(self):
        param = {"name": "query", "schema": {"type": "string"}}
        result = condense_parameter(param)
        assert result["name"] == "query"
        assert result["required"] is False
        assert result["type"] == "string"

    def test_required_param(self):
        param = {"name": "key", "required": True, "schema": {"type": "string"}}
        result = condense_parameter(param)
        assert result["required"] is True

    def test_enum_in_schema(self):
        param = {
            "name": "format",
            "schema": {"type": "string", "enum": ["json", "rich", "ai"]},
        }
        result = condense_parameter(param)
        assert result["enum"] == ["json", "rich", "ai"]

    def test_enum_extracted_from_description(self):
        param = {
            "name": "format",
            "description": "Output format: json, rich, ai",
            "schema": {"type": "string"},
        }
        result = condense_parameter(param)
        assert result["enum"] == ["json", "rich", "ai"]

    def test_schema_enum_takes_precedence_over_description(self):
        param = {
            "name": "format",
            "description": "Output format: json, rich, ai",
            "schema": {"type": "string", "enum": ["xml", "csv"]},
        }
        result = condense_parameter(param)
        assert result["enum"] == ["xml", "csv"]

    def test_with_default(self):
        param = {
            "name": "limit",
            "schema": {"type": "integer", "default": 50},
        }
        result = condense_parameter(param)
        assert result["default"] == 50

    def test_with_min_max_constraints(self):
        param = {
            "name": "limit",
            "schema": {"type": "integer", "minimum": 1, "maximum": 100},
        }
        result = condense_parameter(param)
        assert result["min"] == 1
        assert result["max"] == 100

    def test_long_description_truncated(self):
        """Descriptions >= 100 chars are excluded from the result."""
        long_desc = "x" * 100
        param = {
            "name": "query",
            "description": long_desc,
            "schema": {"type": "string"},
        }
        result = condense_parameter(param)
        assert "description" not in result

    def test_short_description_included(self):
        param = {
            "name": "query",
            "description": "Search query",
            "schema": {"type": "string"},
        }
        result = condense_parameter(param)
        assert result["description"] == "Search query"

    def test_missing_schema_defaults_to_string(self):
        param = {"name": "q"}
        result = condense_parameter(param)
        assert result["type"] == "string"


class TestResolveRef:
    def test_valid_ref(self):
        openapi = {
            "components": {
                "schemas": {
                    "Foo": {"type": "object", "properties": {"bar": {"type": "string"}}}
                }
            }
        }
        result = resolve_ref("#/components/schemas/Foo", openapi)
        assert result["type"] == "object"
        assert "bar" in result["properties"]

    def test_nested_ref(self):
        openapi = {"a": {"b": {"c": {"value": 42}}}}
        result = resolve_ref("#/a/b/c", openapi)
        assert result == {"value": 42}

    def test_missing_ref_returns_empty_dict(self):
        openapi = {"components": {"schemas": {}}}
        result = resolve_ref("#/components/schemas/Missing", openapi)
        assert result == {}


class TestCondenseBodySchema:
    def test_basic_properties(self):
        schema = {
            "properties": {
                "summary": {"type": "string"},
                "description": {"type": "string"},
            },
        }
        result = condense_body_schema(schema, {})
        names = [p["name"] for p in result]
        assert "summary" in names
        assert "description" in names
        assert all(p["required"] is False for p in result)

    def test_required_fields(self):
        schema = {
            "properties": {
                "summary": {"type": "string"},
                "optional_field": {"type": "string"},
            },
            "required": ["summary"],
        }
        result = condense_body_schema(schema, {})
        by_name = {p["name"]: p for p in result}
        assert by_name["summary"]["required"] is True
        assert by_name["optional_field"]["required"] is False

    def test_anyof_nullable(self):
        """anyOf with null type picks the non-null type."""
        schema = {
            "properties": {
                "description": {
                    "anyOf": [
                        {"type": "string"},
                        {"type": "null"},
                    ]
                }
            },
        }
        result = condense_body_schema(schema, {})
        assert result[0]["type"] == "string"

    def test_ref_resolution(self):
        openapi = {
            "components": {
                "schemas": {
                    "CreateBody": {
                        "properties": {
                            "title": {"type": "string"},
                        },
                        "required": ["title"],
                    }
                }
            }
        }
        schema = {"$ref": "#/components/schemas/CreateBody"}
        result = condense_body_schema(schema, openapi)
        assert len(result) == 1
        assert result[0]["name"] == "title"
        assert result[0]["required"] is True

    def test_with_default_and_enum(self):
        schema = {
            "properties": {
                "priority": {
                    "type": "string",
                    "default": "Medium",
                    "enum": ["Low", "Medium", "High"],
                },
            },
        }
        result = condense_body_schema(schema, {})
        assert result[0]["default"] == "Medium"
        assert result[0]["enum"] == ["Low", "Medium", "High"]


class TestCondenseEndpoint:
    def test_get_with_params(self):
        spec = {
            "description": "Search for issues.\nMore details here.",
            "parameters": [
                {
                    "name": "query",
                    "in": "query",
                    "required": True,
                    "schema": {"type": "string"},
                },
            ],
        }
        result = condense_endpoint("/jira/search", "get", spec, {})
        assert result["method"] == "GET"
        assert result["path"] == "/jira/search"
        assert result["summary"] == "Search for issues."
        assert len(result["params"]) == 1
        assert result["params"][0]["name"] == "query"

    def test_post_with_body(self):
        openapi = {
            "components": {
                "schemas": {
                    "CreateIssueBody": {
                        "properties": {
                            "summary": {"type": "string"},
                        },
                        "required": ["summary"],
                    }
                }
            }
        }
        spec = {
            "summary": "Create an issue",
            "requestBody": {
                "content": {
                    "application/json": {
                        "schema": {"$ref": "#/components/schemas/CreateIssueBody"}
                    }
                }
            },
        }
        result = condense_endpoint("/jira/issue", "post", spec, openapi)
        assert result["method"] == "POST"
        assert result["summary"] == "Create an issue"
        assert len(result["params"]) == 1
        assert result["params"][0]["name"] == "summary"
        assert result["params"][0]["required"] is True

    def test_no_params(self):
        spec = {"description": "List all projects"}
        result = condense_endpoint("/jira/projects", "get", spec, {})
        assert result["method"] == "GET"
        assert result["summary"] == "List all projects"
        assert "params" not in result

    def test_summary_falls_back_to_summary_field(self):
        spec = {"summary": "Fallback summary"}
        result = condense_endpoint("/jira/test", "get", spec, {})
        assert result["summary"] == "Fallback summary"

    def test_header_params_excluded(self):
        spec = {
            "description": "Test endpoint",
            "parameters": [
                {"name": "Authorization", "in": "header", "schema": {"type": "string"}},
                {"name": "key", "in": "path", "schema": {"type": "string"}},
            ],
        }
        result = condense_endpoint("/jira/issue/{key}", "get", spec, {})
        assert len(result["params"]) == 1
        assert result["params"][0]["name"] == "key"

    def test_multipart_form_body(self):
        spec = {
            "description": "Upload attachment",
            "requestBody": {
                "content": {
                    "multipart/form-data": {
                        "schema": {
                            "properties": {
                                "file": {"type": "string"},
                            },
                        }
                    }
                }
            },
        }
        result = condense_endpoint("/jira/attach", "post", spec, {})
        assert len(result["params"]) == 1
        assert result["params"][0]["name"] == "file"


class TestFormatHelpText:
    def test_get_endpoint_no_method_shown(self):
        endpoints = [
            {"method": "GET", "path": "/jira/search", "summary": "Search issues"},
        ]
        text = format_help_text(endpoints)
        assert "jira/search" in text
        assert "[GET]" not in text

    def test_post_endpoint_method_shown(self):
        endpoints = [
            {"method": "POST", "path": "/jira/issue", "summary": "Create issue"},
        ]
        text = format_help_text(endpoints)
        assert "[POST]" in text

    def test_with_params(self):
        endpoints = [
            {
                "method": "GET",
                "path": "/jira/search",
                "summary": "Search issues",
                "params": [
                    {"name": "query", "required": True, "type": "string"},
                    {
                        "name": "format",
                        "required": False,
                        "type": "string",
                        "enum": ["json", "rich"],
                        "default": "rich",
                    },
                ],
            },
        ]
        text = format_help_text(endpoints)
        assert "--query*" in text
        assert "--format" in text
        assert "[json, rich]" in text
        assert "(default: rich)" in text

    def test_header_line(self):
        text = format_help_text([])
        assert "Jira CLI - Available Commands" in text
        assert "=" * 40 in text

    def test_path_replaces_slash_jira(self):
        endpoints = [
            {"method": "GET", "path": "/jira/projects", "summary": "List projects"},
        ]
        text = format_help_text(endpoints)
        assert "jira/projects" in text
        assert "/jira/projects" not in text


class TestFormatHelpAi:
    def test_markdown_headers(self):
        endpoints = [
            {"method": "GET", "path": "/jira/search", "summary": "Search issues"},
        ]
        text = format_help_ai(endpoints)
        assert "# Jira API Endpoints" in text
        assert "## GET /jira/search" in text
        assert "Search issues" in text

    def test_params_formatting(self):
        endpoints = [
            {
                "method": "POST",
                "path": "/jira/issue",
                "summary": "Create issue",
                "params": [
                    {"name": "summary", "required": True, "type": "string"},
                    {
                        "name": "priority",
                        "required": False,
                        "type": "string",
                        "enum": ["Low", "High"],
                    },
                    {"name": "count", "required": False, "type": "integer"},
                ],
            },
        ]
        text = format_help_ai(endpoints)
        assert "## POST /jira/issue" in text
        assert "Params:" in text
        assert "summary*" in text
        assert "priority:[Low,High]" in text
        assert "count:integer" in text

    def test_no_params_line_when_empty(self):
        endpoints = [
            {"method": "GET", "path": "/jira/status", "summary": "Status check"},
        ]
        text = format_help_ai(endpoints)
        assert "Params:" not in text

    def test_string_type_not_shown(self):
        """String params without enum show just the name, not ':string'."""
        endpoints = [
            {
                "method": "GET",
                "path": "/jira/search",
                "summary": "Search",
                "params": [
                    {"name": "query", "required": False, "type": "string"},
                ],
            },
        ]
        text = format_help_ai(endpoints)
        assert "query:string" not in text
        assert "Params: query" in text
