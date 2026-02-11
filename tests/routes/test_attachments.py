"""
Tests for attachment endpoints.

Endpoints tested:
- GET /attachments/{key} - List attachments on issue
- POST /attachment/{key} - Upload attachment (skipped - write operation)
- DELETE /attachment/{attachment_id} - Delete attachment (skipped - write operation)
"""

import pytest

from helpers import TEST_PROJECT, TEST_ISSUE, run_cli, get_data, run_cli_raw


class TestListAttachments:
    """Test /attachments/{key} endpoint."""

    def test_list_attachments_basic(self):
        """Should list attachments on an issue."""
        result = run_cli("jira", "attachments", TEST_ISSUE)
        data = get_data(result)
        assert isinstance(data, list)

    def test_list_attachments_json_format(self):
        """Should return JSON format by default."""
        result = run_cli("jira", "attachments", TEST_ISSUE, "--format", "json")
        data = get_data(result)
        assert isinstance(data, list)

    def test_list_attachments_rich_format(self):
        """Should format attachments for rich output."""
        stdout, stderr, code = run_cli_raw("jira", "attachments", TEST_ISSUE, "--format", "rich")
        assert code == 0

    def test_list_attachments_ai_format(self):
        """Should format attachments for AI consumption."""
        stdout, stderr, code = run_cli_raw("jira", "attachments", TEST_ISSUE, "--format", "ai")
        assert code == 0

    def test_list_attachments_markdown_format(self):
        """Should format attachments as markdown."""
        stdout, stderr, code = run_cli_raw("jira", "attachments", TEST_ISSUE, "--format", "markdown")
        assert code == 0

    def test_list_attachments_structure(self):
        """Attachments should have expected structure if present."""
        result = run_cli("jira", "attachments", TEST_ISSUE)
        data = get_data(result)
        if len(data) > 0:
            attachment = data[0]
            # Attachments typically have: id, filename, size, mimeType, content
            assert "id" in attachment or "filename" in attachment or "self" in attachment

    def test_list_attachments_invalid_issue(self):
        """Should handle non-existent issue gracefully."""
        stdout, stderr, code = run_cli_raw("jira", "attachments", "NONEXISTENT-99999")
        stdout_lower = stdout.lower()
        assert code != 0
        assert "not found" in stdout_lower or "error" in stdout_lower


class TestAttachmentHelp:
    """Test attachment help system."""

    def test_attachments_help(self):
        """Should show help for attachments command."""
        stdout, stderr, code = run_cli_raw("jira", "attachments", "--help")
        # Should show help or at least not error
        assert code == 0 or "attachments" in stdout.lower()


class TestUploadAttachment:
    """Test /attachment/{key} POST endpoint."""

    def test_upload_single_file(self):
        """Should upload a single file by path."""
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Test content for attachment upload")
            temp_file = f.name

        try:
            result = run_cli("jira", "attachment", TEST_ISSUE, "--file", temp_file)
            data = get_data(result)

            assert isinstance(data, list) and len(data) > 0
            attachment = data[0]
            assert "id" in attachment
            assert "filename" in attachment
        finally:
            os.unlink(temp_file)

    def test_upload_multiple_files(self):
        """Should upload multiple files in one call."""
        import tempfile
        import os

        files = []
        for i in range(3):
            f = tempfile.NamedTemporaryFile(mode='w', suffix=f'_{i}.txt', delete=False)
            f.write(f"Content {i}")
            f.close()
            files.append(f.name)

        try:
            result = run_cli(
                "jira", "attachment", TEST_ISSUE,
                "--file", files[0], "--file", files[1], "--file", files[2],
            )
            data = get_data(result)

            assert isinstance(data, list)
            assert len(data) == 3
        finally:
            for f in files:
                os.unlink(f)


class TestDeleteAttachment:
    """Test /attachment/{attachment_id} DELETE endpoint."""


    def test_delete_attachment(self):
        """Should delete attachment by ID."""
        result = run_cli("jira", "attachment", "10200", "-X", "DELETE")
        data = get_data(result)
        assert data.get("deleted") is True
        assert data.get("attachment_id") == "10200"

    def test_delete_nonexistent_attachment(self):
        """Should handle deleting non-existent attachment."""
        stdout, stderr, code = run_cli_raw("jira", "attachment/delete", "99999999")
        stdout_lower = stdout.lower()
        assert code != 0
        assert "not found" in stdout_lower or "error" in stdout_lower


class TestDeleteAttachmentForbidden:
    """Test that 403 from Jira is returned as HTTP 403, not 400."""

    def test_delete_forbidden_returns_403(self):
        """Bug 4.1: delete_attachment with 403 should return status=403."""
        from helpers import _test_client
        response = _test_client.delete("/jira/attachment/FORBIDDEN-001")
        assert response.status_code == 403
        data = response.json()
        assert data["success"] is False
        assert "permission denied" in data["error"].lower()


class TestUploadSizeLimit:
    """Test that oversized uploads are rejected."""

    def test_upload_over_50mb_returns_413(self):
        """Uploads over 50MB should be rejected with 413."""
        import tempfile
        import os
        from helpers import _test_client

        # Create a sparse file just over the limit (50MB + 1 byte)
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.seek(50 * 1024 * 1024)
            f.write(b"\x00")
            temp_file = f.name

        try:
            response = _test_client.post(
                "/jira/attachment/HMKG-2062",
                json={"files": [temp_file]},
            )
            assert response.status_code == 413
            data = response.json()
            assert data["success"] is False
        finally:
            os.unlink(temp_file)


class TestAttachmentEdgeCases:
    """Test edge cases for attachments."""

    def test_attachment_invalid_key_format(self):
        """Should handle invalid issue key format."""
        stdout, stderr, code = run_cli_raw("jira", "attachments", "invalid-key-format")
        assert ("error" in stdout.lower() or "not found" in stdout.lower() or
                "existiert nicht" in stdout.lower() or code != 0)

    def test_attachment_empty_key(self):
        """Should handle missing issue key."""
        stdout, stderr, code = run_cli_raw("jira", "attachments")
        # Should error - missing required parameter or return not found
        stdout_lower = stdout.lower()
        assert ("error" in stdout_lower or "required" in stderr.lower() or
                "not found" in stdout_lower or code != 0)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
