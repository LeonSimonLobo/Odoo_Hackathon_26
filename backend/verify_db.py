import unittest
from datetime import datetime, date, timedelta
from database import Base, engine, SessionLocal
from models import (
    Department, Employee, AssetCategory, Asset, AssetAllocation,
    TransferRequest, Resource, ResourceBooking, MaintenanceRequest,
    AuditCycle, AuditItem, Notification, ActivityLog
)
from seed import seed_database

class TestAssetFlowDatabase(unittest.TestCase):
    
    def setUp(self):
        # Always run seed_database to get a fresh, populated database
        seed_database()
        self.session = SessionLocal()

    def tearDown(self):
        self.session.close()

    def test_double_allocation_prevention(self):
        """Test that the database prevents double-allocating a single asset"""
        print("\n--- Running Test: Double Allocation Prevention ---")
        
        # Dell XPS 15 (AF-0002) is already allocated to Priya Patel in the seed data
        asset_dell = self.session.query(Asset).filter_by(asset_tag="AF-0002").first()
        self.assertIsNotNone(asset_dell)
        self.assertEqual(asset_dell.status, "allocated")

        # Raj Kumar tries to allocate the same Dell XPS 15 laptop
        emp_raj = self.session.query(Employee).filter_by(email="raj@assetflow.com").first()
        mgr_mark = self.session.query(Employee).filter_by(role="asset_manager").first()
        
        double_alloc = AssetAllocation(
            asset_id=asset_dell.id,
            allocated_to_type="employee",
            allocated_employee_id=emp_raj.id,
            allocated_by_id=mgr_mark.id,
            allocation_date=datetime.utcnow(),
            status="active"
        )
        
        self.session.add(double_alloc)
        
        # Verify that committing/flushing raises ValueError
        with self.assertRaises(ValueError) as context:
            self.session.flush()
        
        print(f"Captured double-allocation error message: {context.exception}")
        self.assertIn("Conflict: Asset", str(context.exception))
        self.assertIn("is already allocated", str(context.exception))
        self.session.rollback()

    def test_booking_overlap_validation(self):
        """Test time-slot bookings overlap rules matching the problem statement"""
        print("\n--- Running Test: Booking Overlap Validation ---")
        
        # Fetch Room B2 resource
        room_b2 = self.session.query(Resource).filter_by(name="Conference Room B2").first()
        self.assertIsNotNone(room_b2)
        
        # In seed data, Room B2 is booked today 14:00 - 15:00 by Raj Kumar
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        emp_john = self.session.query(Employee).filter_by(email="john@assetflow.com").first()

        # Test Case 1: Overlapping booking (14:30 - 15:30) -> Should fail
        overlap_booking = ResourceBooking(
            resource_id=room_b2.id,
            booked_by_employee_id=emp_john.id,
            start_time=today + timedelta(hours=14, minutes=30),
            end_time=today + timedelta(hours=15, minutes=30),
            status="upcoming"
        )
        self.session.add(overlap_booking)
        
        with self.assertRaises(ValueError) as context:
            self.session.flush()
        
        print(f"Captured overlapping booking error message: {context.exception}")
        self.assertIn("Conflict: Resource", str(context.exception))
        self.assertIn("is already booked", str(context.exception))
        self.session.rollback()

        # Test Case 2: Adjacent non-overlapping booking (15:00 - 16:00) -> Should succeed
        valid_booking = ResourceBooking(
            resource_id=room_b2.id,
            booked_by_employee_id=emp_john.id,
            start_time=today + timedelta(hours=15),
            end_time=today + timedelta(hours=16),
            status="upcoming"
        )
        self.session.add(valid_booking)
        self.session.commit()
        print("Success: Adjacent booking at 15:00 committed successfully!")
        
        # Verify it exists in database
        db_booking = self.session.query(ResourceBooking).filter_by(id=valid_booking.id).first()
        self.assertIsNotNone(db_booking)

    def test_maintenance_lifecycle(self):
        """Test status changes during maintenance requests approvals and resolutions"""
        print("\n--- Running Test: Maintenance Lifecycle Transitions ---")
        
        # Macbook Pro M3 (AF-0001) is currently 'available'
        macbook = self.session.query(Asset).filter_by(asset_tag="AF-0001").first()
        self.assertEqual(macbook.status, "available")

        # Find the pending request we seeded
        req = self.session.query(MaintenanceRequest).filter_by(asset_id=macbook.id, status="pending").first()
        self.assertIsNotNone(req)

        # Mark request as approved
        req.status = "approved"
        self.session.flush()

        # Verify asset status updated to under_maintenance
        self.session.refresh(macbook)
        self.assertEqual(macbook.status, "under_maintenance")
        print("Success: Asset transitioned to 'under_maintenance' on request approval.")

        # Resolve maintenance
        req.status = "resolved"
        req.resolution_notes = "Screen assembly replaced. Fully functional."
        self.session.flush()

        # Verify asset status reverted to available
        self.session.refresh(macbook)
        self.assertEqual(macbook.status, "available")
        print("Success: Asset transitioned back to 'available' on request resolution.")

    def test_audit_cycle_lock_lost_transition(self):
        """Test that closing an audit cycle updates missing assets to lost"""
        print("\n--- Running Test: Audit Cycle Close & Asset Lost Transition ---")
        
        # Find the open audit cycle
        cycle = self.session.query(AuditCycle).filter_by(status="open").first()
        self.assertIsNotNone(cycle)
        
        # Find the iPad Air asset (AF-0007), which has a 'missing' audit item in this cycle
        ipad = self.session.query(Asset).filter_by(asset_tag="AF-0007").first()
        self.assertIsNotNone(ipad)
        
        # Set its status to 'available' to verify transition upon closing the audit
        ipad.status = "available"
        self.session.commit()
        
        # Close the cycle
        cycle.status = "closed"
        self.session.commit()

        # Verify that the asset status has transitioned to 'lost'
        self.session.refresh(ipad)
        self.assertEqual(ipad.status, "lost")
        print("Success: Confirmed-missing items automatically marked as 'lost' on audit cycle lock.")

    def test_dashboard_kpi_queries(self):
        """Verify the database query logic for the Screen 2 KPI dashboard metrics"""
        print("\n--- Running Test: Dashboard KPI Queries ---")
        
        # 1. Assets Available
        avail_count = self.session.query(Asset).filter_by(status="available").count()
        
        # 2. Assets Allocated
        alloc_count = self.session.query(Asset).filter_by(status="allocated").count()
        
        # 3. Under Maintenance Today
        maint_count = self.session.query(Asset).filter_by(status="under_maintenance").count()
        
        # 4. Active Bookings
        active_bookings = self.session.query(ResourceBooking).filter(
            ResourceBooking.status.in_(["upcoming", "ongoing"])
        ).count()
        
        # 5. Pending Transfers
        pending_transfers = self.session.query(TransferRequest).filter_by(status="pending").count()
        
        # 6. Overdue Returns (return date past current time and status = active)
        now_time = datetime.utcnow()
        overdue_returns = self.session.query(AssetAllocation).filter(
            AssetAllocation.status == "active",
            AssetAllocation.expected_return_date < now_time
        ).count()

        print(f"Dashboard Operational Snapshots:")
        print(f"  - Assets Available: {avail_count}")
        print(f"  - Assets Allocated: {alloc_count}")
        print(f"  - Under Maintenance Today: {maint_count}")
        print(f"  - Active Bookings: {active_bookings}")
        print(f"  - Pending Transfers: {pending_transfers}")
        print(f"  - Overdue Returns: {overdue_returns}")

        # Assert correct count from seed data
        # Dell (AF-0002) and ThinkPad (AF-0006) are allocated = 2
        self.assertEqual(alloc_count, 2)
        # ThinkPad is overdue = 1
        self.assertEqual(overdue_returns, 1)
        # Tesla is under maintenance = 1
        self.assertEqual(maint_count, 1)
        # Transfer request for ThinkPad is pending = 1
        self.assertEqual(pending_transfers, 1)

if __name__ == '__main__':
    unittest.main()
