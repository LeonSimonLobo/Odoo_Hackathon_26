import sys
from datetime import datetime, date, timedelta
from database import Base, engine, SessionLocal
from security import hash_password
from models import (
    Department, Employee, AssetCategory, Asset, AssetAllocation,
    TransferRequest, Resource, ResourceBooking, MaintenanceRequest,
    AuditCycle, AuditCycleAuditor, AuditItem, Notification, ActivityLog
)

def seed_database():
    # Initialize the database and create tables
    print("Initializing database tables...")
    Base.metadata.drop_all(bind=engine)  # Fresh start
    Base.metadata.create_all(bind=engine)

    session = SessionLocal()

    try:
        print("Seeding asset categories...")
        cat_electronics = AssetCategory(
            name="Electronics",
            description="Laptops, smartphones, tablets, monitors, and accessories",
            schema_attributes={"warranty_period_months": 24, "type": "Computing"}
        )
        cat_furniture = AssetCategory(
            name="Furniture",
            description="Desks, ergonomic chairs, tables, and cabinets",
            schema_attributes={"material": "Wood/Metal", "dimensions": "Standard"}
        )
        cat_vehicles = AssetCategory(
            name="Vehicles",
            description="Company cars, delivery vans, and shuttle buses",
            schema_attributes={"fuel_type": "Diesel/EV", "mileage_limit_km": 150000}
        )
        session.add_all([cat_electronics, cat_furniture, cat_vehicles])
        session.flush()  # Generate IDs

        print("Seeding temporary employees (for circular reference resolution)...")
        # Default dev password for all seeded accounts.
        pwd_hash = hash_password("password123")
        
        # 1. Admins & Asset Managers
        admin_alice = Employee(name="Alice Admin", email="alice@assetflow.com", password_hash=pwd_hash, role="admin")
        manager_mark = Employee(name="Mark Manager", email="mark@assetflow.com", password_hash=pwd_hash, role="asset_manager")
        
        # 2. Future Department Heads
        head_priya = Employee(name="Priya Patel", email="priya@assetflow.com", password_hash=pwd_hash, role="department_head")
        head_sarah = Employee(name="Sarah Jenkins", email="sarah@assetflow.com", password_hash=pwd_hash, role="department_head")
        head_dave = Employee(name="Dave Vance", email="dave@assetflow.com", password_hash=pwd_hash, role="department_head")

        # 3. Standard Employees
        emp_raj = Employee(name="Raj Kumar", email="raj@assetflow.com", password_hash=pwd_hash, role="employee")
        emp_john = Employee(name="John Doe", email="john@assetflow.com", password_hash=pwd_hash, role="employee")
        emp_jane = Employee(name="Jane Smith", email="jane@assetflow.com", password_hash=pwd_hash, role="employee")

        session.add_all([admin_alice, manager_mark, head_priya, head_sarah, head_dave, emp_raj, emp_john, emp_jane])
        session.flush()

        print("Seeding departments...")
        dept_eng = Department(name="Engineering", status="active", department_head_id=head_priya.id)
        dept_hr = Department(name="Human Resources", status="active", department_head_id=head_sarah.id)
        dept_ops = Department(name="Operations", status="active", department_head_id=head_dave.id)
        session.add_all([dept_eng, dept_hr, dept_ops])
        session.flush()

        # Update departments references for employees
        head_priya.department_id = dept_eng.id
        head_sarah.department_id = dept_hr.id
        head_dave.department_id = dept_ops.id
        emp_raj.department_id = dept_eng.id
        emp_john.department_id = dept_hr.id
        emp_jane.department_id = dept_ops.id
        session.flush()

        print("Seeding assets...")
        # Available Electronics
        asset_macbook = Asset(
            name="MacBook Pro M3 Max",
            category_id=cat_electronics.id,
            asset_tag="AF-0001",
            serial_number="C02FG456Q05D",
            acquisition_date=date(2025, 6, 15),
            acquisition_cost=3499.00,
            condition="new",
            location="HQ - Floor 3 - Room 302",
            is_shared=False,
            status="available"
        )
        
        # Allocated Electronics
        asset_dell = Asset(
            name="Dell XPS 15",
            category_id=cat_electronics.id,
            asset_tag="AF-0002",
            serial_number="D15XPS9530",
            acquisition_date=date(2024, 1, 10),
            acquisition_cost=1899.00,
            condition="good",
            location="HQ - Floor 3 - Engineering",
            is_shared=False,
            status="available"  # Will transition to 'allocated' on seeding allocation
        )

        # Available Furniture
        asset_desk = Asset(
            name="Ergonomic Standing Desk",
            category_id=cat_furniture.id,
            asset_tag="AF-0003",
            serial_number="FN-DESK-092",
            acquisition_date=date(2024, 3, 1),
            acquisition_cost=650.00,
            condition="good",
            location="HQ - Floor 2 - Workspaces",
            is_shared=False,
            status="available"
        )
        
        asset_table = Asset(
            name="Conference Room Table",
            category_id=cat_furniture.id,
            asset_tag="AF-0004",
            serial_number="FN-CONF-002",
            acquisition_date=date(2023, 8, 20),
            acquisition_cost=1500.00,
            condition="good",
            location="Meeting Room B2",
            is_shared=True,
            status="available"
        )

        # Under Maintenance Vehicle
        asset_tesla = Asset(
            name="Tesla Model 3 (Company Car)",
            category_id=cat_vehicles.id,
            asset_tag="AF-0005",
            serial_number="5YJ3E1EA5LF12345",
            acquisition_date=date(2023, 11, 15),
            acquisition_cost=42000.00,
            condition="fair",
            location="Main Garage - Bay 2",
            is_shared=True,
            status="available"  # Will transition to 'under_maintenance' on seeding request approval
        )

        # Overdue return Laptop
        asset_thinkpad = Asset(
            name="ThinkPad T14 Gen 4",
            category_id=cat_electronics.id,
            asset_tag="AF-0006",
            serial_number="TP-T14-049281",
            acquisition_date=date(2024, 5, 20),
            acquisition_cost=1200.00,
            condition="good",
            location="HQ - Floor 3 - Engineering",
            is_shared=False,
            status="available"  # Will transition to 'allocated'
        )

        # Lost Asset
        asset_ipad = Asset(
            name="iPad Air 5th Gen",
            category_id=cat_electronics.id,
            asset_tag="AF-0007",
            serial_number="GG7F289N0D5",
            acquisition_date=date(2024, 8, 5),
            acquisition_cost=699.00,
            condition="good",
            location="Unknown",
            is_shared=False,
            status="lost"
        )

        # Shared/Bookable Vehicle
        asset_van = Asset(
            name="Toyota HiAce 12-Seater Van",
            category_id=cat_vehicles.id,
            asset_tag="AF-0008",
            serial_number="JT182JT910283",
            acquisition_date=date(2023, 5, 12),
            acquisition_cost=31000.00,
            condition="good",
            location="Garage A - Spot 3",
            is_shared=True,
            status="available"
        )

        session.add_all([
            asset_macbook, asset_dell, asset_desk, asset_table,
            asset_tesla, asset_thinkpad, asset_ipad, asset_van
        ])
        session.flush()

        print("Seeding active asset allocations...")
        # 1. Priya Patel holds Dell XPS 15 (AF-0002) - active
        alloc_priya = AssetAllocation(
            asset_id=asset_dell.id,
            allocated_to_type="employee",
            allocated_employee_id=head_priya.id,
            allocated_by_id=manager_mark.id,
            allocation_date=datetime.utcnow() - timedelta(days=30),
            expected_return_date=datetime.utcnow() + timedelta(days=335),
            status="active"
        )
        
        # 2. Raj Kumar holds ThinkPad T14 (AF-0006) - active but OVERDUE (expected return date was yesterday)
        alloc_raj = AssetAllocation(
            asset_id=asset_thinkpad.id,
            allocated_to_type="employee",
            allocated_employee_id=emp_raj.id,
            allocated_by_id=manager_mark.id,
            allocation_date=datetime.utcnow() - timedelta(days=20),
            expected_return_date=datetime.utcnow() - timedelta(days=1), # Yesterday
            status="active"
        )
        
        # 3. Standing Desk (AF-0003) was allocated to HR dept and returned
        alloc_returned = AssetAllocation(
            asset_id=asset_desk.id,
            allocated_to_type="department",
            allocated_department_id=dept_hr.id,
            allocated_by_id=manager_mark.id,
            allocation_date=datetime.utcnow() - timedelta(days=90),
            expected_return_date=datetime.utcnow() - timedelta(days=60),
            actual_return_date=datetime.utcnow() - timedelta(days=61),
            condition_check_in_notes="Returned in excellent condition. Back in stock.",
            status="returned"
        )

        session.add_all([alloc_priya, alloc_raj, alloc_returned])
        session.flush()  # Triggers the event listeners which updates Asset status to 'allocated'

        print("Seeding transfer requests...")
        # Raj has ThinkPad AF-0006. Priya Patel tries to allocate it or requests transfer
        transfer_request = TransferRequest(
            asset_id=asset_thinkpad.id,
            requestor_employee_id=head_priya.id,
            target_employee_id=head_priya.id,
            current_holder_employee_id=emp_raj.id,
            status="pending",
            comments="I need this specific laptop model for running local engineering tests."
        )
        session.add(transfer_request)
        session.flush()

        print("Seeding shared resources for booking...")
        res_room_b2 = Resource(
            name="Conference Room B2",
            type="room",
            asset_id=asset_table.id, # Map to the conference table asset
            description="Capacity of 12 people, smart whiteboard, 4K screen, and glass walls.",
            status="active"
        )
        res_tesla = Resource(
            name="Tesla Model 3 (Car)",
            type="vehicle",
            asset_id=asset_tesla.id,
            description="Fully electric sedan, keyless access. Active company vehicle.",
            status="active"
        )
        res_van = Resource(
            name="Toyota HiAce (Van)",
            type="vehicle",
            asset_id=asset_van.id,
            description="12-seater utility van for client transport or team events.",
            status="active"
        )
        session.add_all([res_room_b2, res_tesla, res_van])
        session.flush()

        print("Seeding resource bookings...")
        # Today's date reference
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # 1. Upcoming booking today 14:00 - 15:00 for Room B2 by Raj Kumar
        booking_upcoming = ResourceBooking(
            resource_id=res_room_b2.id,
            booked_by_employee_id=emp_raj.id,
            start_time=today + timedelta(hours=14),
            end_time=today + timedelta(hours=15),
            status="upcoming"
        )
        # 2. Completed booking yesterday for Room B2 by Sarah Jenkins
        booking_completed = ResourceBooking(
            resource_id=res_room_b2.id,
            booked_by_employee_id=head_sarah.id,
            start_time=today - timedelta(days=1, hours=10),
            end_time=today - timedelta(days=1, hours=8),
            status="completed"
        )
        # 3. Upcoming booking tomorrow for Toyota Van by Dave Vance
        booking_tomorrow = ResourceBooking(
            resource_id=res_van.id,
            booked_by_employee_id=head_dave.id,
            start_time=today + timedelta(days=1, hours=9),
            end_time=today + timedelta(days=1, hours=17),
            status="upcoming"
        )
        session.add_all([booking_upcoming, booking_completed, booking_tomorrow])
        session.flush()

        print("Seeding maintenance requests...")
        # 1. Tesla Model 3 has battery charge fault - approved & in progress
        maint_tesla = MaintenanceRequest(
            asset_id=asset_tesla.id,
            raised_by_employee_id=head_dave.id,
            description="Vehicle dashboard displays warning 'Electrical System Error: Charging Vault Fault'. Battery drains rapidly.",
            priority="high",
            status="approved", # Transitions asset to under_maintenance
            technician_name="Tesla Service Center, San Jose",
            actioned_by_id=manager_mark.id,
            actioned_at=datetime.utcnow() - timedelta(days=2)
        )
        # 2. MacBook Pro M3 (AF-0001) has flickering screen - pending approval
        maint_macbook = MaintenanceRequest(
            asset_id=asset_macbook.id,
            raised_by_employee_id=emp_raj.id,
            description="Lower quarter of the screen flickers erratically when running heavy processes or connected to external display.",
            priority="medium",
            status="pending"
        )
        session.add_all([maint_tesla, maint_macbook])
        session.flush()  # Transitions Tesla status to 'under_maintenance'

        # Let's force Tesla status to under_maintenance explicitly via session updates (or relying on listener)
        # Actually our listener did this! We will confirm it in verification.
        
        print("Seeding audit cycle...")
        # 1. Audit Cycle: Q3 2026 Engineering Directory Audit
        audit_cycle = AuditCycle(
            name="Q3 2026 Engineering Directory Audit",
            scope_type="department",
            scope_department_id=dept_eng.id,
            start_date=date(2026, 7, 1),
            end_date=date(2026, 7, 31),
            status="open"
        )
        session.add(audit_cycle)
        session.flush()

        # Assign Mark Manager as auditor
        auditor_relation = AuditCycleAuditor(
            audit_cycle_id=audit_cycle.id,
            auditor_employee_id=manager_mark.id
        )
        session.add(auditor_relation)
        session.flush()

        print("Seeding audit items...")
        # Add assets that are currently in Engineering (AF-0002 Dell, AF-0006 ThinkPad, and AF-0007 Lost iPad)
        item_dell = AuditItem(
            audit_cycle_id=audit_cycle.id,
            asset_id=asset_dell.id,
            verification_status="verified",
            notes="Laptop inspected by Mark. Physical condition matches records.",
            verified_by_employee_id=manager_mark.id,
            verified_at=datetime.utcnow() - timedelta(days=1)
        )
        
        item_thinkpad = AuditItem(
            audit_cycle_id=audit_cycle.id,
            asset_id=asset_thinkpad.id,
            verification_status="pending"
        )
        
        item_ipad = AuditItem(
            audit_cycle_id=audit_cycle.id,
            asset_id=asset_ipad.id,
            verification_status="missing",
            notes="Could not locate iPad in office lockers or desk space. Raj reports he hasn't had it in two weeks.",
            verified_by_employee_id=manager_mark.id,
            verified_at=datetime.utcnow() - timedelta(days=1)
        )
        session.add_all([item_dell, item_thinkpad, item_ipad])
        session.flush()

        print("Seeding notifications...")
        notif_overdue = Notification(
            employee_id=emp_raj.id,
            type="overdue_return",
            title="Overdue Asset Return Alert",
            message="Your expected return date for ThinkPad T14 (AF-0006) was yesterday. Please return it or contact Mark Manager to request an extension.",
            is_read=False
        )
        notif_maint = Notification(
            employee_id=head_dave.id,
            type="maintenance_approved",
            title="Tesla Maintenance Approved",
            message="Your maintenance request for the Tesla Model 3 (AF-0005) has been approved. The vehicle is scheduled for Apex Auto Care technician assignment.",
            is_read=True
        )
        session.add_all([notif_overdue, notif_maint])
        
        print("Seeding activity logs...")
        log1 = ActivityLog(
            employee_id=admin_alice.id,
            action="CREATE_ASSET",
            details={"asset_tag": "AF-0001", "name": "MacBook Pro M3 Max"}
        )
        log2 = ActivityLog(
            employee_id=manager_mark.id,
            action="ALLOCATE_ASSET",
            details={"asset_tag": "AF-0006", "employee_email": "raj@assetflow.com"}
        )
        session.add_all([log1, log2])

        session.commit()
        print("Database successfully seeded!")
        
    except Exception as e:
        session.rollback()
        print(f"Error during seeding: {e}", file=sys.stderr)
        raise e
    finally:
        session.close()

if __name__ == "__main__":
    seed_database()
