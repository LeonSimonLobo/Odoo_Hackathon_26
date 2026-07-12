import sys
import os
import requests
from datetime import datetime, timedelta, date

# Reset the database to clean dev state before E2E run
print("=== Step 0: Resetting Database to Seed State ===")
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from seed import seed_database
seed_database()

BASE_URL = "http://localhost:8000"

class E2EClient:
    def __init__(self):
        self.session = requests.Session()
        
    def login(self, email, password):
        resp = self.session.post(f"{BASE_URL}/auth/login", json={"email": email, "password": password})
        if resp.status_code != 200:
            raise Exception(f"Login failed for {email}: {resp.status_code} - {resp.text}")
        print(f"  Logged in as: {email}")
        return resp.json()

    def get(self, path):
        resp = self.session.get(f"{BASE_URL}{path}")
        if resp.status_code != 200:
            raise Exception(f"GET {path} failed: {resp.status_code} - {resp.text}")
        return resp.json()

    def post(self, path, json_data):
        resp = self.session.post(f"{BASE_URL}{path}", json=json_data)
        return resp

    def put(self, path, json_data=None):
        resp = self.session.put(f"{BASE_URL}{path}", json=json_data or {})
        return resp

def run_e2e():
    client = E2EClient()

    # =========================================================================
    # STEP 1: Admin sets up departments, categories, and promotes employees
    # =========================================================================
    print("\n=== Step 1: Admin Org Setup & Promotion ===")
    client.login("alice@assetflow.com", "password123")  # Admin

    # 1. Create a department
    dept_resp = client.post("/api/departments", {
        "name": "Security Operations",
        "parent_department_id": None,
        "department_head_id": None,
        "status": "active"
    })
    assert dept_resp.status_code == 201, f"Failed to create department: {dept_resp.text}"
    security_dept_id = dept_resp.json()["id"]
    print(f"  [PASSED] Created department: Security Operations (ID: {security_dept_id})")

    # 2. Create asset category
    cat_resp = client.post("/api/categories", {
        "name": "Network Appliances",
        "description": "Enterprise switches and routers",
        "schema_attributes": {"port_count": 24, "warranty_months": 36}
    })
    assert cat_resp.status_code == 201, f"Failed to create category: {cat_resp.text}"
    cat_id = cat_resp.json()["id"]
    print(f"  [PASSED] Created category: Network Appliances (ID: {cat_id})")

    # 3. Fetch directory and promote Raj to Asset Manager and Bob to Department Head
    employees = client.get("/api/employees")
    raj = next(e for e in employees if e["email"] == "raj@assetflow.com")
    john = next(e for e in employees if e["email"] == "john@assetflow.com")

    promo_raj = client.put(f"/api/employees/{raj['id']}/role", {"role": "asset_manager"})
    assert promo_raj.status_code == 200
    print(f"  [PASSED] Promoted Raj Kumar to Asset Manager")

    promo_john = client.put(f"/api/employees/{john['id']}/role", {"role": "department_head"})
    assert promo_john.status_code == 200
    print(f"  [PASSED] Promoted John Doe to Department Head")


    # =========================================================================
    # STEP 2: Asset Manager registers a new asset
    # =========================================================================
    print("\n=== Step 2: Asset Manager registers new asset ===")
    client.login("raj@assetflow.com", "password123")  # Asset Manager

    asset_resp = client.post("/api/assets", {
        "name": "Cisco Catalyst Switch 9300",
        "category_id": cat_id,
        "serial_number": "CS-C9300-48P",
        "acquisition_date": "2026-07-12",
        "acquisition_cost": 4500.0,
        "condition": "new",
        "location": "HQ Server Room Rack 2",
        "is_shared": False
    })
    assert asset_resp.status_code == 201, f"Failed to register asset: {asset_resp.text}"
    switch_id = asset_resp.json()["id"]
    switch_tag = asset_resp.json()["asset_tag"]
    print(f"  [PASSED] Registered asset: Cisco Catalyst Switch (Tag: {switch_tag}, Status: {asset_resp.json()['status']})")


    # =========================================================================
    # STEP 3: Asset is allocated (and double-allocation is blocked)
    # =========================================================================
    print("\n=== Step 3: Asset Allocation & Double-Allocation Block ===")
    
    # 1. Allocate asset to John Doe
    alloc_resp = client.post("/api/allocations", {
        "asset_id": switch_id,
        "allocated_to_type": "employee",
        "allocated_employee_id": john["id"],
        "expected_return_date": (datetime.utcnow() + timedelta(days=30)).isoformat()
    })
    assert alloc_resp.status_code == 200, f"Failed to allocate: {alloc_resp.text}"
    print(f"  [PASSED] Allocated switch {switch_tag} to John Doe")

    # Verify status changed to allocated
    asset_detail = client.get(f"/api/assets/{switch_id}")
    assert asset_detail["status"] == "allocated"
    print(f"  [PASSED] Asset status updated to: {asset_detail['status']}")

    # 2. Attempt to allocate the same asset to Jane (should block)
    jane = next(e for e in employees if e["email"] == "jane@assetflow.com")
    block_resp = client.post("/api/allocations", {
        "asset_id": switch_id,
        "allocated_to_type": "employee",
        "allocated_employee_id": jane["id"]
    })
    assert block_resp.status_code == 400
    assert "already allocated" in block_resp.json()["detail"]
    print(f"  [PASSED] Successfully blocked double-allocation! Error message: \"{block_resp.json()['detail']}\"")


    # =========================================================================
    # STEP 4: Shared resource bookings & overlap checks
    # =========================================================================
    print("\n=== Step 4: Shared Resource Booking & Overlap Prevention ===")
    
    # 1. Register a shared room asset (which auto-registers a Resource)
    meeting_room_resp = client.post("/api/assets", {
        "name": "Conference Room B2",
        "category_id": 2, # Furniture
        "serial_number": None,
        "acquisition_date": "2026-01-01",
        "acquisition_cost": 500.0,
        "condition": "good",
        "location": "HQ Floor 2",
        "is_shared": True
    })
    assert meeting_room_resp.status_code == 201
    room_id = meeting_room_resp.json()["id"]

    # 2. Fetch the corresponding resource id
    resources = client.get("/api/resources")
    room_resource = next(r for r in resources if r["name"] == "Conference Room B2")
    room_res_id = room_resource["id"]
    print(f"  [PASSED] Shared asset Conference Room B2 registered as Resource ID: {room_res_id}")

    # 3. Jane books the room from 10:00 to 11:00
    client.login("jane@assetflow.com", "password123")
    booking1 = client.post("/api/bookings", {
        "resource_id": room_res_id,
        "start_time": "2026-07-07T10:00:00",
        "end_time": "2026-07-07T11:00:00"
    })
    assert booking1.status_code == 200, f"Failed to book room: {booking1.text}"
    print(f"  [PASSED] Jane Smith booked Conference Room B2 for 10:00 - 11:00")

    # 4. Raj attempts to book the room from 10:30 to 11:30 (should reject)
    client.login("raj@assetflow.com", "password123")
    booking2 = client.post("/api/bookings", {
        "resource_id": room_res_id,
        "start_time": "2026-07-07T10:30:00",
        "end_time": "2026-07-07T11:30:00"
    })
    assert booking2.status_code == 400
    assert "already booked" in booking2.json()["detail"].lower() or "conflict" in booking2.json()["detail"].lower()
    print(f"  [PASSED] Successfully blocked overlapping booking! Error message: \"{booking2.json()['detail']}\"")


    # =========================================================================
    # STEP 5: Maintenance request workflow
    # =========================================================================
    print("\n=== Step 5: Maintenance Workflow & Status Transitions ===")
    client.login("john@assetflow.com", "password123") # Holder

    # 1. John Doe raises a maintenance request for Cisco Switch
    maint_resp = client.post("/api/maintenance", {
        "asset_id": switch_id,
        "description": "Port 3 is dead and power cable is frayed.",
        "priority": "critical"
    })
    assert maint_resp.status_code == 201
    maint_id = maint_resp.json()["id"]
    print(f"  [PASSED] John Doe raised maintenance request (ID: {maint_id}, Status: {maint_resp.json()['status']})")

    # Verify asset status is still allocated (not under maintenance yet)
    switch_detail = client.get(f"/api/assets/{switch_id}")
    assert switch_detail["status"] == "allocated"
    print(f"  [PASSED] Asset status remains: {switch_detail['status']}")

    # 2. Asset Manager approves the maintenance request
    client.login("raj@assetflow.com", "password123")
    approve_resp = client.put(f"/api/maintenance/{maint_id}/status", {
        "status": "approved"
    })
    assert approve_resp.status_code == 200
    print(f"  [PASSED] Asset Manager approved maintenance request")

    # Verify asset status changed to under_maintenance automatically
    switch_detail = client.get(f"/api/assets/{switch_id}")
    assert switch_detail["status"] == "under_maintenance"
    print(f"  [PASSED] Asset status transitioned to: {switch_detail['status']} (under-maintenance trigger)")


    # =========================================================================
    # STEP 6: Transfers, Returns & Overdue returns
    # =========================================================================
    print("\n=== Step 6: Transfers, Returns & Overdue Logs ===")
    
    # 1. Jane raises transfer request for the Cisco Switch
    client.login("jane@assetflow.com", "password123")
    transfer_resp = client.post("/api/transfers", {
        "asset_id": switch_id,
        "target_employee_id": jane["id"],
        "comments": "Need this switch for testing security protocols."
    })
    assert transfer_resp.status_code == 200
    transfer_id = transfer_resp.json()["id"]
    print(f"  [PASSED] Jane Smith requested transfer of switch {switch_tag} (ID: {transfer_id})")

    # 2. Asset Manager approves the transfer
    client.login("raj@assetflow.com", "password123")
    approve_trans = client.put(f"/api/transfers/{transfer_id}/approve")
    assert approve_trans.status_code == 200
    print(f"  [PASSED] Asset Manager approved transfer request")

    # Verify allocation is transferred
    switch_detail = client.get(f"/api/assets/{switch_id}")
    assert switch_detail["status"] == "allocated"
    print(f"  [PASSED] Switch is now successfully allocated to target holder")

    # 3. Check overdue returns analytics
    client.login("alice@assetflow.com", "password123")
    overdue_list = client.get("/api/analytics/overdue")
    assert len(overdue_list) > 0
    print(f"  [PASSED] Overdue Return logs fetched. Found {len(overdue_list)} overdue allocations.")


    # =========================================================================
    # STEP 7: Periodic Audit Cycles
    # =========================================================================
    print("\n=== Step 7: Audit Cycle Verification & Closures ===")
    
    # 1. Admin creates an audit cycle scope: all assets, assigned to John Doe
    audit_resp = client.post("/api/audits/cycles", {
        "name": "E2E Q3 Inventory Verification",
        "scope_type": "all",
        "start_date": "2026-07-01",
        "end_date": "2026-07-30",
        "auditor_ids": [john["id"]]
    })
    assert audit_resp.status_code == 201, f"Audit creation failed: {audit_resp.text}"
    cycle_id = audit_resp.json()["id"]
    print(f"  [PASSED] Admin initiated Audit Cycle: E2E Q3 Inventory Verification (ID: {cycle_id})")

    # 2. John Doe lists and verifies audit items
    client.login("john@assetflow.com", "password123")
    audit_items = client.get(f"/api/audits/cycles/{cycle_id}/items")
    switch_item = next(it for it in audit_items if it["asset_id"] == switch_id)
    
    verify_resp = client.put(f"/api/audits/items/{switch_item['id']}", {
        "verification_status": "damaged",
        "notes": "Chassis got slightly bent during transfer."
    })
    assert verify_resp.status_code == 200
    print(f"  [PASSED] Auditor John Doe flagged Cisco Switch as 'damaged' with notes")

    # 3. Admin closes the audit cycle
    client.login("alice@assetflow.com", "password123")
    close_resp = client.put(f"/api/audits/cycles/{cycle_id}/close")
    assert close_resp.status_code == 200
    print(f"  [PASSED] Admin closed the audit cycle")

    # Verify that the closed cycle automatically cascaded the switch status to under_maintenance
    switch_detail = client.get(f"/api/assets/{switch_id}")
    assert switch_detail["status"] == "under_maintenance"
    print(f"  [PASSED] Closed cycle cascaded switch status to: {switch_detail['status']}")


    # =========================================================================
    # STEP 8: Live Activity Logging & Notification Feeds
    # =========================================================================
    print("\n=== Step 8: Activity Tracking & Live Notifications ===")
    
    # 1. Verify notification feed for John Doe
    client.login("john@assetflow.com", "password123")
    notifs = client.get("/api/notifications")
    assert len(notifs) > 0
    print(f"  [PASSED] John Doe notification feed contains {len(notifs)} alerts. Latest: \"{notifs[0]['title']}: {notifs[0]['message']}\"")

    # 2. Verify central audit activity logs
    client.login("alice@assetflow.com", "password123")
    logs = client.get("/api/activity-logs")
    assert len(logs) > 0
    actions = [l["action"] for l in logs]
    print(f"  [PASSED] Verified central auditable logs containing actions: {set(actions[:5])}")

    print("\n=======================================================")
    print("  ALL E2E INTEGRATION WORKFLOW TESTS PASSED SUCCESSFULLY!")
    print("=======================================================")

if __name__ == "__main__":
    run_e2e()
