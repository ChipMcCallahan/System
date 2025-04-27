import json
import mysql.connector
from mysql.connector import MySQLConnection
from typing import Optional, List
from src.dao.system_node import SystemNode


class SystemNodeDAO:
    def __init__(self, db_config: dict):
        """
        db_config is a dict like:
        {
            'host': 'YOUR_DB_HOST',
            'user': 'YOUR_DB_USER',
            'password': 'YOUR_DB_PASSWORD',
            'database': 'jbone-system-db'
        }
        """
        self.db_config = db_config

    def _get_connection(self) -> MySQLConnection:
        return mysql.connector.connect(**self.db_config)

    # -----------------------------------------------------------
    # 1) CREATE
    # -----------------------------------------------------------
    def create(self, node: SystemNode) -> int:
        """
        Inserts a new row into SystemNode.
        Places it at the end of siblings by setting SortOrder = max sibling's SortOrder + 1.
        Returns the newly generated ID.
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()

            # 1) Determine next SortOrder for the parent's children
            sql_max = """
                SELECT COALESCE(MAX(SortOrder), 0) + 1
                FROM SystemNode
                WHERE ParentID <=> %s
            """
            cursor.execute(sql_max, (node.ParentID,))
            (new_sort_order,) = cursor.fetchone() or (1,)

            # 2) Insert the row
            sql_insert = """
                INSERT INTO SystemNode (
                    ParentID, Name, Description, Notes,
                    Tags, Metadata, Status, Importance, SortOrder
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql_insert, (
                node.ParentID,
                node.Name,
                node.Description,
                node.Notes,
                json.dumps(node.Tags) if node.Tags else None,
                json.dumps(node.Metadata) if node.Metadata else None,
                node.Status,
                node.Importance,
                new_sort_order
            ))
            conn.commit()
            new_id = cursor.lastrowid

            cursor.close()
            return new_id
        finally:
            conn.close()

    # -----------------------------------------------------------
    # 2) READ (Single / All)
    # -----------------------------------------------------------
    def read(self, node_id: int) -> Optional[SystemNode]:
        """
        Fetch a single row by ID. Returns a SystemNode or None if not found.
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            sql = """
                SELECT
                    ID, ParentID, Name, Description, Notes,
                    Tags, Metadata, Status, Importance, SortOrder
                FROM SystemNode
                WHERE ID = %s
            """
            cursor.execute(sql, (node_id,))
            row = cursor.fetchone()
            cursor.close()

            if not row:
                return None

            return SystemNode(
                ID=row["ID"],
                ParentID=row["ParentID"],
                Name=row["Name"],
                Description=row["Description"],
                Notes=row["Notes"],
                Tags=json.loads(row["Tags"]) if row["Tags"] else {},
                Metadata=json.loads(row["Metadata"]) if row["Metadata"] else {},
                Status=row["Status"],
                Importance=row["Importance"],
                SortOrder=row["SortOrder"]
            )
        finally:
            conn.close()

    def read_by_parent(self, parent_id: Optional[int]) -> list[SystemNode]:
        """
        Return all nodes whose ParentID == parent_id (null or not),
        ordered by SortOrder.
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            sql = """
                SELECT
                    ID, ParentID, Name, Description, Notes,
                    Tags, Metadata, Status, Importance, SortOrder
                FROM SystemNode
                WHERE ParentID <=> %s
                ORDER BY SortOrder
            """
            cursor.execute(sql, (parent_id,))
            rows = cursor.fetchall()
            cursor.close()

            results = []
            for row in rows:
                results.append(SystemNode(
                    ID=row["ID"],
                    ParentID=row["ParentID"],
                    Name=row["Name"],
                    Description=row["Description"],
                    Notes=row["Notes"],
                    Tags=json.loads(row["Tags"]) if row["Tags"] else {},
                    Metadata=json.loads(row["Metadata"]) if row["Metadata"] else {},
                    Status=row["Status"],
                    Importance=row["Importance"],
                    SortOrder=row["SortOrder"]
                ))
            return results
        finally:
            conn.close()

    def read_all(self) -> List[SystemNode]:
        """
        Fetch all rows from SystemNode. Returns a list of SystemNode objects.
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            sql = """
                SELECT
                    ID, ParentID, Name, Description, Notes,
                    Tags, Metadata, Status, Importance, SortOrder
                FROM SystemNode
                ORDER BY ParentID, SortOrder  -- optional
            """
            cursor.execute(sql)
            rows = cursor.fetchall()
            cursor.close()

            nodes = []
            for row in rows:
                node = SystemNode(
                    ID=row["ID"],
                    ParentID=row["ParentID"],
                    Name=row["Name"],
                    Description=row["Description"],
                    Notes=row["Notes"],
                    Tags=json.loads(row["Tags"]) if row["Tags"] else {},
                    Metadata=json.loads(row["Metadata"]) if row["Metadata"] else {},
                    Status=row["Status"],
                    Importance=row["Importance"],
                    SortOrder=row["SortOrder"]
                )
                nodes.append(node)

            return nodes
        finally:
            conn.close()

    # -----------------------------------------------------------
    # 3) UPDATE (Looser Concurrency)
    # -----------------------------------------------------------
    def update(self, old: SystemNode, new: SystemNode) -> bool:
        """
        Update a row only if the existing DB record still matches old.ID, old.ParentID,
        old.Status, and old.Importance (not checking SortOrder or Name, etc.).
        Returns True if exactly one row was updated, False otherwise.
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            sql = """
            UPDATE SystemNode
            SET
                ParentID = %s,
                Name = %s,
                Description = %s,
                Notes = %s,
                Tags = %s,
                Metadata = %s,
                Status = %s,
                Importance = %s,
                SortOrder = %s
            WHERE
                ID = %s
                AND ParentID <=> %s
                AND Status <=> %s
                AND Importance = %s
            """
            # The SET uses the new node's data
            set_params = (
                new.ParentID,
                new.Name,
                new.Description,
                new.Notes,
                json.dumps(new.Tags) if new.Tags else None,
                json.dumps(new.Metadata) if new.Metadata else None,
                new.Status,
                new.Importance,
                new.SortOrder
            )
            # The WHERE uses old node's ID, ParentID, Status, Importance
            where_params = (
                old.ID,
                old.ParentID,
                old.Status,
                old.Importance
            )

            cursor.execute(sql, set_params + where_params)
            conn.commit()
            updated_count = cursor.rowcount
            cursor.close()
            return updated_count == 1
        finally:
            conn.close()

    # -----------------------------------------------------------
    # 4) DELETE (Looser Concurrency)
    # -----------------------------------------------------------
    def delete(self, old: SystemNode) -> bool:
        """
        Delete a row only if the existing DB record still matches old.ID, old.ParentID,
        old.Status, and old.Importance. We ignore SortOrder concurrency checks here.
        Returns True if exactly one row was deleted, False otherwise.
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            sql = """
            DELETE FROM SystemNode
            WHERE
                ID = %s
                AND ParentID <=> %s
                AND Status <=> %s
                AND Importance = %s
            """
            params = (
                old.ID,
                old.ParentID,
                old.Status,
                old.Importance
            )
            cursor.execute(sql, params)
            conn.commit()
            deleted_count = cursor.rowcount
            cursor.close()
            return deleted_count == 1
        finally:
            conn.close()

    # -----------------------------------------------------------
    # 5) MOVE & REORDER
    # -----------------------------------------------------------
    def move_node(self, node_id: int, new_parent_id: Optional[int], target_index: Optional[int] = None) -> bool:
        """
        Move or reorder a node:
          - If 'target_index' is specified, place the node at that SortOrder among siblings.
          - If no 'target_index', place it at the end (max SortOrder + 1).
          - Also handle removing the node from its old parent's "list" if parent changed,
            and shifting sibling SortOrders if within same parent.

        Returns True if exactly one row was updated, False otherwise.
        """
        conn = self._get_connection()
        try:
            conn.start_transaction()
            cursor = conn.cursor(dictionary=True)

            # 1) Read the current node info
            cursor.execute("SELECT ParentID, SortOrder FROM SystemNode WHERE ID = %s", (node_id,))
            old_row = cursor.fetchone()
            if not old_row:
                conn.rollback()
                cursor.close()
                return False

            old_parent = old_row["ParentID"]
            old_sort_order = old_row["SortOrder"]

            # If the parent isn't changing but we do have a target_index => reorder within the same parent
            # If the parent is changing we do two steps: remove from old parent's list & insert into new parent's list.

            # 2) If we are *changing* parents, close gap in the old parent's SortOrder
            if old_parent != new_parent_id:
                # Shift siblings after old_sort_order down by 1
                shift_old_parent_sql = """
                    UPDATE SystemNode
                    SET SortOrder = SortOrder - 1
                    WHERE ParentID <=> %s
                      AND SortOrder > %s
                """
                cursor.execute(shift_old_parent_sql, (old_parent, old_sort_order))

            # 3) Determine the actual target_index (SortOrder) in the new parent's list
            if target_index is not None:
                # Shift siblings >= target_index up by 1
                shift_new_parent_sql = """
                    UPDATE SystemNode
                    SET SortOrder = SortOrder + 1
                    WHERE ParentID <=> %s
                      AND SortOrder >= %s
                """
                cursor.execute(shift_new_parent_sql, (new_parent_id, target_index))
                new_sort_order = target_index
            else:
                # Place at the end if no target_index
                sql_max = """
                    SELECT COALESCE(MAX(SortOrder), 0) + 1 AS next_pos
                    FROM SystemNode
                    WHERE ParentID <=> %s
                """
                cursor.execute(sql_max, (new_parent_id,))
                row = cursor.fetchone()
                new_sort_order = row["next_pos"] if row else 1

            # 4) Update the node to the new parent + new_sort_order
            update_sql = """
                UPDATE SystemNode
                SET ParentID = %s, SortOrder = %s
                WHERE ID = %s
            """
            cursor.execute(update_sql, (new_parent_id, new_sort_order, node_id))
            updated_count = cursor.rowcount

            conn.commit()
            cursor.close()
            return updated_count == 1

        except:  # noqa
            conn.rollback()
            raise
        finally:
            conn.close()
