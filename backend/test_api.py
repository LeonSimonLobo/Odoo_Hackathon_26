import unittest
from fastapi.testclient import TestClient
from main import app
from database import SessionLocal, Base, engine
from models import Employee, Department, AssetCategory

class TestAssetFlowAPI(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Create test tables
        Base.metadata.create_all(bind=engine)
        cls.client = TestClient(app)

    def setUp(self):
        # Clean up database data before each test
        self.db = SessionLocal()
        self.db.query(Department).delete()
        self.db.query(Employee).delete()
        self.db.query(AssetCategory).delete()
        self.db.commit()

        # Seed initial test employee
        self.test_emp = Employee(
            name="Bob Builder",
            email="bob@builder.com",
            password_hash="hashed_pw",
            role="employee",
            status="active"
        )
        self.db.add(self.test_emp)
        self.db.commit()
        self.db.refresh(self.test_emp)

    def tearDown(self):
        self.db.close()

    def test_get_departments_empty(self):
        """Test getting departments list when empty"""
        response = self.client.get("/api/departments")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_create_department_and_auto_promote(self):
        """Test department creation and auto-promotion of department head role"""
        # Create department with Bob Builder as head
        dept_data = {
            "name": "Construction",
            "parent_department_id": None,
            "department_head_id": self.test_emp.id,
            "status": "active"
        }
        
        response = self.client.post("/api/departments", json=dept_data)
        self.assertEqual(response.status_code, 201)
        
        res_data = response.json()
        self.assertEqual(res_data["name"], "Construction")
        self.assertEqual(res_data["department_head_name"], "Bob Builder")
        
        # Verify employee role is auto-promoted to department_head in directory
        self.db.refresh(self.test_emp)
        self.assertEqual(self.test_emp.role, "department_head")
        self.assertEqual(self.test_emp.department_id, res_data["id"])

    def test_category_endpoints_with_json_schema(self):
        """Test category creation and dynamic schema fields"""
        cat_data = {
            "name": "Electronics",
            "description": "Electronic gadgets",
            "schema_attributes": {
                "warranty_months": 24,
                "voltage": "220V"
            }
        }
        
        # Post category
        response = self.client.post("/api/categories", json=cat_data)
        self.assertEqual(response.status_code, 201)
        res_data = response.json()
        self.assertEqual(res_data["name"], "Electronics")
        self.assertEqual(res_data["schema_attributes"]["warranty_months"], 24)

        # Get categories
        response = self.client.get("/api/categories")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]["name"], "Electronics")

    def test_employee_directory_role_promotion(self):
        """Test promoting employee role via API endpoint"""
        # Verify initial role
        self.assertEqual(self.test_emp.role, "employee")
        
        # Promote role to asset_manager
        promo_data = {"role": "asset_manager"}
        response = self.client.put(f"/api/employees/{self.test_emp.id}/role", json=promo_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["role"], "asset_manager")
        
        # Verify in DB
        self.db.refresh(self.test_emp)
        self.assertEqual(self.test_emp.role, "asset_manager")

    def test_employee_status_toggle(self):
        """Test deactivating employee status via API endpoint"""
        # Deactivate employee
        status_data = {"status": "inactive"}
        response = self.client.put(f"/api/employees/{self.test_emp.id}/status", json=status_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "inactive")

        # Verify in DB
        self.db.refresh(self.test_emp)
        self.assertEqual(self.test_emp.status, "inactive")

if __name__ == '__main__':
    unittest.main()
