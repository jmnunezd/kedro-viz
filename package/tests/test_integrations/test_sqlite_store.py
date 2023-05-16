import json
import logging
import os
from pathlib import Path
from typing import Dict, cast
from unittest.mock import patch

import boto3
import pytest
from moto import mock_s3
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from kedro_viz.integrations.kedro.sqlite_store import SQLiteStore, _get_dbname, get_db
from kedro_viz.models.experiment_tracking import Base, RunModel

BUCKET_NAME = "test-bucket"


@pytest.fixture
def store_path(tmp_path):
    return Path(tmp_path)


@pytest.fixture
def db_session_class(store_path):
    engine = create_engine(f"sqlite:///{store_path}/session_store.db")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session


@pytest.fixture(scope="class")
def aws_credentials():
    """Mocked AWS credentials for moto"""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"


@pytest.fixture(scope="class")
def mocked_s3_bucket(aws_credentials):
    """S3 Mock Client"""
    with mock_s3():
        conn = boto3.client("s3", region_name="us-east-1")
        conn.create_bucket(Bucket=BUCKET_NAME)
        yield conn


@pytest.fixture
def remote_path():
    return f"s3://{BUCKET_NAME}"


@pytest.fixture
def mock_db1(tmp_path):
    database_loc = str(tmp_path / "db1.db")
    engine = create_engine(f"sqlite:///{database_loc}")
    session_class = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    session = session_class()
    session.add(RunModel(id="1", blob="blob1"))
    session.commit()
    session.close()
    yield Path(database_loc)


@pytest.fixture
def mock_db2(tmp_path):
    database_loc = str(tmp_path / "db2.db")
    engine = create_engine(f"sqlite:///{database_loc}")
    session_class = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    session = session_class()
    session.add(RunModel(id="2", blob="blob2"))
    session.commit()
    session.close()
    yield Path(database_loc)


@pytest.fixture
def mock_db3(tmp_path):
    database_loc = str(tmp_path / "db3.db")
    engine = create_engine(f"sqlite:///{database_loc}")
    session_class = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    session = session_class()
    session.add(RunModel(id="3", blob="blob3"))
    session.commit()
    session.close()
    yield Path(database_loc)


@pytest.fixture
def mock_db4(tmp_path):
    database_loc = str(tmp_path / "db4.db")
    engine = create_engine(f"sqlite:///{database_loc}")
    session_class = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    session = session_class()
    session.add(RunModel(id="3", blob="blob3"))
    session.commit()
    session.close()
    yield Path(database_loc)


def get_files_in_bucket(bucket_name):
    s3 = boto3.client("s3")
    response = s3.list_objects(Bucket=bucket_name)
    files = [obj["Key"] for obj in response.get("Contents", [])]
    return files


@pytest.fixture
def mocked_db_in_s3(mocked_s3_bucket, mock_db1, mock_db2, mock_db3):
    # define the name of the S3 bucket and the database file names
    db1_filename = "db1.db"
    db2_filename = "db2.db"
    db3_filename = "db3.db"

    # upload each mock database file to the mocked S3 bucket
    mocked_s3_bucket.put_object(
        Bucket=BUCKET_NAME, Key=db1_filename, Body=mock_db1.read_bytes()
    )
    mocked_s3_bucket.put_object(
        Bucket=BUCKET_NAME, Key=db2_filename, Body=mock_db2.read_bytes()
    )
    mocked_s3_bucket.put_object(
        Bucket=BUCKET_NAME, Key=db3_filename, Body=mock_db3.read_bytes()
    )

    return get_files_in_bucket(BUCKET_NAME)


@pytest.fixture
def mocked_db_in_s3_repeated_runs(
    mocked_s3_bucket, mock_db1, mock_db2, mock_db3, mock_db4
):
    # define the name of the S3 bucket and the database file names
    db1_filename = "db1.db"
    db2_filename = "db2.db"
    db3_filename = "db3.db"
    db4_filename = "db4.db"

    # upload each mock database file to the mocked S3 bucket
    mocked_s3_bucket.put_object(
        Bucket=BUCKET_NAME, Key=db1_filename, Body=mock_db1.read_bytes()
    )
    mocked_s3_bucket.put_object(
        Bucket=BUCKET_NAME, Key=db2_filename, Body=mock_db2.read_bytes()
    )
    mocked_s3_bucket.put_object(
        Bucket=BUCKET_NAME, Key=db3_filename, Body=mock_db3.read_bytes()
    )
    mocked_s3_bucket.put_object(
        Bucket=BUCKET_NAME, Key=db4_filename, Body=mock_db4.read_bytes()
    )

    return get_files_in_bucket(BUCKET_NAME)


def session_id():
    i = 0
    while True:
        yield f"session_{i}"
        i += 1


@patch.dict(os.environ, {"KEDRO_SQLITE_STORE_USERNAME": "env_user_name"})
@patch("getpass.getuser", return_value="computer_user_name")
def test_get_dbname_with_env_var(mock_getuser):
    dbname = _get_dbname()
    assert dbname == "env_user_name.db"


@patch(
    "os.environ",
    cast(Dict[str, str], {**os.environ, "KEDRO_SQLITE_STORE_USERNAME": None}),
)
@patch("getpass.getuser", return_value="computer_user_name")
def test_get_dbname_without_env_var(mock_getuser):
    dbname = _get_dbname()
    assert dbname == "computer_user_name.db"


class TestSQLiteStore:
    def test_empty(self, store_path):
        sqlite_store = SQLiteStore(store_path, next(session_id()))
        assert not sqlite_store
        assert sqlite_store.location == str(Path(store_path) / "session_store.db")

    def test_save_single_run(self, store_path, db_session_class):
        sqlite_store = SQLiteStore(store_path, next(session_id()))
        sqlite_store.data = {"project_path": store_path, "project_name": "test"}
        sqlite_store.save()
        db = next(get_db(db_session_class))
        loaded_runs = db.query(RunModel).all()
        assert len(loaded_runs) == 1
        assert json.loads(loaded_runs[0].blob) == {
            "project_path": str(store_path),
            "project_name": "test",
        }

    def test_save_multiple_runs(self, store_path, db_session_class):
        session = session_id()
        sqlite_store = SQLiteStore(store_path, next(session))
        sqlite_store.save()
        db = next(get_db(db_session_class))
        assert db.query(RunModel).count() == 1
        # save another session
        sqlite_store2 = SQLiteStore(store_path, next(session))
        sqlite_store2.save()
        db = next(get_db(db_session_class))
        assert db.query(RunModel).count() == 2

    @patch("fsspec.filesystem")
    def test_save_run_with_remote_path(self, mock_fs, store_path, remote_path):
        sqlite_store = SQLiteStore(
            store_path, next(session_id()), remote_path=remote_path
        )
        sqlite_store.data = {"project_path": store_path, "project_name": "test"}
        with patch.object(sqlite_store, "_upload") as mock_upload:
            sqlite_store.save()
            mock_upload.assert_called_once()

    def test_save_run_without_remote_path(self, store_path):
        sqlite_store = SQLiteStore(store_path, next(session_id()))
        sqlite_store.data = {"project_path": store_path, "project_name": "test"}
        with patch.object(sqlite_store, "_upload") as mock_upload:
            sqlite_store.save()
            assert not mock_upload.called

    def test_update_git_branch(self, store_path, mocker):
        sqlite_store = SQLiteStore(store_path, next(session_id()))
        sqlite_store.data = {
            "project_path": store_path,
            "git": {"commit_sha": "123456"},
        }
        mocker.patch("git.Repo.active_branch").name = "test_branch"

        assert sqlite_store._to_json() == json.dumps(
            {
                "project_path": str(store_path),
                "git": {"commit_sha": "123456", "branch": "test_branch"},
            }
        )

    @patch("fsspec.filesystem")
    def test_upload_to_s3_success(self, mock_fs, store_path, remote_path):
        sqlite_store = SQLiteStore(
            store_path, next(session_id()), remote_path=remote_path
        )
        sqlite_store._upload()
        sqlite_store._remote_fs.put.assert_called_once()

    @patch("fsspec.filesystem")
    def test_upload_to_s3_fail(self, mock_fs, store_path, remote_path):
        sqlite_store = SQLiteStore(
            store_path, next(session_id()), remote_path=remote_path
        )
        sqlite_store._remote_fs.put.side_effect = ConnectionError("Connection error")
        with patch.object(logging.Logger, "exception") as mock_log:
            sqlite_store._upload()
            mock_log.assert_called_once()

    @patch("fsspec.filesystem")
    def test_download_from_s3_success(
        self, mock_fs, store_path, remote_path, mocked_db_in_s3
    ):
        sqlite_store = SQLiteStore(
            store_path, next(session_id()), remote_path=remote_path
        )
        sqlite_store._remote_fs.glob.return_value = mocked_db_in_s3
        sqlite_store._download()
        downloaded_dbs = set(Path(sqlite_store.location).parent.glob("*.db")) - {
            Path(sqlite_store.location)
        }
        # Assert that the number of databases downloaded is 3
        assert len(downloaded_dbs) == 3

        # Assert that the paths contain db1.db, db2.db, and db3.db
        assert any("db1.db" in str(db_loc) for db_loc in downloaded_dbs)
        assert any("db2.db" in str(db_loc) for db_loc in downloaded_dbs)
        assert any("db3.db" in str(db_loc) for db_loc in downloaded_dbs)

    @patch("fsspec.filesystem")
    def test_download_from_s3_failure(self, mock_fs, store_path, remote_path):
        sqlite_store = SQLiteStore(
            store_path, next(session_id()), remote_path=remote_path
        )
        sqlite_store._remote_fs.glob.side_effect = ConnectionError("Connection error")
        with patch.object(logging.Logger, "exception") as mock_log:
            sqlite_store._download()
            downloaded_dbs = set(Path(sqlite_store.location).parent.glob("*.db"))
            # Assert that the number of databases downloaded is 0
            assert len(downloaded_dbs) == 0
            mock_log.assert_called_once()

    @patch("fsspec.filesystem")
    def test_merge_databases(
        self, mock_fs, store_path, remote_path, mocked_db_in_s3, db_session_class
    ):
        sqlite_store = SQLiteStore(
            store_path, next(session_id()), remote_path=remote_path
        )
        sqlite_store._remote_fs.glob.return_value = mocked_db_in_s3
        sqlite_store._download()
        sqlite_store._merge()
        db = next(get_db(db_session_class))
        downloaded_dbs = set(Path(sqlite_store.location).parent.glob("*.db")) - {
            Path(sqlite_store.location)
        }
        assert len(downloaded_dbs) == 3
        assert db.query(RunModel).count() == 3

    @patch("fsspec.filesystem")
    def test_merge_databases_with_repeated_runs(
        self,
        mock_fs,
        store_path,
        remote_path,
        mocked_db_in_s3_repeated_runs,
        db_session_class,
    ):
        sqlite_store = SQLiteStore(
            store_path, next(session_id()), remote_path=remote_path
        )
        sqlite_store._remote_fs.glob.return_value = mocked_db_in_s3_repeated_runs
        sqlite_store._download()
        sqlite_store._merge()
        db = next(get_db(db_session_class))
        downloaded_dbs = set(Path(sqlite_store.location).parent.glob("*.db")) - {
            Path(sqlite_store.location)
        }
        assert len(downloaded_dbs) == 4
        assert db.query(RunModel).count() == 3

    @patch("fsspec.filesystem")
    def test_sync(self, mock_fs, store_path, remote_path, mocked_db_in_s3):
        sqlite_store = SQLiteStore(
            store_path, next(session_id()), remote_path=remote_path
        )
        sqlite_store._remote_fs.glob.return_value = mocked_db_in_s3
        with patch.object(sqlite_store, "_download") as mock_download, patch.object(
            sqlite_store, "_merge"
        ) as mock_merge, patch.object(sqlite_store, "_upload") as mock_upload:
            sqlite_store.sync()
            mock_download.assert_called_once()
            mock_merge.assert_called_once()
            mock_upload.assert_called_once()

    @patch("fsspec.filesystem")
    def test_sync_without_remote_path(self, mock_fs, store_path):
        sqlite_store = SQLiteStore(store_path, next(session_id()))
        with patch.object(sqlite_store, "_download") as mock_download, patch.object(
            sqlite_store, "_merge"
        ) as mock_merge, patch.object(sqlite_store, "_upload") as mock_upload:
            sqlite_store.sync()
            assert not mock_download.called
            assert not mock_merge.called
            assert not mock_upload.called
