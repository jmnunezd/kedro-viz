"""kedro_viz.intergrations.kedro.sqlite_store is a child of BaseSessionStore
which stores sessions data in the SQLite database"""

import getpass
import json
import logging
import os
import uuid
from pathlib import Path
from typing import Any, Generator, List, Optional

import fsspec
from kedro.framework.session.store import BaseSessionStore
from kedro.io.core import get_protocol_and_path
from sqlalchemy import MetaData, create_engine, event
from sqlalchemy.orm import sessionmaker

from kedro_viz.database import create_db_engine
from kedro_viz.models.experiment_tracking import Base, RunModel

logger = logging.getLogger(__name__)


def get_db(session_class: sessionmaker) -> Generator:
    """Makes connection to the database"""
    try:
        database = session_class()
        yield database
    finally:
        database.close()


def _get_dbname():
    username = os.environ.get("KEDRO_SQLITE_STORE_USERNAME") or getpass.getuser()
    return username + ".db"


def _is_json_serializable(obj: Any):
    try:
        json.dumps(obj)
        return True
    except (TypeError, OverflowError):
        return False


class SQLiteStore(BaseSessionStore):
    """Stores the session data on the sqlite db."""

    def __init__(self, *args, remote_path: str = None, **kwargs):
        """Sets remote_path for Collaborative Experiment Tracking"""
        super().__init__(*args, **kwargs)
        self._remote_path = remote_path

        if self.remote_location:
            protocol, _ = get_protocol_and_path(self.remote_location)
            self._remote_fs = fsspec.filesystem(protocol)

    @property
    def location(self) -> Path:
        """Returns location of the sqlite_store database"""
        return Path(self._path) / "session_store.db"

    @property
    def remote_location(self) -> Optional[str]:
        """Returns the remote location of the sqlite_store database on the cloud"""
        return self._remote_path

    def _to_json(self) -> str:
        """Returns session_store information in json format after converting PosixPath to string"""
        session_dict = {}
        for key, value in self.data.items():
            if key == "git":
                try:
                    import git  # pylint: disable=import-outside-toplevel

                    branch = git.Repo(search_parent_directories=True).active_branch
                    value["branch"] = branch.name
                except ImportError as exc:  # pragma: no cover
                    logger.warning("%s:%s", exc.__class__.__name__, exc.msg)

            if _is_json_serializable(value):
                session_dict[key] = value
            else:
                session_dict[key] = str(value)
        return json.dumps(session_dict)

    def save(self):
        """Save the session store info on db and uploads it to the cloud if a remote cloud path is provided ."""
        engine, session_class = create_db_engine(self.location)
        Base.metadata.create_all(bind=engine)
        database = next(get_db(session_class))

        session_store_data = RunModel(id=self._session_id, blob=self._to_json())
        database.add(session_store_data)
        database.commit()
        if self.remote_location:
            self._upload()

    def _upload(self):
        """Uploads the session store database file to the specified remote path on the cloud storage."""
        db_name = _get_dbname()
        try:
            # Fsspec will read credentials stored as env variables
            # Upload the local file to the remote path
            self._remote_fs.put(f"{self.location}", f"{self.remote_location}/{db_name}")
        except Exception as e:
            logging.exception(f"Error uploading file to S3: {e}")

    def _download(self) -> List[str]:
        """Downloads all the session store database files from the specified remote path on the cloud storage
        to your local project.
        Note: All the database files are deleted after they are merged to the main session_store.db.

        Returns:
        A list of local filepath in string format for all the databases

        """
        databases_location = []

        try:
            # Find all the databases at the remote path
            databases = self._remote_fs.glob(f"{self.remote_location}/*.db")

            # Download each database to a local filepath
            for database in databases:
                database_name = Path(database).name
                db_loc = Path(self._path) / database_name
                self._remote_fs.get(f"{database}", f"{db_loc}")
                databases_location.append(db_loc)
        except Exception as e:
            logging.exception(f"Error downloading file from S3: {e}")
        # Return the list of local filepaths
        return databases_location

    def _merge(self, databases_location: List[str]):
        """Merges all the session store databases stored at the specified locations into the user's local session_store.db

        Notes:
        - This method uses multiple SQLAlchemy engines to connect to the user's session_store.db and to all the other downloaded dbs.
        - It is assumed that all the databases share the same schema.
        - In the version 1.0 - we only merge the runs table which contains all the experiments.
        - The downloaded database files are deleted after it's runs are merged with the user's local session_store.db

        Args:
            database_location:  A list of local filepath in string format for all the databases

        """

        # Connect to the user's local session_store.db
        engine, session_class = create_db_engine(self.location)
        Base.metadata.create_all(bind=engine)
        database = next(get_db(session_class))

        temp_engine = None
        # Iterate through each downloaded database
        for db_loc in databases_location:
            if temp_engine:
                temp_engine.dispose()
            # Open a connection to the downloaded database
            temp_engine = create_engine(f"sqlite:///{db_loc}")
            with temp_engine.connect() as database_conn:
                db_metadata = MetaData()
                db_metadata.reflect(bind=temp_engine)
                # Merge data from the 'runs' table
                all_runs_data = []
                for table_name, table_obj in db_metadata.tables.items():
                    if table_name == "runs":
                        data = database_conn.execute(table_obj.select()).fetchall()
                        for row in data:
                            all_runs_data.append((row._asdict()))
                for run in all_runs_data:
                    try:
                        session_store_data = RunModel(**run)
                        database.add(session_store_data)
                        database.commit()
                    except Exception as e:
                        database.rollback()
                        logging.exception(f"Failed to add runs: {e}")
            # Close the connection to the downloaded database and delete it
            temp_engine.dispose()
            os.remove(db_loc)

    def sync(self):
        """
        Synchronizes the user's local session_store.db with remote session_store.db stored on a cloud storage service.

        Notes:
        - First, all the database files at the remote location are downloaded to the local project.
        - Next, the downloaded databases are merged into the user's local session_store.db.
        - Finally, the user's local session_store.db is uploaded to the remote location to ensure that it has the most up-to-date runs.
        """

        if self.remote_location:
            downloaded_dbs = self._download()
            self._merge(downloaded_dbs)
            self._upload()

# TODO: refactor if remote_location, error catching into decorator?
# Don't want broken sync to stop kedro-viz.

# Notes:
# --autoreload should work still, so long as change local file