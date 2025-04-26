# python -m unittest
# flake8 .

import unittest
from unittest.mock import patch, MagicMock

# Adjust these imports if your actual module paths differ
from src.dao.system_node_dao import SystemNodeDAO
from src.dao.system_node import SystemNode


class TestSystemNodeDAO(unittest.TestCase):
    """
    Pure unit tests for SystemNodeDAO, using mocks
    so we do not connect to a real MySQL database.
    """

    def setUp(self) -> None:
        """
        Create the DAO. We'll mock out the DB connection in each test using patch.
        """
        self.db_config = {
            "host": "fake_host",
            "user": "fake_user",
            "password": "fake_pass",
            "database": "fake_db"
        }
        self.dao = SystemNodeDAO(self.db_config)

    @patch("src.dao.system_node_dao.mysql.connector.connect")
    def test_create_node(self, mock_connect: MagicMock) -> None:
        """
        Test that create() executes the correct SQL with the correct parameters,
        and returns the lastrowid.
        """
        # Mock connection and cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # Simulate a DB insertion returning lastrowid = 123
        mock_cursor.lastrowid = 123

        # Prepare a sample node to insert
        node = SystemNode(
            ParentID=None,
            Name="UnitTest Node",
            Description="Some description",
            Notes="Some notes",
            Tags={"type": "mocked"},
            Metadata={"foo": "bar"},
            Status="Active",
            Importance=2
        )

        new_id = self.dao.create(node)

        # Assertions on lastrowid
        self.assertEqual(new_id, 123, "create() should return the cursor's lastrowid")

        # Check that 'connect' was called once with our db_config
        mock_connect.assert_called_once_with(**self.db_config)

        # Verify the SQL statement and parameters
        mock_cursor.execute.assert_called_once()
        sql_called, params_called = mock_cursor.execute.call_args[0]
        self.assertIn("INSERT INTO SystemNode", sql_called, "SQL should be an INSERT statement.")
        self.assertEqual(
            params_called,
            (
                node.ParentID,
                node.Name,
                node.Description,
                node.Notes,
                '{"type": "mocked"}',   # json.dumps(node.Tags)
                '{"foo": "bar"}',      # json.dumps(node.Metadata)
                node.Status,
                node.Importance
            ),
            "Parameters for the INSERT should match the node's fields."
        )
        mock_conn.commit.assert_called_once()

    @patch("src.dao.system_node_dao.mysql.connector.connect")
    def test_read_node(self, mock_connect: MagicMock) -> None:
        """
        Test that read() executes the correct SELECT and returns a SystemNode object.
        """
        # Mock connection
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # Simulate DB row for ID=101
        mock_cursor.fetchone.return_value = {
            "ID": 101,
            "ParentID": None,
            "Name": "MockedName",
            "Description": "MockedDesc",
            "Notes": "SomeNotes",
            "Tags": '{"key": "value"}',
            "Metadata": '{"meta": 123}',
            "Status": "Active",
            "Importance": 2
        }

        result_node = self.dao.read(101)
        self.assertIsNotNone(result_node, "read() should return a SystemNode, not None")

        # Check the fields on the returned node
        self.assertEqual(result_node.ID, 101)
        self.assertEqual(result_node.Name, "MockedName")
        self.assertEqual(result_node.Tags, {"key": "value"})
        self.assertEqual(result_node.Metadata, {"meta": 123})
        self.assertEqual(result_node.Importance, 2)

        # Check SQL
        mock_cursor.execute.assert_called_once()
        sql_called, params_called = mock_cursor.execute.call_args[0]
        self.assertIn("SELECT", sql_called, "SQL should be a SELECT statement")
        self.assertIn("FROM SystemNode", sql_called)
        self.assertEqual(params_called, (101,), "Should SELECT by ID=101")
        mock_conn.close.assert_called_once()

    @patch("src.dao.system_node_dao.mysql.connector.connect")
    def test_update_node(self, mock_connect: MagicMock) -> None:
        """
        Test that update(old, new) constructs the correct SQL and returns True if rowcount=1.
        """
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # Simulate rowcount=1 for a successful update
        mock_cursor.rowcount = 1

        old_node = SystemNode(
            ID=200,
            ParentID=None,
            Name="OldName",
            Description=None,
            Notes=None,
            Tags={},
            Metadata={},
            Status=None,
            Importance=0
        )

        new_node = SystemNode(
            ID=200,
            ParentID=10,
            Name="NewName",
            Description="NewDesc",
            Notes="NewNotes",
            Tags={"new": "tag"},
            Metadata={"version": 1},
            Status="Updated",
            Importance=2
        )

        success = self.dao.update(old_node, new_node)
        self.assertTrue(success, "update() should return True if rowcount=1")

        # Verify SQL
        mock_cursor.execute.assert_called_once()
        sql_called, params_called = mock_cursor.execute.call_args[0]
        self.assertIn("UPDATE SystemNode", sql_called)
        normalized_sql = " ".join(sql_called.split())
        self.assertIn("WHERE ID = %s", normalized_sql)
        # The WHERE clause includes <=> for null-safe comparison
        # We won't check every substring, but you could.

        # Check the parameter tuple: 8 for the SET, plus 9 in the WHERE = 17 total
        self.assertEqual(len(params_called), 17, "Should have 17 parameters in total.")
        # Checking a few of them:
        self.assertEqual(params_called[0], new_node.ParentID)
        self.assertEqual(params_called[1], new_node.Name)
        self.assertEqual(params_called[7], new_node.Importance)
        # WHERE side
        self.assertEqual(params_called[8], old_node.ID)
        self.assertEqual(params_called[9], old_node.ParentID)

        # We can confirm the JSON strings for the tags/metadata:
        self.assertEqual(params_called[4], '{"new": "tag"}')
        self.assertEqual(params_called[5], '{"version": 1}')

        mock_conn.commit.assert_called_once()

    @patch("src.dao.system_node_dao.mysql.connector.connect")
    def test_delete_node(self, mock_connect: MagicMock) -> None:
        """
        Test that delete(old) constructs the correct DELETE statement and returns True if rowcount=1.
        """
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # Simulate rowcount=1 for successful delete
        mock_cursor.rowcount = 1

        old_node = SystemNode(
            ID=300,
            ParentID=1,
            Name="Deletable",
            Description="OldDesc",
            Notes="OldNotes",
            Tags={"delete": True},
            Metadata={"key": "val"},
            Status="Active",
            Importance=1
        )

        deleted = self.dao.delete(old_node)
        self.assertTrue(deleted, "delete() should return True if exactly one row was deleted")

        mock_cursor.execute.assert_called_once()
        sql_called, params_called = mock_cursor.execute.call_args[0]
        self.assertIn("DELETE FROM SystemNode", sql_called)
        normalized_sql = " ".join(sql_called.split())
        self.assertIn("WHERE ID = %s", normalized_sql)
        self.assertEqual(len(params_called), 9, "DELETE uses 9 parameters for the WHERE condition")

        self.assertEqual(params_called[0], old_node.ID)
        self.assertEqual(params_called[1], old_node.ParentID)
        self.assertEqual(params_called[2], old_node.Name)
        self.assertEqual(params_called[3], old_node.Description)
        # ...
        self.assertEqual(params_called[5], '{"delete": true}')  # JSON for Tags
        self.assertEqual(params_called[6], '{"key": "val"}')    # JSON for Metadata

        mock_conn.commit.assert_called_once()

    @patch("src.dao.system_node_dao.mysql.connector.connect")
    def test_move_node(self, mock_connect: MagicMock) -> None:
        """
        Test that move_node() only updates the ParentID and returns True if rowcount=1.
        """
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # Simulate successful update
        mock_cursor.rowcount = 1

        node_id = 400
        new_parent_id = 999

        result = self.dao.move_node(node_id, new_parent_id)
        self.assertTrue(result, "move_node() should return True if rowcount=1")

        mock_cursor.execute.assert_called_once()
        sql_called, params_called = mock_cursor.execute.call_args[0]
        self.assertIn("UPDATE SystemNode", sql_called)
        self.assertIn("SET ParentID = %s", sql_called)
        self.assertIn("WHERE ID = %s", sql_called)
        self.assertEqual(params_called, (new_parent_id, node_id),
                         "Should update the row with the correct parent and ID")

        mock_conn.commit.assert_called_once()


if __name__ == "__main__":
    unittest.main()
