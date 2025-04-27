import unittest
from unittest.mock import patch, MagicMock

# Adjust these imports to match your actual paths
from src.dao.system_node_dao import SystemNodeDAO
from src.dao.system_node import SystemNode


def normalize_sql(sql: str) -> str:
    """
    Helper to normalize SQL by removing extra newlines/tabs
    so we can use substring checks reliably.
    """
    return " ".join(sql.split()).lower()


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

    # ------------------------------------------------------------------
    # CREATE
    # ------------------------------------------------------------------
    @patch("src.dao.system_node_dao.mysql.connector.connect")
    def test_create_node(self, mock_connect: MagicMock) -> None:
        """
        Test that create() executes the correct SQL with the correct parameters,
        and returns the lastrowid.
        """
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # The first SELECT (max SortOrder) returns (1,) meaning next order is 1
        mock_cursor.fetchone.return_value = (1,)
        # After that we do the INSERT. lastrowid = 123
        mock_cursor.lastrowid = 123

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
        self.assertEqual(new_id, 123)

        # We expect a query for max SortOrder, then an INSERT
        calls = mock_cursor.execute.call_args_list
        self.assertGreaterEqual(len(calls), 2, "Expected at least two SQL calls (max SortOrder, then INSERT).")

        # 1) check the SELECT call
        sql_1, params_1 = calls[0][0]
        norm_1 = normalize_sql(sql_1)
        self.assertIn("select coalesce(max(sortorder), 0) + 1", norm_1)
        self.assertIn("where parentid <=> %s", norm_1)
        self.assertEqual(params_1, (None,))

        # 2) check the INSERT call
        sql_2, params_2 = calls[1][0]
        norm_2 = normalize_sql(sql_2)
        self.assertIn("insert into systemnode", norm_2)
        self.assertEqual(
            params_2,
            (
                node.ParentID,
                node.Name,
                node.Description,
                node.Notes,
                '{"type": "mocked"}',
                '{"foo": "bar"}',
                node.Status,
                node.Importance,
                1  # from the SELECT above
            )
        )

        mock_conn.commit.assert_called_once()

    # ------------------------------------------------------------------
    # READ a Single Node
    # ------------------------------------------------------------------
    @patch("src.dao.system_node_dao.mysql.connector.connect")
    def test_read_node(self, mock_connect: MagicMock) -> None:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        mock_cursor.fetchone.return_value = {
            "ID": 101,
            "ParentID": None,
            "Name": "MockedName",
            "Description": "MockedDesc",
            "Notes": "SomeNotes",
            "Tags": '{"key": "value"}',
            "Metadata": '{"meta": 123}',
            "Status": "Active",
            "Importance": 2,
            "SortOrder": 10
        }

        node = self.dao.read(101)
        self.assertIsNotNone(node)
        self.assertEqual(node.ID, 101)
        self.assertEqual(node.Name, "MockedName")
        self.assertEqual(node.SortOrder, 10)

        sql_called, params_called = mock_cursor.execute.call_args[0]
        norm_sql = normalize_sql(sql_called)
        self.assertIn("select", norm_sql)
        self.assertIn("from systemnode", norm_sql)
        self.assertEqual(params_called, (101,))

        mock_conn.close.assert_called_once()

    # ------------------------------------------------------------------
    # READ BY PARENT
    # ------------------------------------------------------------------
    @patch("src.dao.system_node_dao.mysql.connector.connect")
    def test_read_by_parent(self, mock_connect: MagicMock) -> None:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        mock_cursor.fetchall.return_value = [
            {
                "ID": 1,
                "ParentID": None,
                "Name": "Root1",
                "Description": None,
                "Notes": None,
                "Tags": None,
                "Metadata": None,
                "Status": None,
                "Importance": 0,
                "SortOrder": 1
            },
            {
                "ID": 2,
                "ParentID": None,
                "Name": "Root2",
                "Description": None,
                "Notes": None,
                "Tags": None,
                "Metadata": None,
                "Status": None,
                "Importance": 0,
                "SortOrder": 2
            }
        ]

        results = self.dao.read_by_parent(None)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].ID, 1)
        self.assertEqual(results[1].ID, 2)
        self.assertEqual(results[0].SortOrder, 1)
        self.assertEqual(results[1].SortOrder, 2)

        sql_called, params_called = mock_cursor.execute.call_args[0]
        norm_sql = normalize_sql(sql_called)
        self.assertIn("where parentid <=> %s", norm_sql)
        self.assertIn("order by sortorder", norm_sql)
        self.assertEqual(params_called, (None,))
        mock_conn.close.assert_called_once()

    # ------------------------------------------------------------------
    # READ ALL
    # ------------------------------------------------------------------
    @patch("src.dao.system_node_dao.mysql.connector.connect")
    def test_read_all_nodes(self, mock_connect: MagicMock) -> None:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        mock_cursor.fetchall.return_value = [
            {
                "ID": 1,
                "ParentID": None,
                "Name": "RootNode",
                "Description": None,
                "Notes": None,
                "Tags": '{"k1":"v1"}',
                "Metadata": '{}',
                "Status": None,
                "Importance": 0,
                "SortOrder": 1
            },
            {
                "ID": 2,
                "ParentID": 1,
                "Name": "ChildNode",
                "Description": "desc",
                "Notes": "notes",
                "Tags": '{"child":"yes"}',
                "Metadata": '{"extra":42}',
                "Status": "Active",
                "Importance": 2,
                "SortOrder": 5
            }
        ]

        all_nodes = self.dao.read_all()
        self.assertEqual(len(all_nodes), 2)
        self.assertEqual(all_nodes[0].ID, 1)
        self.assertEqual(all_nodes[1].ID, 2)

        sql_called = mock_cursor.execute.call_args[0][0]
        norm_sql = normalize_sql(sql_called)
        self.assertIn("select", norm_sql)
        self.assertIn("from systemnode", norm_sql)
        self.assertIn("order by parentid, sortorder", norm_sql)

    # ------------------------------------------------------------------
    # UPDATE
    # ------------------------------------------------------------------
    @patch("src.dao.system_node_dao.mysql.connector.connect")
    def test_update_node(self, mock_connect: MagicMock) -> None:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
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
            Importance=0,
            SortOrder=0
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
            Importance=2,
            SortOrder=7
        )

        success = self.dao.update(old_node, new_node)
        self.assertTrue(success)

        # Check SQL
        sql_called, params_called = mock_cursor.execute.call_args[0]
        norm_sql = normalize_sql(sql_called)
        self.assertIn("update systemnode", norm_sql)
        self.assertIn("set parentid = %s", norm_sql)
        self.assertIn("sortorder = %s", norm_sql)
        self.assertIn("where id = %s", norm_sql)
        self.assertIn("and parentid <=> %s", norm_sql)

        # 9 SET fields + 4 WHERE = 13
        self.assertEqual(len(params_called), 13)

        mock_conn.commit.assert_called_once()

    # ------------------------------------------------------------------
    # DELETE
    # ------------------------------------------------------------------
    @patch("src.dao.system_node_dao.mysql.connector.connect")
    def test_delete_node(self, mock_connect: MagicMock) -> None:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
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
            Importance=1,
            SortOrder=2
        )

        deleted = self.dao.delete(old_node)
        self.assertTrue(deleted)

        sql_called, params_called = mock_cursor.execute.call_args[0]
        norm_sql = normalize_sql(sql_called)
        self.assertIn("delete from systemnode", norm_sql)
        self.assertIn("where id = %s", norm_sql)

        # 4 where params: ID, ParentID, Status, Importance
        self.assertEqual(len(params_called), 4)
        mock_conn.commit.assert_called_once()

    # ------------------------------------------------------------------
    # MOVE NODE - simple
    # ------------------------------------------------------------------
    @patch("src.dao.system_node_dao.mysql.connector.connect")
    def test_move_node_simple(self, mock_connect: MagicMock) -> None:
        """
        Move with no target_index => place at end (max SortOrder + 1).
        """
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # Step 1: read old parent's ParentID, SortOrder => (None, 2)
        # Step 2: SHIFT old parent's siblings if parent changed
        # Step 3: read new parent's max sort => 5
        # Step 4: update node => rowcount=1
        mock_cursor.fetchone.side_effect = [
            {"ParentID": None, "SortOrder": 2},   # read old row
            {"next_pos": 5}                       # new parent's next order
        ]
        mock_cursor.rowcount = 1

        success = self.dao.move_node(400, 999, None)
        self.assertTrue(success)

        calls = mock_cursor.execute.call_args_list
        self.assertEqual(len(calls), 4, "Should have 4 queries total.")

        sql1, param1 = calls[0][0]
        norm1 = normalize_sql(sql1)
        self.assertIn("select parentid, sortorder from systemnode", norm1)
        self.assertEqual(param1, (400,))

        sql2, param2 = calls[1][0]
        norm2 = normalize_sql(sql2)
        self.assertIn("set sortorder = sortorder - 1", norm2)
        self.assertEqual(param2, (None, 2))

        sql3, param3 = calls[2][0]
        norm3 = normalize_sql(sql3)
        self.assertIn("select coalesce(max(sortorder), 0) + 1 as next_pos", norm3)
        self.assertEqual(param3, (999,))

        sql4, param4 = calls[3][0]
        norm4 = normalize_sql(sql4)
        self.assertIn("update systemnode set parentid = %s, sortorder = %s", norm4)
        self.assertEqual(param4, (999, 5, 400))

        mock_conn.commit.assert_called_once()

    # ------------------------------------------------------------------
    # MOVE NODE - reorder in same parent
    # ------------------------------------------------------------------
    @patch("src.dao.system_node_dao.mysql.connector.connect")
    def test_move_node_reorder_same_parent(self, mock_connect: MagicMock) -> None:
        """
        Reordering within the same parent => no gap close, just shift >= target_index.
        """
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # old parent=10, old_sort_order=3, new_parent=10, target_index=1
        mock_cursor.fetchone.return_value = {"ParentID": 10, "SortOrder": 3}
        mock_cursor.rowcount = 1

        success = self.dao.move_node(500, 10, 1)
        self.assertTrue(success)

        calls = mock_cursor.execute.call_args_list
        self.assertEqual(len(calls), 3, "3 queries: read old row, shift siblings, update node")

        sql1, param1 = calls[0][0]
        norm1 = normalize_sql(sql1)
        self.assertIn("select parentid, sortorder from systemnode where id = %s", norm1)
        self.assertEqual(param1, (500,))

        sql2, param2 = calls[1][0]
        norm2 = normalize_sql(sql2)
        self.assertIn("set sortorder = sortorder + 1", norm2)
        self.assertIn("where parentid <=> %s and sortorder >= %s", norm2)
        self.assertEqual(param2, (10, 1))

        sql3, param3 = calls[2][0]
        norm3 = normalize_sql(sql3)
        self.assertIn("update systemnode set parentid = %s, sortorder = %s", norm3)
        self.assertEqual(param3, (10, 1, 500))

        mock_conn.commit.assert_called_once()


if __name__ == "__main__":
    unittest.main()
