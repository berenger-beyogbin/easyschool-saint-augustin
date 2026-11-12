from psycopg2 import OperationalError

from scripts import db_connection_test


class _Cursor:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def execute(self, query):
        assert query.startswith("SELECT current_database()")

    def fetchone(self):
        return "easy_school_cjga_db", "easy_school_app", "PostgreSQL 18.4 on x86_64"


class _Connection:
    def cursor(self):
        return _Cursor()

    def close(self):
        pass


def _write_config(path):
    path.write_text(
        "host=172.22.50.10\n"
        "port=5432\n"
        "dbname=easy_school_cjga_db\n"
        "user=easy_school_app\n"
        "password=secret=avec=egal\n",
        encoding="utf-8",
    )


def test_connection_success(monkeypatch, tmp_path):
    config = tmp_path / "connection.ini"
    result = tmp_path / "result.txt"
    _write_config(config)
    monkeypatch.setattr(db_connection_test.psycopg2, "connect", lambda **kwargs: _Connection())
    monkeypatch.setattr(db_connection_test.sys, "argv", ["tool", str(config), str(result)])

    assert db_connection_test.main() == 0
    assert "Connexion réussie" in result.read_text(encoding="cp1252")


def test_connection_timeout_is_explained(monkeypatch, tmp_path):
    config = tmp_path / "connection.ini"
    result = tmp_path / "result.txt"
    _write_config(config)

    def fail(**kwargs):
        raise OperationalError("connection timed out")

    monkeypatch.setattr(db_connection_test.psycopg2, "connect", fail)
    monkeypatch.setattr(db_connection_test.sys, "argv", ["tool", str(config), str(result)])

    assert db_connection_test.main() == 3
    assert "172.22.50.10:5432" in result.read_text(encoding="cp1252")
