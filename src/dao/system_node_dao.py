import json
import mysql.connector
from mysql.connector import MySQLConnection
from typing import Optional
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

    def create(self, node: SystemNode) -> int:
        """
        Inserts a new row into SystemNode.
        Returns the newly generated ID.
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            sql = """
                INSERT INTO SystemNode (
                    ParentID, Name, Description, Notes,
                    Tags, Metadata, Status, Importance
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (
                node.ParentID,
                node.Name,
                node.Description,
                node.Notes,
                json.dumps(node.Tags) if node.Tags else None,
                json.dumps(node.Metadata) if node.Metadata else None,
                node.Status,
                node.Importance
            ))
            conn.commit()
            new_id = cursor.lastrowid
            cursor.close()
            return new_id
        finally:
            conn.close()

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
                    Tags, Metadata, Status, Importance
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
                Importance=row["Importance"]
            )
        finally:
            conn.close()

    def update(self, old: SystemNode, new: SystemNode) -> bool:
        """
        Update a row only if the existing DB record matches the 'old' object.
        This approach helps ensure no one changed it between read & update.
        Returns True if exactly one row was updated, False otherwise.
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            # We'll compare all non-null fields from 'old'
            # For example, if old.Notes is None, we won't include it in the WHERE.
            # But for simplicity here, let's compare *everything* including None.
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
                Importance = %s
            WHERE
                ID = %s
                AND ParentID <=> %s
                AND Name = %s
                AND Description <=> %s
                AND Notes <=> %s
                AND Tags <=> %s
                AND Metadata <=> %s
                AND Status <=> %s
                AND Importance = %s
            """

            # <=> is MySQL's null-safe equality operator (so NULL <=> NULL is true)
            # We'll bind parameters in pairs for the SET (new) and the WHERE (old)
            set_params = (
                new.ParentID,
                new.Name,
                new.Description,
                new.Notes,
                json.dumps(new.Tags) if new.Tags else None,
                json.dumps(new.Metadata) if new.Metadata else None,
                new.Status,
                new.Importance
            )
            where_params = (
                old.ID,
                old.ParentID,
                old.Name,
                old.Description,
                old.Notes,
                json.dumps(old.Tags) if old.Tags else None,
                json.dumps(old.Metadata) if old.Metadata else None,
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

    def delete(self, old: SystemNode) -> bool:
        """
        Delete a row only if it matches the 'old' object in all fields.
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
                AND Name = %s
                AND Description <=> %s
                AND Notes <=> %s
                AND Tags <=> %s
                AND Metadata <=> %s
                AND Status <=> %s
                AND Importance = %s
            """
            params = (
                old.ID,
                old.ParentID,
                old.Name,
                old.Description,
                old.Notes,
                json.dumps(old.Tags) if old.Tags else None,
                json.dumps(old.Metadata) if old.Metadata else None,
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

    def move_node(self, node_id: int, new_parent_id: Optional[int]) -> bool:
        """
        Update just the ParentID for a node, ignoring concurrency checks on other fields.
        (If you do want concurrency checks, you'd do a read->update as in the update() method.)
        Returns True if exactly one row was updated, False otherwise.
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            sql = """
                UPDATE SystemNode
                SET ParentID = %s
                WHERE ID = %s
            """
            cursor.execute(sql, (new_parent_id, node_id))
            conn.commit()
            updated_count = cursor.rowcount
            cursor.close()
            return updated_count == 1
        finally:
            conn.close()
