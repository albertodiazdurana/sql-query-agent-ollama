"""Tests for app/database.py functions."""

from app.database import (
    get_schema_info,
    get_sample_rows,
    build_schema_text,
    build_column_map,
    postprocess_sql,
)


class TestGetSchemaInfo:
    """Tests for get_schema_info()."""

    def test_returns_all_tables(self, test_engine):
        schema = get_schema_info(test_engine)
        assert "Artist" in schema
        assert "Album" in schema
        assert len(schema) == 2

    def test_includes_columns(self, test_engine):
        schema = get_schema_info(test_engine)
        artist_cols = [c["name"] for c in schema["Artist"]["columns"]]
        assert "ArtistId" in artist_cols
        assert "Name" in artist_cols

    def test_includes_foreign_keys(self, test_engine):
        schema = get_schema_info(test_engine)
        album_fks = schema["Album"]["fks"]
        assert len(album_fks) == 1
        assert album_fks[0]["referred_table"] == "Artist"


class TestGetSampleRows:
    """Tests for get_sample_rows()."""

    def test_fetches_sample_data(self, test_engine):
        samples = get_sample_rows(test_engine, ["Artist"], n=2)
        assert "Artist" in samples
        assert len(samples["Artist"]["rows"]) == 2

    def test_includes_column_names(self, test_engine):
        samples = get_sample_rows(test_engine, ["Artist"], n=1)
        assert "columns" in samples["Artist"]
        assert "ArtistId" in samples["Artist"]["columns"]


class TestBuildColumnMap:
    """Tests for build_column_map()."""

    def test_lowercase_mapping(self, test_schema_info):
        col_map = build_column_map(test_schema_info)
        assert col_map["artistid"] == "ArtistId"
        assert col_map["name"] == "Name"

    def test_snake_case_mapping(self, test_schema_info):
        col_map = build_column_map(test_schema_info)
        assert col_map["artist_id"] == "ArtistId"
        assert col_map["album_id"] == "AlbumId"

    def test_table_name_mapping(self, test_schema_info):
        col_map = build_column_map(test_schema_info)
        assert col_map["artist"] == "Artist"
        assert col_map["album"] == "Album"


class TestPostprocessSql:
    """Tests for postprocess_sql() (DEC-004)."""

    def test_ilike_to_like(self, test_column_map):
        sql = "SELECT * FROM Artist WHERE Name ILIKE '%rock%'"
        result = postprocess_sql(sql, test_column_map)
        assert "ILIKE" not in result
        assert "LIKE" in result

    def test_removes_nulls_first(self, test_column_map):
        sql = "SELECT * FROM Artist ORDER BY Name NULLS FIRST"
        result = postprocess_sql(sql, test_column_map)
        assert "NULLS" not in result
        assert "FIRST" not in result

    def test_removes_nulls_last(self, test_column_map):
        sql = "SELECT * FROM Artist ORDER BY Name DESC NULLS LAST"
        result = postprocess_sql(sql, test_column_map)
        assert "NULLS" not in result
        assert "LAST" not in result

    def test_fixes_snake_case_columns(self, test_column_map):
        sql = "SELECT artist_id, title FROM album"
        result = postprocess_sql(sql, test_column_map)
        assert "ArtistId" in result
        assert "Title" in result
        assert "Album" in result

    def test_preserves_sql_keywords(self, test_column_map):
        sql = "SELECT Name FROM Artist WHERE ArtistId = 1"
        result = postprocess_sql(sql, test_column_map)
        assert "SELECT" in result
        assert "FROM" in result
        assert "WHERE" in result

    def test_combined_fixes(self, test_column_map):
        sql = "SELECT artist_id FROM album WHERE title ILIKE '%rock%' ORDER BY artist_id NULLS LAST"
        result = postprocess_sql(sql, test_column_map)
        assert "ArtistId" in result
        assert "Album" in result
        assert "Title" in result
        assert "LIKE" in result
        assert "ILIKE" not in result
        assert "NULLS" not in result


class TestBuildSchemaText:
    """Tests for build_schema_text() (EXP-002 ablation: schema context)."""

    def test_builds_all_tables_when_no_filter(self, test_schema_info):
        result = build_schema_text(test_schema_info)
        assert "CREATE TABLE Artist" in result
        assert "CREATE TABLE Album" in result

    def test_builds_only_selected_tables(self, test_schema_info):
        result = build_schema_text(test_schema_info, tables=["Artist"])
        assert "CREATE TABLE Artist" in result
        assert "CREATE TABLE Album" not in result

    def test_includes_column_definitions(self, test_schema_info):
        result = build_schema_text(test_schema_info, tables=["Album"])
        assert "AlbumId" in result
        assert "Title" in result
        assert "ArtistId" in result

    def test_ignores_unknown_tables(self, test_schema_info):
        result = build_schema_text(test_schema_info, tables=["Artist", "NonExistent"])
        assert "CREATE TABLE Artist" in result
        assert "NonExistent" not in result
