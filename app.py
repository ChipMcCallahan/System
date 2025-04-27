import os

from flask import Flask, request, jsonify
from src.dao.system_node_dao import SystemNodeDAO
from src.dao.system_node import SystemNode

app = Flask(__name__)

# Load DB configuration from environment variables or defaults
db_config = {
    "host": os.getenv("DB_HOST", "127.0.0.1"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "jbone-system-db")
}

dao = SystemNodeDAO(db_config)


@app.route("/")
def home():
    return "Welcome to the SystemNode Flask API!"


# -----------------------------------------------------------
# 1) CREATE - POST /nodes
# -----------------------------------------------------------
@app.route("/nodes", methods=["POST"])
def create_node():
    """
    Create a new SystemNode and place it at the end of its siblings (SortOrder).
    JSON body example:
    {
      "Name": "My Node",
      "ParentID": 123,
      "Description": "...",
      "Notes": "...",
      "Tags": { ... },
      "Metadata": { ... },
      "Status": "Active",
      "Importance": 2
    }
    """
    try:
        data = request.json
        if not data or "Name" not in data:
            return jsonify({"error": "Missing 'Name' in JSON body"}), 400

        node = SystemNode(
            ParentID=data.get("ParentID"),
            Name=data["Name"],
            Description=data.get("Description"),
            Notes=data.get("Notes"),
            Tags=data.get("Tags", {}),
            Metadata=data.get("Metadata", {}),
            Status=data.get("Status"),
            Importance=data.get("Importance", 0)
        )

        new_id = dao.create(node)
        return jsonify({"message": "Node created", "ID": new_id}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# -----------------------------------------------------------
# 2) READ - GET /nodes/<id> or GET /nodes?parent=<pid>
# -----------------------------------------------------------
@app.route("/nodes/<int:node_id>", methods=["GET"])
def get_node(node_id):
    """
    Fetch a single node by ID.
    GET /nodes/123
    """
    try:
        node = dao.read(node_id)
        if node is None:
            return jsonify({"error": "Node not found"}), 404

        return jsonify({
            "ID": node.ID,
            "ParentID": node.ParentID,
            "Name": node.Name,
            "Description": node.Description,
            "Notes": node.Notes,
            "Tags": node.Tags,
            "Metadata": node.Metadata,
            "Status": node.Status,
            "Importance": node.Importance,
            "SortOrder": node.SortOrder
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/nodes", methods=["GET"])
def get_nodes():
    """
    If query param ?parent=VALUE is present, return only children of that parent (VALUE can be 'null').
    Otherwise return all nodes in the system.
    """
    try:
        parent_str = request.args.get("parent", None)
        if parent_str is not None:
            # If parent_str is "null", interpret as None
            if parent_str.lower() == "null":
                parent_id = None
            else:
                parent_id = int(parent_str)

            nodes = dao.read_by_parent(parent_id)
        else:
            nodes = dao.read_all()

        result = []
        for node in nodes:
            result.append({
                "ID": node.ID,
                "ParentID": node.ParentID,
                "Name": node.Name,
                "Description": node.Description,
                "Notes": node.Notes,
                "Tags": node.Tags,
                "Metadata": node.Metadata,
                "Status": node.Status,
                "Importance": node.Importance,
                "SortOrder": node.SortOrder
            })
        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# -----------------------------------------------------------
# 3) UPDATE - PATCH /nodes/<id>
# -----------------------------------------------------------
@app.route("/nodes/<int:node_id>", methods=["PATCH"])
def update_node(node_id):
    """
    The JSON body should have:
    {
      "old": { ... },
      "new": { ... }
    }
    We do concurrency check on old's ID, ParentID, Status, Importance.
    """
    try:
        body = request.json
        if not body or "old" not in body or "new" not in body:
            return jsonify({"error": "Must provide 'old' and 'new' objects"}), 400

        old_data = body["old"]
        new_data = body["new"]

        # Ensure the IDs match the URL param
        if old_data.get("ID") != node_id or new_data.get("ID") != node_id:
            return jsonify({"error": "Mismatched node_id in URL vs. JSON"}), 400

        old_node = SystemNode(
            ID=old_data["ID"],
            ParentID=old_data["ParentID"],
            Name=old_data.get("Name", ""),  # might not matter
            Description=old_data.get("Description"),
            Notes=old_data.get("Notes"),
            Tags=old_data.get("Tags", {}),
            Metadata=old_data.get("Metadata", {}),
            Status=old_data.get("Status"),
            Importance=old_data.get("Importance", 0),
            SortOrder=old_data.get("SortOrder", 0)
        )

        new_node = SystemNode(
            ID=new_data["ID"],
            ParentID=new_data.get("ParentID"),
            Name=new_data.get("Name", ""),
            Description=new_data.get("Description"),
            Notes=new_data.get("Notes"),
            Tags=new_data.get("Tags", {}),
            Metadata=new_data.get("Metadata", {}),
            Status=new_data.get("Status"),
            Importance=new_data.get("Importance", 0),
            SortOrder=new_data.get("SortOrder", 0)
        )

        success = dao.update(old_node, new_node)
        if success:
            return jsonify({"message": "Node updated"}), 200
        else:
            return jsonify({"error": "Update failed (concurrency mismatch or node not found)"}), 409

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# -----------------------------------------------------------
# 4) DELETE - DELETE /nodes/<id>
# -----------------------------------------------------------
@app.route("/nodes/<int:node_id>", methods=["DELETE"])
def delete_node(node_id):
    """
    JSON body:
    {
      "old": {
         "ID": 123,
         "ParentID": ...,
         "Status": ...,
         "Importance": ...
      }
    }
    """
    try:
        body = request.json
        if not body or "old" not in body:
            return jsonify({"error": "Must provide 'old' object"}), 400

        old_data = body["old"]
        if old_data.get("ID") != node_id:
            return jsonify({"error": "Mismatched node_id in URL vs. JSON"}), 400

        old_node = SystemNode(
            ID=old_data["ID"],
            ParentID=old_data.get("ParentID"),
            Name=old_data.get("Name", ""),
            Description=old_data.get("Description"),
            Notes=old_data.get("Notes"),
            Tags=old_data.get("Tags", {}),
            Metadata=old_data.get("Metadata", {}),
            Status=old_data.get("Status"),
            Importance=old_data.get("Importance", 0),
            SortOrder=old_data.get("SortOrder", 0)
        )

        success = dao.delete(old_node)
        if success:
            return jsonify({"message": f"Node {node_id} deleted"}), 200
        else:
            return jsonify({"error": "Delete failed (concurrency mismatch or node not found)"}), 409

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# -----------------------------------------------------------
# 5) MOVE - POST /nodes/<id>/move
# -----------------------------------------------------------
@app.route("/nodes/<int:node_id>/move", methods=["POST"])
def move_node_endpoint(node_id):
    """
    JSON body example:
    {
      "new_parent_id": 123,     # optional if you want to move under parent=123
      "target_index": 2         # optional if you want to place at index=2 among siblings
    }
    """
    try:
        body = request.json
        if not body:
            return jsonify({"error": "No JSON provided"}), 400

        new_parent_id = body.get("new_parent_id", None)
        target_index = body.get("target_index", None)
        # move_node(...) signature is (node_id, new_parent_id, target_index=None)

        success = dao.move_node(node_id, new_parent_id, target_index)
        if success:
            msg = f"Node {node_id} moved to parent {new_parent_id}"
            if target_index is not None:
                msg += f" at index {target_index}"
            return jsonify({"message": msg}), 200
        else:
            return jsonify({"error": "Move failed (node not found?)"}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# -----------------------------------------------------------
# RUN LOCALLY
# -----------------------------------------------------------
if __name__ == "__main__":
    # For local dev: app.run(debug=True, host="0.0.0.0", port=8080)
    # For production (e.g. Cloud Run), use gunicorn or similar WSGI server.
    app.run(debug=True, host="0.0.0.0", port=8080)
