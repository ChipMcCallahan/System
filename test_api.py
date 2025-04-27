#!/usr/bin/env python3

"""
./cloud-sql-proxy jbone-system:us-west1:jbone-system-sql --port=3306

A thorough Python script that uses subprocess + curl to exercise:
- Creating multiple parent nodes
- Creating multiple child nodes
- Reordering children
- Moving children between parents / null parent
- Checking that deleting a parent with children fails
- Finally cleaning everything up to restore the DB to its original state


export DB_HOST="127.0.0.1"
export DB_USER={your-db-user}
export DB_PASSWORD={your-db-password}
export DB_NAME="{your-db-name}"
python app.py

python test_api.py
"""

import subprocess
import json
import sys

BASE_URL = "http://127.0.0.1:8080"  # Adjust if needed


def run_curl_v2(method, endpoint, data=None):
    """
    Runs a curl command with the given method (GET, POST, PATCH, DELETE)
    and endpoint (e.g. '/nodes/123'). 'data' is a dict -> JSON body.

    Returns (status_code, parsed_json_or_string).
    """
    url = f"{BASE_URL}{endpoint}"
    cmd = [
        "curl", "-s",
        "-X", method, url,
        "-H", "Content-Type: application/json",
        "-w", "\n%{http_code}"
    ]
    if data is not None:
        json_str = json.dumps(data)
        cmd += ["-d", json_str]

    result = subprocess.run(cmd, capture_output=True, text=True)
    lines = result.stdout.strip().split("\n")
    if len(lines) < 2:
        return (999, result.stdout.strip())  # Something unexpected
    body = "\n".join(lines[:-1])
    status_str = lines[-1]
    try:
        status_code = int(status_str)
    except ValueError:
        status_code = 999

    # Attempt to parse the body as JSON
    try:
        parsed_body = json.loads(body)
        return (status_code, parsed_body)
    except json.JSONDecodeError:
        return (status_code, body)


def main():
    print("=== Thorough test of SystemNode Flask API ===")

    # 1) Capture original DB state
    status, orig_nodes = run_curl_v2("GET", "/nodes")
    if status != 200:
        print(f"Cannot get /nodes initially. Status={status}, body={orig_nodes}")
        sys.exit(1)
    orig_json_str = json.dumps(orig_nodes, sort_keys=True)

    # We'll keep track of the IDs we create so we can delete them in reverse order if needed.
    # But we'll do it systematically.

    created_parents = []
    created_children = []

    # 2) Create two parent nodes: "ParentA" and "ParentB"
    for parent_name in ["ParentA", "ParentB"]:
        payload = {
            "Name": parent_name,
            "ParentID": None,
            "Status": "Parent",
            "Importance": 1
        }
        st, resp = run_curl_v2("POST", "/nodes", payload)
        if st != 201:
            print(f"Failed to create parent '{parent_name}': status={st}, resp={resp}")
            sys.exit(1)
        new_id = resp.get("ID")
        print(f"Created parent {parent_name} with ID={new_id}")
        created_parents.append((new_id, parent_name))

    parentA_id = created_parents[0][0]
    parentB_id = created_parents[1][0]

    # 3) Create multiple child nodes under parent A: Child1, Child2, Child3
    for i in range(1, 4):
        payload = {
            "Name": f"Child{i}",
            "ParentID": parentA_id,
            "Status": "Child",
            "Importance": 2
        }
        st, resp = run_curl_v2("POST", "/nodes", payload)
        if st != 201:
            print(f"Failed to create child Child{i}: status={st}, resp={resp}")
            sys.exit(1)
        cid = resp.get("ID")
        print(f"Created child {cid} -> 'Child{i}' under ParentA={parentA_id}")
        created_children.append(cid)

    # 4) Reorder children under ParentA. Let's reorder Child2 to index=0 (top).
    # We need to find the child2 ID from created_children. It's the second we created, i.e. created_children[1].
    child2_id = created_children[1]
    reorder_payload = {
        "new_parent_id": parentA_id,
        "target_index": 0
    }
    st, move_resp = run_curl_v2("POST", f"/nodes/{child2_id}/move", reorder_payload)
    if st == 200:
        print(f"Reordered child2 (ID={child2_id}) to index=0 in ParentA.")
    else:
        print(f"Reorder child2 failed: st={st}, resp={move_resp}")
        sys.exit(1)

    # 5) Move Child2 to ParentB at index=0
    # (i.e., re-parent Child2 from ParentA to ParentB)
    st, move_resp = run_curl_v2("POST", f"/nodes/{child2_id}/move",
                                {"new_parent_id": parentB_id, "target_index": 0})
    if st == 200:
        print(f"Moved child2 (ID={child2_id}) from ParentA to ParentB at index=0.")
    else:
        print(f"Move child2 to parentB failed: st={st}, resp={move_resp}")
        sys.exit(1)

    # 6) Attempt to delete ParentA while it still has children (Child1 & Child3).
    # This should fail if your DB has a foreign key restricting that.
    # We'll read ParentA node so we have concurrency data.
    st, parentA_info = run_curl_v2("GET", f"/nodes/{parentA_id}")
    if st != 200:
        print(f"Failed to read ParentA for concurrency data. st={st}, resp={parentA_info}")
        sys.exit(1)
    # old object
    old_parentA = {
        "ID": parentA_info["ID"],
        "ParentID": parentA_info["ParentID"],
        "Name": parentA_info["Name"],
        "Description": parentA_info["Description"],
        "Notes": parentA_info["Notes"],
        "Tags": parentA_info["Tags"],
        "Metadata": parentA_info["Metadata"],
        "Status": parentA_info["Status"],
        "Importance": parentA_info["Importance"]
    }
    # Try deleting
    st, delA_resp = run_curl_v2("DELETE", f"/nodes/{parentA_id}", {"old": old_parentA})
    if st == 200:
        print("WARNING: ParentA was deleted but it still has children. Possibly your DB didn't restrict it.")
    else:
        print(f"Expected fail to delete ParentA with children => st={st}, resp={delA_resp}")

    # 7) Delete the child nodes. We'll do them in reverse creation order, or any order.
    # child2 is in parentB, child1/child3 in parentA
    # We do concurrency checks for each child
    def delete_node(node_id):
        # read node to get concurrency 'old' object
        st_read, node_info = run_curl_v2("GET", f"/nodes/{node_id}")
        if st_read != 200:
            print(f"Cannot read node {node_id} before delete, st={st_read}, resp={node_info}")
            return False
        old_obj = {
            "ID": node_info["ID"],
            "ParentID": node_info["ParentID"],
            "Name": node_info["Name"],
            "Description": node_info["Description"],
            "Notes": node_info["Notes"],
            "Tags": node_info["Tags"],
            "Metadata": node_info["Metadata"],
            "Status": node_info["Status"],
            "Importance": node_info["Importance"]
        }
        st_del, del_resp = run_curl_v2("DELETE", f"/nodes/{node_id}", {"old": old_obj})
        if st_del == 200:
            print(f"Deleted node {node_id} successfully.")
            return True
        else:
            print(f"Failed to delete node {node_id}, st={st_del}, resp={del_resp}")
            return False

    # Let's delete Child3 => child2 => child1
    # But child2 is in parentB now, no real difference. The order is arbitrary.
    # We'll do child3, child1, child2
    for c in [created_children[2], created_children[0], created_children[1]]:
        if not delete_node(c):
            sys.exit(1)

    # 8) Now that we've deleted the children, we can try to delete ParentA & ParentB.
    # We'll define a quick function for parent concurrency:
    def delete_parent(node_id):
        st_read, node_info = run_curl_v2("GET", f"/nodes/{node_id}")
        if st_read != 200:
            print(f"Cannot read parent {node_id} before delete, st={st_read}, resp={node_info}")
            return False
        old_obj = {
            "ID": node_info["ID"],
            "ParentID": node_info["ParentID"],
            "Name": node_info["Name"],
            "Description": node_info["Description"],
            "Notes": node_info["Notes"],
            "Tags": node_info["Tags"],
            "Metadata": node_info["Metadata"],
            "Status": node_info["Status"],
            "Importance": node_info["Importance"]
        }
        st_del, del_resp = run_curl_v2("DELETE", f"/nodes/{node_id}", {"old": old_obj})
        if st_del == 200:
            print(f"Deleted parent {node_id} successfully.")
            return True
        else:
            print(f"Failed to delete parent {node_id}, st={st_del}, resp={del_resp}")
            return False

    # ParentA, ParentB
    if not delete_parent(parentA_id):
        sys.exit(1)
    if not delete_parent(parentB_id):
        sys.exit(1)

    # 9) final read
    st_final, final_nodes = run_curl_v2("GET", "/nodes")
    if st_final != 200:
        print(f"Failed final read /nodes, st={st_final}, body={final_nodes}")
        sys.exit(1)

    final_json_str = json.dumps(final_nodes, sort_keys=True)
    if final_json_str == orig_json_str:
        print("SUCCESS: The DB ended in the same state as we found it.")
    else:
        print("WARNING: DB final state differs from initial.")
        print("Original:", orig_json_str)
        print("Final:   ", final_json_str)


if __name__ == "__main__":
    main()
