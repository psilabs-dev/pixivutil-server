import pytest
from pydantic import ValidationError

from PixivServer.models.pixiv_worker import (
    DownloadArtworkByIdRequest,
    DownloadArtworksByMemberIdRequest,
    DownloadArtworksByTagsRequest,
)


class TestDownloadArtworkByIdRequest:
    """Tests for DownloadArtworkByIdRequest model."""

    def test_valid_artwork_id(self):
        """Test creating request with valid artwork ID."""
        request = DownloadArtworkByIdRequest(artwork_id=123456)
        assert request.artwork_id == 123456

    def test_artwork_id_as_string_number(self):
        """Test that string numbers are coerced to int."""
        request = DownloadArtworkByIdRequest(artwork_id="123456")
        assert request.artwork_id == 123456
        assert isinstance(request.artwork_id, int)

    def test_invalid_artwork_id_type(self):
        """Test that non-numeric strings raise validation error."""
        with pytest.raises(ValidationError):
            DownloadArtworkByIdRequest(artwork_id="not_a_number")

    def test_negative_artwork_id(self):
        """Test that negative IDs are accepted (validation at business logic layer)."""
        request = DownloadArtworkByIdRequest(artwork_id=-1)
        assert request.artwork_id == -1


class TestDownloadArtworksByMemberIdRequest:
    """Tests for DownloadArtworksByMemberIdRequest model."""

    def test_valid_member_id(self):
        """Test creating request with valid member ID."""
        request = DownloadArtworksByMemberIdRequest(member_id=789012)
        assert request.member_id == 789012

    def test_member_id_as_string_number(self):
        """Test that string numbers are coerced to int."""
        request = DownloadArtworksByMemberIdRequest(member_id="789012")
        assert request.member_id == 789012
        assert isinstance(request.member_id, int)

    def test_invalid_member_id_type(self):
        """Test that non-numeric strings raise validation error."""
        with pytest.raises(ValidationError):
            DownloadArtworksByMemberIdRequest(member_id="invalid")


class TestDownloadArtworksByTagsRequest:
    """Tests for DownloadArtworksByTagsRequest model."""

    def test_minimal_valid_request(self):
        """Test creating request with only required fields."""
        request = DownloadArtworksByTagsRequest(
            tags="landscape",
            sort_order="date_d"
        )
        assert request.tags == "landscape"
        assert request.sort_order == "date_d"
        assert request.wildcard is False
        assert request.start_date is None
        assert request.end_date is None
        assert request.bookmark_count is None
        assert request.type_mode == "a"

    def test_full_valid_request(self):
        """Test creating request with all fields."""
        request = DownloadArtworksByTagsRequest(
            tags="anime girl",
            wildcard=True,
            start_date="2024-01-01",
            end_date="2024-12-31",
            bookmark_count=100,
            sort_order="popular_d",
            type_mode="i"
        )
        assert request.tags == "anime girl"
        assert request.wildcard is True
        assert request.start_date == "2024-01-01"
        assert request.end_date == "2024-12-31"
        assert request.bookmark_count == 100
        assert request.sort_order == "popular_d"
        assert request.type_mode == "i"

    @pytest.mark.parametrize("sort_order", [
        "date_d",
        "date",
        "popular_d",
        "popular_male_d",
        "popular_female_d",
    ])
    def test_valid_sort_orders(self, sort_order):
        """Test all valid sort_order literal values."""
        request = DownloadArtworksByTagsRequest(
            tags="test",
            sort_order=sort_order
        )
        assert request.sort_order == sort_order

    def test_invalid_sort_order(self):
        """Test that invalid sort_order raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            DownloadArtworksByTagsRequest(
                tags="test",
                sort_order="invalid_order"
            )
        assert "sort_order" in str(exc_info.value)

    @pytest.mark.parametrize("type_mode", ["a", "i", "m"])
    def test_valid_type_modes(self, type_mode):
        """Test all valid type_mode literal values."""
        request = DownloadArtworksByTagsRequest(
            tags="test",
            sort_order="date_d",
            type_mode=type_mode
        )
        assert request.type_mode == type_mode

    def test_invalid_type_mode(self):
        """Test that invalid type_mode raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            DownloadArtworksByTagsRequest(
                tags="test",
                sort_order="date_d",
                type_mode="x"
            )
        assert "type_mode" in str(exc_info.value)

    def test_optional_fields_none(self):
        """Test that optional fields can be None."""
        request = DownloadArtworksByTagsRequest(
            tags="test",
            sort_order="date_d",
            wildcard=False,
            start_date=None,
            end_date=None,
            bookmark_count=None
        )
        assert request.start_date is None
        assert request.end_date is None
        assert request.bookmark_count is None

    def test_bookmark_count_as_string(self):
        """Test that bookmark_count string is coerced to int."""
        request = DownloadArtworksByTagsRequest(
            tags="test",
            sort_order="date_d",
            bookmark_count="500"
        )
        assert request.bookmark_count == 500
        assert isinstance(request.bookmark_count, int)

    def test_tags_with_special_characters(self):
        """Test that tags with special characters are accepted."""
        special_tags = "tag:with:colons (parentheses) 日本語"
        request = DownloadArtworksByTagsRequest(
            tags=special_tags,
            sort_order="date_d"
        )
        assert request.tags == special_tags

    def test_wildcard_default_value(self):
        """Test that wildcard defaults to False."""
        request = DownloadArtworksByTagsRequest(
            tags="test",
            sort_order="date_d"
        )
        assert request.wildcard is False

    def test_type_mode_default_value(self):
        """Test that type_mode defaults to 'a'."""
        request = DownloadArtworksByTagsRequest(
            tags="test",
            sort_order="date_d"
        )
        assert request.type_mode == "a"
