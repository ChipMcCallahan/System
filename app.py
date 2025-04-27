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


# 1) CREATE - POST /nodes
#    Expects JSON with the fields needed for a new node.
@app.route("/nodes", methods=["POST"])
def create_node():
    try:
        data = request.json
        # Minimal validation for required fields
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


# 2) READ - GET /nodes/<id>
@app.route("/nodes/<int:node_id>", methods=["GET"])
def get_node(node_id):
    try:
        node = dao.read(node_id)
        if node is None:
            return jsonify({"error": "Node not found"}), 404

        # Convert node to a dict to return as JSON
        return jsonify({
            "ID": node.ID,
            "ParentID": node.ParentID,
            "Name": node.Name,
            "Description": node.Description,
            "Notes": node.Notes,
            "Tags": node.Tags,
            "Metadata": node.Metadata,
            "Status": node.Status,
            "Importance": node.Importance
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# 3) UPDATE - PATCH /nodes/<id>
#    Because your DAO does concurrency check with old & new, we expect "old" and "new" objects in JSON.
@app.route("/nodes/<int:node_id>", methods=["PATCH"])
def update_node(node_id):
    """
    The JSON body should look like:
    {
      "old": {
        "ID": 123, "ParentID": ..., "Name": ..., etc.
      },
      "new": {
        "ID": 123, "ParentID": ..., "Name": ..., etc.
      }
    }
    """
    try:
        body = request.json
        if not body or "old" not in body or "new" not in body:
            return jsonify({"error": "Must provide 'old' and 'new' objects"}), 400

        old_data = body["old"]
        new_data = body["new"]

        # Ensure IDs match the URL param
        if old_data.get("ID") != node_id or new_data.get("ID") != node_id:
            return jsonify({"error": "Mismatched node_id in URL vs. JSON"}), 400

        # Convert the dicts into SystemNode objects
        old_node = SystemNode(
            ID=old_data["ID"],
            ParentID=old_data["ParentID"],
            Name=old_data["Name"],
            Description=old_data["Description"],
            Notes=old_data["Notes"],
            Tags=old_data.get("Tags", {}),
            Metadata=old_data.get("Metadata", {}),
            Status=old_data["Status"],
            Importance=old_data["Importance"]
        )

        new_node = SystemNode(
            ID=new_data["ID"],
            ParentID=new_data["ParentID"],
            Name=new_data["Name"],
            Description=new_data["Description"],
            Notes=new_data["Notes"],
            Tags=new_data.get("Tags", {}),
            Metadata=new_data.get("Metadata", {}),
            Status=new_data["Status"],
            Importance=new_data["Importance"]
        )

        success = dao.update(old_node, new_node)
        if success:
            return jsonify({"message": "Node updated"}), 200
        else:
            return jsonify({"error": "Update failed (concurrency mismatch or node not found)"}), 409
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# 4) DELETE - DELETE /nodes/<id>
#    We must pass an "old" object in JSON to ensure concurrency check.
@app.route("/nodes/<int:node_id>", methods=["DELETE"])
def delete_node(node_id):
    """
    The JSON body for concurrency might look like:
    {
      "old": {
        "ID": 123, "ParentID": ..., etc
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
            ParentID=old_data["ParentID"],
            Name=old_data["Name"],
            Description=old_data["Description"],
            Notes=old_data["Notes"],
            Tags=old_data.get("Tags", {}),
            Metadata=old_data.get("Metadata", {}),
            Status=old_data["Status"],
            Importance=old_data["Importance"]
        )

        success = dao.delete(old_node)
        if success:
            return jsonify({"message": f"Node {node_id} deleted"}), 200
        else:
            return jsonify({"error": "Delete failed (concurrency mismatch or node not found)"}), 409
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# 5) MOVE - POST /nodes/<id>/move
@app.route("/nodes/<int:node_id>/move", methods=["POST"])
def move_node(node_id):
    """
    JSON body:
    {
      "new_parent_id": 999
    }
    This will call dao.move_node(node_id, new_parent_id).
    """
    try:
        body = request.json
        if not body or "new_parent_id" not in body:
            return jsonify({"error": "Missing 'new_parent_id'"}), 400

        new_parent_id = body["new_parent_id"]
        success = dao.move_node(node_id, new_parent_id)
        if success:
            return jsonify({"message": f"Node {node_id} moved to parent {new_parent_id}"}), 200
        else:
            return jsonify({"error": "Move failed (node not found?)"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Running Flask locally:
if __name__ == "__main__":
    # Typically, you'd do `app.run(debug=True, host="0.0.0.0", port=8080)`
    # for local development. On production (e.g., Cloud Run), Gunicorn is recommended.
    app.run(debug=True, host="0.0.0.0", port=8080)
