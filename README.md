# ShopEasy E-Commerce Website

A premium, modern E-Commerce web application built using **Python**, **Flask**, and **SQLite**. 

## Features
* **Product Catalog**: Multi-category support (Mobiles, Laptops, Fashion, Electronics, Home & Kitchen, Toys & Games).
* **Live Search**: Autocomplete search suggestions with price display and dynamic routing.
* **Filtering & Sorting**: Fast filtering by price range and sorting by popularity, price, or rating.
* **Shopping Cart**: Real-time quantity adjustments and order summaries with discount coupons support.
* **Wishlist**: Toggle items to save them for later.
* **Checkout & Orders**: Secure simulated order checkout processing and tracking.
* **Admin Dashboard**: Control center for tracking revenue, monitoring low-stock items, adjusting inventory, and updating delivery statuses.

---

## Getting Started

### Prerequisites
* Python 3.x
* Flask (`pip install Flask`)

### Installation & Setup

1. **Initialize the Database**:
   Seed the database with mock products, users, and admin accounts:
   ```bash
   python db_init.py
   ```

2. **Run the Application**:
   Start the local Flask development server:
   ```bash
   python app.py
   ```
   Open your browser and navigate to `http://127.0.0.1:5000`.

3. **Running Tests**:
   Verify everything is working correctly by executing the unit test suite:
   ```bash
   python test_app.py
   ```

---

## Author & Contact Details
* **Name**: D.Yeswanth Kumar
* **Email**: dyeswanth1005@gmail.com
