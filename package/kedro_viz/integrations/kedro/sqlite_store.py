"""kedro_viz.intergrations.kedro.sqlite_store is a child of BaseSessionStore
which stores sessions data in the SQLite database"""

import json
import logging
import s3fs
from pathlib import Path
from typing import Any, Generator

from kedro.framework.session.store import BaseSessionStore
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


def _is_json_serializable(obj: Any):
    try:
        json.dumps(obj)
        return True
    except (TypeError, OverflowError):
        return False


class SQLiteStore(BaseSessionStore):
    """Stores the session data on the sqlite db."""

    @property
    def location(self) -> Path:
        """Returns location of the sqlite_store database"""
        return Path(self._path) / "session_store.db"
    
    @property
    def s3_location(self) -> Path:
        """Returns location of the sqlite_store database"""
        return self._s3_path

    def to_json(self) -> str:
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
        """Save the session store info on db ."""
        engine, session_class = create_db_engine(self.location)
        Base.metadata.create_all(bind=engine)
        database = next(get_db(session_class))
        session_store_data = RunModel(id=self._session_id, blob=self.to_json())
        database.add(session_store_data)
        database.commit()
        if(self._s3_path):
            s3 = s3fs.S3FileSystem()
            with open(self.location,'rb') as file:
                 with s3.open(f'{self._s3_path}/example2.db', 'wb') as s3f:
                         s3f.write(file.read())

