import unittest
import os
import sqlite3
import json
from app import app, DB_PATH

class ShopEasyTestCase(unittest.TestCase):

    def setUp(self):
        # Configure app for testing
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()
        
        # Verify db exists
        self.assertTrue(os.path.exists(DB_PATH), "Database file 'shop.db' must exist.")

        # Clear cart, wishlist, and orders to isolate tests from manual browser states
        conn = sqlite3.connect(DB_PATH)
        conn.execute('DELETE FROM cart')
        conn.execute('DELETE FROM wishlist')
        conn.execute('DELETE FROM orders')
        conn.execute('DELETE FROM order_items')
        conn.commit()
        conn.close()

    def test_home_page(self):
        """Test that the homepage renders successfully."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'ShopEasy', response.data)
        self.assertIn(b'Featured Products', response.data)

    def test_category_page(self):
        """Test that categories show products and handle sorting parameters."""
        response = self.client.get('/category/mobiles')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Mobiles', response.data)
        
        # Test sorting query param
        response_sort = self.client.get('/category/mobiles?sort_by=price_asc')
        self.assertEqual(response_sort.status_code, 200)

    def test_product_detail_page(self):
        """Test product page is loading and returns specs."""
        # Grab first product ID from db
        conn = sqlite3.connect(DB_PATH)
        row = conn.execute('SELECT id, name FROM products LIMIT 1').fetchone()
        conn.close()
        
        if row:
            product_id = row[0]
            name = row[1]
            response = self.client.get(f'/product/{product_id}')
            self.assertEqual(response.status_code, 200)
            self.assertIn(name.encode('utf-8', errors='ignore')[:15], response.data)
        else:
            self.skipTest("No products seeded in database, skipping product detail test.")

    def test_search_endpoint(self):
        """Test the live search suggestions endpoint."""
        response = self.client.get('/api/search?q=iPhone')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIsInstance(data, list)
        if len(data) > 0:
            self.assertIn('name', data[0])
            self.assertTrue(any('iPhone' in item['name'] for item in data))

    def test_login_page_renders(self):
        """Test that the login page loads."""
        response = self.client.get('/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Sign In', response.data)
        self.assertIn(b'Create Account', response.data)

    def test_authentication_flow(self):
        """Test logging in with seeded user credentials."""
        # Standard user is seeded in db_init with user / user123
        response = self.client.post('/login', data={
            'action': 'login',
            'username_or_email': 'user',
            'password': 'user123'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Welcome, user', response.data)

    def test_admin_restriction(self):
        """Test that regular users or guest visitors cannot access the admin page."""
        # 1. Unauthenticated guest check
        response_guest = self.client.get('/admin', follow_redirects=True)
        self.assertIn(b'Please log in to continue.', response_guest.data)

        # 2. Regular user logged in check
        with self.client.session_transaction() as sess:
            sess['user_id'] = 2 # standard 'user' id
        response_user = self.client.get('/admin', follow_redirects=True)
        self.assertIn(b'Administrator privileges required.', response_user.data)

    def test_admin_access_and_stock_updates(self):
        """Test admin login and API operations."""
        # Login as admin
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1 # 'admin' user id

        # Verify dashboard page loads
        response_admin = self.client.get('/admin')
        self.assertEqual(response_admin.status_code, 200)
        self.assertIn(b'Administrator Control Panel', response_admin.data)
        
        # Test product stock adjustment via API
        response_stock = self.client.post('/api/admin/product/stock', data=json.dumps({
            'product_id': 1,
            'stock': 45
        }), content_type='application/json')
        self.assertEqual(response_stock.status_code, 200)
        data = json.loads(response_stock.data)
        self.assertTrue(data['success'])
        
        # Verify changes in database
        conn = sqlite3.connect(DB_PATH)
        row = conn.execute('SELECT stock FROM products WHERE id = 1').fetchone()
        conn.close()
        self.assertEqual(row[0], 45)

    def test_wishlist_operations(self):
        """Test toggling items in wishlist and loading the wishlist page."""
        # 1. Unauthenticated toggle attempt should return 401
        res = self.client.post('/api/wishlist/toggle', data=json.dumps({
            'product_id': 1
        }), content_type='application/json')
        self.assertEqual(res.status_code, 401)

        # 2. Login as regular user
        with self.client.session_transaction() as sess:
            sess['user_id'] = 2 # standard user

        # Toggle product 1 (should add)
        res_add = self.client.post('/api/wishlist/toggle', data=json.dumps({
            'product_id': 1
        }), content_type='application/json')
        self.assertEqual(res_add.status_code, 200)
        data_add = json.loads(res_add.data)
        self.assertEqual(data_add['state'], 'added')
        self.assertEqual(data_add['wishlist_count'], 1)

        # Fetch wishlist page
        res_page = self.client.get('/wishlist')
        self.assertEqual(res_page.status_code, 200)
        self.assertIn(b'My Wishlist', res_page.data)
        self.assertIn(b'Apple iPhone 16 Pro Max', res_page.data)

        # Toggle product 1 again (should remove)
        res_remove = self.client.post('/api/wishlist/toggle', data=json.dumps({
            'product_id': 1
        }), content_type='application/json')
        self.assertEqual(res_remove.status_code, 200)
        data_remove = json.loads(res_remove.data)
        self.assertEqual(data_remove['state'], 'removed')
        self.assertEqual(data_remove['wishlist_count'], 0)

    def test_checkout_coupons(self):
        """Test applying promo coupons and validating discounts."""
        with self.client.session_transaction() as sess:
            sess['user_id'] = 2 # standard user

        # 1. Cart is empty, coupon application should fail
        res_fail = self.client.post('/api/checkout/coupon', data=json.dumps({
            'promo_code': 'SE10'
        }), content_type='application/json')
        self.assertEqual(res_fail.status_code, 400)
        
        # 2. Add an item to cart (iPhone 16 Pro Max, price = 144,999)
        self.client.post('/api/cart/add', data=json.dumps({
            'product_id': 1,
            'quantity': 1
        }), content_type='application/json')

        # 3. Apply SE10 coupon (10% off)
        res_se10 = self.client.post('/api/checkout/coupon', data=json.dumps({
            'promo_code': 'SE10'
        }), content_type='application/json')
        self.assertEqual(res_se10.status_code, 200)
        data_se10 = json.loads(res_se10.data)
        self.assertTrue(data_se10['success'])
        # Subtotal: 144999. Base discount (5%): 7249. Coupon discount (10%): 14499.
        self.assertEqual(data_se10['coupon_discount'], 14499)
        self.assertEqual(data_se10['total_discount'], 7249 + 14499)

        # 4. Apply SUPER500 coupon (flat 500 off)
        res_super500 = self.client.post('/api/checkout/coupon', data=json.dumps({
            'promo_code': 'SUPER500'
        }), content_type='application/json')
        self.assertEqual(res_super500.status_code, 200)
        data_super500 = json.loads(res_super500.data)
        self.assertTrue(data_super500['success'])
        self.assertEqual(data_super500['coupon_discount'], 500)

if __name__ == '__main__':
    unittest.main()
