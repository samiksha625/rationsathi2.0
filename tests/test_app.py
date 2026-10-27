import os
import tempfile
import unittest
import app as ration_app

class RationSathiTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(delete=False)
        self.tmp.close()
        ration_app.DATABASE = self.tmp.name
        ration_app.app.config["TESTING"] = True
        ration_app.init_db()
        self.client = ration_app.app.test_client()

    def tearDown(self):
        try:
            os.unlink(self.tmp.name)
        except OSError:
            pass

    def login(self, username, password):
        return self.client.post("/login", data={"username": username, "password": password}, follow_redirects=True)

    def test_root_redirects_to_login(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 302)
        self.assertIn(b"/login", response.data)

    def test_invalid_login(self):
        response = self.login("admin", "wrong")
        self.assertIn(b"Invalid username or password", response.data)

    def test_operator_can_open_dashboard(self):
        response = self.login("operator", "Operator@123")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Dashboard", response.data)

    def test_beneficiary_cannot_open_stock_page(self):
        self.login("beneficiary", "User@123")
        response = self.client.get("/stock", follow_redirects=True)
        self.assertIn(b"do not have permission", response.data)

    def test_distribution_updates_stock(self):
        self.login("operator", "Operator@123")
        with ration_app.app.app_context():
            before = ration_app.get_db().execute("SELECT quantity_kg FROM stock WHERE commodity='Rice'").fetchone()[0]
        response = self.client.post("/distribute", data={
            "card_number":"TN-1001", "commodity":"Rice", "quantity_kg":"5"
        }, follow_redirects=True)
        self.assertIn(b"Distribution recorded", response.data)
        with ration_app.app.app_context():
            after = ration_app.get_db().execute("SELECT quantity_kg FROM stock WHERE commodity='Rice'").fetchone()[0]
        self.assertAlmostEqual(before - after, 5.0)

    def test_distribution_rejects_excess_stock(self):
        self.login("operator", "Operator@123")
        response = self.client.post("/distribute", data={
            "card_number":"TN-1001", "commodity":"Rice", "quantity_kg":"999999"
        }, follow_redirects=True)
        self.assertIn(b"Insufficient stock", response.data)

    def test_beneficiary_can_submit_complaint(self):
        self.login("beneficiary", "User@123")
        response = self.client.post("/complaints", data={
            "category":"Quantity discrepancy", "description":"Sample test complaint"
        }, follow_redirects=True)
        self.assertIn(b"Complaint submitted successfully", response.data)

if __name__ == "__main__":
    unittest.main()
