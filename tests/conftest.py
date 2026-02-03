"""Shared pytest fixtures for SQL Query Agent tests."""

import pytest
from sqlalchemy import create_engine, text


@pytest.fixture
def test_engine():
    """Create an in-memory SQLite database with a minimal test schema.

    Schema matches a subset of Chinook (Artist, Album) to test database
    functions without requiring the full database file.
    """
    engine = create_engine("sqlite:///:memory:")
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE Artist (
                ArtistId INTEGER PRIMARY KEY,
                Name TEXT NOT NULL
            )
        """))
        conn.execute(text("""
            CREATE TABLE Album (
                AlbumId INTEGER PRIMARY KEY,
                Title TEXT NOT NULL,
                ArtistId INTEGER,
                FOREIGN KEY (ArtistId) REFERENCES Artist(ArtistId)
            )
        """))
        conn.execute(text("INSERT INTO Artist (ArtistId, Name) VALUES (1, 'AC/DC')"))
        conn.execute(text("INSERT INTO Artist (ArtistId, Name) VALUES (2, 'Accept')"))
        conn.execute(text("INSERT INTO Album (AlbumId, Title, ArtistId) VALUES (1, 'For Those About To Rock', 1)"))
        conn.execute(text("INSERT INTO Album (AlbumId, Title, ArtistId) VALUES (2, 'Balls to the Wall', 2)"))
        conn.commit()
    return engine


@pytest.fixture
def test_schema_info():
    """Return schema info matching the test_engine schema."""
    return {
        "Artist": {
            "columns": [
                {"name": "ArtistId", "type": "INTEGER"},
                {"name": "Name", "type": "TEXT"},
            ],
            "pk": ["ArtistId"],
            "fks": [],
        },
        "Album": {
            "columns": [
                {"name": "AlbumId", "type": "INTEGER"},
                {"name": "Title", "type": "TEXT"},
                {"name": "ArtistId", "type": "INTEGER"},
            ],
            "pk": ["AlbumId"],
            "fks": [{"referred_table": "Artist", "referred_columns": ["ArtistId"]}],
        },
    }


@pytest.fixture
def test_column_map():
    """Return a column map for the test schema."""
    return {
        "artistid": "ArtistId",
        "artist_id": "ArtistId",
        "name": "Name",
        "artist": "Artist",
        "albumid": "AlbumId",
        "album_id": "AlbumId",
        "title": "Title",
        "album": "Album",
    }
