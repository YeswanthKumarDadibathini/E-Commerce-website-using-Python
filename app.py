import sqlite3
import json
import os
import functools
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, g, jsonify, flash

app = Flask(__name__)
app.secret_key = 'shopeasy_secret_key_change_in_production'

DB_PATH = 'shop.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DB_PATH)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# Template filter to format numbers as currency (e.g. 144999 -> ₹1,44,999)
@app.template_filter('format_price')
def format_price(value):
    try:
        return f"₹{int(value):,}"
    except (ValueError, TypeError):
        return f"₹{value}"

# Load user details before each request
@app.before_request
def load_logged_in_user():
    user_id = session.get('user_id')
    if user_id is None:
        g.user = None
    else:
        db = get_db()
        g.user = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()

    # Get cart count for the header
    g.cart_count = 0
    if g.user:
        db = get_db()
        row = db.execute('SELECT SUM(quantity) as count FROM cart WHERE user_id = ?', (g.user['id'],)).fetchone()
        if row and row['count']:
            g.cart_count = row['count']

    # Get wishlist count and wishlisted product IDs globally
    g.wishlist_count = 0
    g.wishlist_item_ids = []
    if g.user:
        db = get_db()
        row = db.execute('SELECT COUNT(*) as count FROM wishlist WHERE user_id = ?', (g.user['id'],)).fetchone()
        if row and row['count']:
            g.wishlist_count = row['count']
        
        wish_rows = db.execute('SELECT product_id FROM wishlist WHERE user_id = ?', (g.user['id'],)).fetchall()
        g.wishlist_item_ids = [r['product_id'] for r in wish_rows]

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            flash('Please log in to continue.', 'warning')
            return redirect(url_for('login', next=request.url))
        return view(**kwargs)
    return wrapped_view

def admin_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            flash('Please log in to continue.', 'warning')
            return redirect(url_for('login', next=request.url))
        if not g.user['is_admin']:
            flash('Access denied. Administrator privileges required.', 'danger')
            return redirect(url_for('index'))
        return view(**kwargs)
    return wrapped_view

# --- PAGE ROUTES ---

@app.route('/')
def index():
    db = get_db()
    # Fetch 6 featured products (diverse categories)
    featured = db.execute('SELECT * FROM products ORDER BY rating DESC LIMIT 6').fetchall()
    # Fetch 4 top deals (cheaper items or popular categories)
    top_deals = db.execute('SELECT * FROM products ORDER BY price ASC LIMIT 4').fetchall()
    return render_template('index.html', featured=featured, top_deals=top_deals)

@app.route('/category/<cat_name>')
def category(cat_name):
    db = get_db()
    
    # Get filters from query parameters
    sort_by = request.args.get('sort_by', 'popular')
    min_price = request.args.get('min_price', type=int)
    max_price = request.args.get('max_price', type=int)
    q = request.args.get('q', '').strip()
    
    query = 'SELECT * FROM products WHERE category = ?'
    params = [cat_name]
    
    if min_price is not None:
        query += ' AND price >= ?'
        params.append(min_price)
    if max_price is not None:
        query += ' AND price <= ?'
        params.append(max_price)
    if q:
        query += ' AND (name LIKE ? OR description LIKE ?)'
        params.append(f'%{q}%')
        params.append(f'%{q}%')
        
    if sort_by == 'price_asc':
        query += ' ORDER BY price ASC'
    elif sort_by == 'price_desc':
        query += ' ORDER BY price DESC'
    elif sort_by == 'rating_desc':
        query += ' ORDER BY rating DESC'
    else:
        # popular / default
        query += ' ORDER BY id ASC'
        
    products = db.execute(query, params).fetchall()
    
    # Get price bounds for filtering display
    bounds = db.execute('SELECT MIN(price) as min_p, MAX(price) as max_p FROM products WHERE category = ?', (cat_name,)).fetchone()
    min_bound = bounds['min_p'] or 0
    max_bound = bounds['max_p'] or 250000

    # Display friendly title
    category_titles = {
        'mobiles': '📱 Smart Phones',
        'laptops': '💻 Laptops',
        'fashion': '👕 Fashion Collection',
        'electronics': '📺 Electronics',
        'home': '🏠 Home & Kitchen',
        'toys': '🧸 Toys & Games'
    }
    title = category_titles.get(cat_name, cat_name.capitalize())
    
    return render_template('category.html', 
                           category=cat_name, 
                           title=title, 
                           products=products,
                           sort_by=sort_by,
                           min_price=min_price,
                           max_price=max_price,
                           min_bound=min_bound,
                           max_bound=max_bound,
                           q=q)

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    db = get_db()
    product = db.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
    if not product:
        flash('Product not found.', 'danger')
        return redirect(url_for('index'))
        
    # Parse specifications from JSON
    try:
        specs = json.loads(product['specifications'])
    except Exception:
        specs = {}
        
    # Get reviews
    reviews = db.execute('SELECT * FROM reviews WHERE product_id = ? ORDER BY id DESC', (product_id,)).fetchall()
    
    # Calculate average rating and count
    avg_rating = product['rating']
    review_count = len(reviews)
    if review_count > 0:
        total_rating = sum(r['rating'] for r in reviews)
        avg_rating = round(total_rating / review_count, 1)
        
    # Fetch related products from same category (excluding current)
    related = db.execute('SELECT * FROM products WHERE category = ? AND id != ? LIMIT 4', 
                         (product['category'], product_id)).fetchall()
                         
    # Check if current product is wishlisted
    is_wishlisted = False
    if g.user:
        is_wishlisted = product_id in g.wishlist_item_ids

    return render_template('product.html', 
                           product=product, 
                           specs=specs, 
                           reviews=reviews, 
                           avg_rating=avg_rating,
                           review_count=review_count,
                           related=related,
                           is_wishlisted=is_wishlisted)

@app.route('/cart')
@login_required
def cart():
    db = get_db()
    items = db.execute('''
        SELECT c.id as cart_id, c.quantity, p.id as product_id, p.name, p.price, p.image_url, p.stock
        FROM cart c
        JOIN products p ON c.product_id = p.id
        WHERE c.user_id = ?
    ''', (g.user['id'],)).fetchall()
    
    # Calculate order summary
    subtotal = sum(item['price'] * item['quantity'] for item in items)
    shipping = 0 if subtotal > 1000 or subtotal == 0 else 99
    discount = int(subtotal * 0.05) # 5% special checkout discount
    total = subtotal - discount + shipping
    
    summary = {
        'subtotal': subtotal,
        'shipping': shipping,
        'discount': discount,
        'total': total,
        'item_count': sum(item['quantity'] for item in items)
    }
    
    return render_template('cart.html', items=items, summary=summary)

@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    db = get_db()
    cart_items = db.execute('''
        SELECT c.quantity, p.id as product_id, p.name, p.price, p.stock
        FROM cart c
        JOIN products p ON c.product_id = p.id
        WHERE c.user_id = ?
    ''', (g.user['id'],)).fetchall()
    
    if not cart_items:
        flash('Your cart is empty!', 'warning')
        return redirect(url_for('cart'))
        
    subtotal = sum(item['price'] * item['quantity'] for item in cart_items)
    shipping = 0 if subtotal > 1000 else 99
    base_discount = int(subtotal * 0.05)
    
    if request.method == 'POST':
        address = request.form.get('address')
        phone = request.form.get('phone')
        payment_method = request.form.get('payment_method')
        promo_code = request.form.get('promo_code', '').strip().upper()
        
        if not address or not phone or not payment_method:
            flash('All checkout fields are required.', 'danger')
            return redirect(url_for('checkout'))
            
        # Check stock again
        for item in cart_items:
            if item['stock'] < item['quantity']:
                flash(f"Sorry, {item['name']} is out of stock or does not have enough quantities.", 'danger')
                return redirect(url_for('cart'))
                
        # Validate coupon discount securely on backend
        coupon_discount = 0
        if promo_code == 'SE10':
            coupon_discount = int(subtotal * 0.10)
        elif promo_code == 'SUPER500' and subtotal >= 2000:
            coupon_discount = 500
            
        total_discount = base_discount + coupon_discount
        final_total = subtotal - total_discount + shipping
        
        # Begin Order Transaction
        cursor = db.cursor()
        date_str = datetime.now().strftime('%Y-%m-%d %H:%M')
        cursor.execute('''
            INSERT INTO orders (user_id, total_price, date, status, address, phone, payment_method)
            VALUES (?, ?, ?, 'Processing', ?, ?, ?)
        ''', (g.user['id'], final_total, date_str, address, phone, payment_method))
        
        order_id = cursor.lastrowid
        
        # Insert items and deduct stock
        for item in cart_items:
            cursor.execute('''
                INSERT INTO order_items (order_id, product_id, quantity, price_at_purchase)
                VALUES (?, ?, ?, ?)
            ''', (order_id, item['product_id'], item['quantity'], item['price']))
            
            cursor.execute('''
                UPDATE products 
                SET stock = stock - ? 
                WHERE id = ?
            ''', (item['quantity'], item['product_id']))
            
        # Clear Cart
        cursor.execute('DELETE FROM cart WHERE user_id = ?', (g.user['id'],))
        db.commit()
        
        flash('Order placed successfully! Thank you for shopping with ShopEasy.', 'success')
        return redirect(url_for('orders'))
        
    total = subtotal - base_discount + shipping
    return render_template('checkout.html', 
                           cart_items=cart_items, 
                           subtotal=subtotal,
                           base_discount=base_discount,
                           shipping=shipping,
                           total=total, 
                           address=g.user['address'], 
                           phone=g.user['phone'])

@app.route('/orders')
@login_required
def orders():
    db = get_db()
    orders_rows = db.execute('''
        SELECT * FROM orders WHERE user_id = ? ORDER BY id DESC
    ''', (g.user['id'],)).fetchall()
    
    orders_list = []
    for order in orders_rows:
        items = db.execute('''
            SELECT oi.quantity, oi.price_at_purchase, p.name, p.image_url, p.id as product_id
            FROM order_items oi
            JOIN products p ON oi.product_id = p.id
            WHERE oi.order_id = ?
        ''', (order['id'],)).fetchall()
        
        orders_list.append({
            'details': order,
            'items': items
        })
        
    return render_template('orders.html', orders=orders_list)

# --- SEARCH ROUTE ---
@app.route('/search')
def search():
    q = request.args.get('q', '').strip()
    if not q:
        return redirect(url_for('index'))
    db = get_db()
    
    # Get filters from query parameters
    sort_by = request.args.get('sort_by', 'popular')
    min_price = request.args.get('min_price', type=int)
    max_price = request.args.get('max_price', type=int)
    
    query = 'SELECT * FROM products WHERE (name LIKE ? OR description LIKE ? OR category LIKE ?)'
    params = [f'%{q}%', f'%{q}%', f'%{q}%']
    
    if min_price is not None:
        query += ' AND price >= ?'
        params.append(min_price)
    if max_price is not None:
        query += ' AND price <= ?'
        params.append(max_price)
        
    if sort_by == 'price_asc':
        query += ' ORDER BY price ASC'
    elif sort_by == 'price_desc':
        query += ' ORDER BY price DESC'
    elif sort_by == 'rating_desc':
        query += ' ORDER BY rating DESC'
    else:
        query += ' ORDER BY id ASC'
        
    products = db.execute(query, params).fetchall()
    
    # Get price bounds for filtering display
    bounds = db.execute('''
        SELECT MIN(price) as min_p, MAX(price) as max_p FROM products 
        WHERE name LIKE ? OR description LIKE ? OR category LIKE ?
    ''', (f'%{q}%', f'%{q}%', f'%{q}%')).fetchone()
    
    min_bound = bounds['min_p'] or 0
    max_bound = bounds['max_p'] or 250000
    
    return render_template('category.html', 
                           category='search', 
                           title=f"Search Results for '{q}'", 
                           products=products,
                           sort_by=sort_by,
                           min_price=min_price,
                           max_price=max_price,
                           min_bound=min_bound,
                           max_bound=max_bound,
                           q=q)

# --- USER AUTHENTICATION ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if g.user:
        return redirect(url_for('index'))
        
    next_url = request.args.get('next') or request.form.get('next')
    
    if request.method == 'POST':
        action = request.form.get('action')
        db = get_db()
        from werkzeug.security import generate_password_hash, check_password_hash
        
        if action == 'register':
            username = request.form.get('username').strip()
            email = request.form.get('email').strip()
            password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')
            address = request.form.get('address').strip()
            phone = request.form.get('phone').strip()
            
            if not username or not email or not password or not confirm_password:
                flash('All fields marked * are required.', 'danger')
                return render_template('login.html', active_tab='register', next=next_url)
                
            if password != confirm_password:
                flash('Passwords do not match.', 'danger')
                return render_template('login.html', active_tab='register', next=next_url)
                
            # Check user duplicate
            user_check = db.execute('SELECT id FROM users WHERE username = ? OR email = ?', (username, email)).fetchone()
            if user_check:
                flash('Username or Email already exists.', 'danger')
                return render_template('login.html', active_tab='register', next=next_url)
                
            # Create user
            pw_hash = generate_password_hash(password)
            cursor = db.cursor()
            cursor.execute('''
                INSERT INTO users (username, password_hash, email, address, phone)
                VALUES (?, ?, ?, ?, ?)
            ''', (username, pw_hash, email, address, phone))
            db.commit()
            
            user_id = cursor.lastrowid
            session['user_id'] = user_id
            flash('Account created successfully!', 'success')
            return redirect(next_url or url_for('index'))
            
        elif action == 'login':
            username_or_email = request.form.get('username_or_email').strip()
            password = request.form.get('password')
            
            if not username_or_email or not password:
                flash('Username/Email and Password are required.', 'danger')
                return render_template('login.html', active_tab='login', next=next_url)
                
            user = db.execute('''
                SELECT * FROM users 
                WHERE username = ? OR email = ?
            ''', (username_or_email, username_or_email)).fetchone()
            
            if user and check_password_hash(user['password_hash'], password):
                session['user_id'] = user['id']
                flash(f'Welcome back, {user["username"]}!', 'success')
                return redirect(next_url or url_for('index'))
            else:
                flash('Invalid username/email or password.', 'danger')
                return render_template('login.html', active_tab='login', next=next_url)
                
    return render_template('login.html', active_tab='login', next=next_url)

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('index'))

# --- AJAX/REST API ENDPOINTS ---

@app.route('/api/cart/add', methods=['POST'])
def api_cart_add():
    if not g.user:
        return jsonify({'error': 'unauthorized', 'message': 'Please log in to add items to your cart.'}), 401
        
    data = request.get_json() or {}
    product_id = data.get('product_id')
    quantity = int(data.get('quantity', 1))
    
    if not product_id:
        return jsonify({'error': 'bad_request', 'message': 'Product ID is missing.'}), 400
        
    db = get_db()
    # Check product stock
    product = db.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
    if not product:
        return jsonify({'error': 'not_found', 'message': 'Product not found.'}), 404
        
    if product['stock'] <= 0:
        return jsonify({'error': 'out_of_stock', 'message': 'This product is currently out of stock.'}), 400
        
    # Check if already in cart
    cart_item = db.execute('SELECT * FROM cart WHERE user_id = ? AND product_id = ?', 
                           (g.user['id'], product_id)).fetchone()
                           
    if cart_item:
        new_qty = cart_item['quantity'] + quantity
        if new_qty > product['stock']:
            new_qty = product['stock'] # cap at stock level
        db.execute('UPDATE cart SET quantity = ? WHERE id = ?', (new_qty, cart_item['id']))
    else:
        if quantity > product['stock']:
            quantity = product['stock']
        db.execute('INSERT INTO cart (user_id, product_id, quantity) VALUES (?, ?, ?)',
                   (g.user['id'], product_id, quantity))
                   
    db.commit()
    
    # Get updated total items in cart
    row = db.execute('SELECT SUM(quantity) as count FROM cart WHERE user_id = ?', (g.user['id'],)).fetchone()
    count = row['count'] or 0
    
    return jsonify({
        'success': True,
        'message': f"Added '{product['name']}' to cart.",
        'cart_count': count
    })

@app.route('/api/cart/update', methods=['POST'])
def api_cart_update():
    if not g.user:
        return jsonify({'error': 'unauthorized'}), 401
        
    data = request.get_json() or {}
    product_id = data.get('product_id')
    quantity = int(data.get('quantity'))
    
    if not product_id or quantity is None or quantity < 1:
        return jsonify({'error': 'bad_request'}), 400
        
    db = get_db()
    # Check stock
    product = db.execute('SELECT stock, price FROM products WHERE id = ?', (product_id,)).fetchone()
    if not product:
        return jsonify({'error': 'not_found'}), 404
        
    if quantity > product['stock']:
        quantity = product['stock']
        capped = True
    else:
        capped = False
        
    db.execute('UPDATE cart SET quantity = ? WHERE user_id = ? AND product_id = ?',
               (quantity, g.user['id'], product_id))
    db.commit()
    
    # Calculate new totals
    items = db.execute('''
        SELECT c.quantity, p.price
        FROM cart c
        JOIN products p ON c.product_id = p.id
        WHERE c.user_id = ?
    ''', (g.user['id'],)).fetchall()
    
    subtotal = sum(item['price'] * item['quantity'] for item in items)
    shipping = 0 if subtotal > 1000 or subtotal == 0 else 99
    discount = int(subtotal * 0.05)
    total = subtotal - discount + shipping
    cart_count = sum(item['quantity'] for item in items)
    
    return jsonify({
        'success': True,
        'quantity': quantity,
        'capped': capped,
        'item_total': product['price'] * quantity,
        'subtotal': subtotal,
        'shipping': shipping,
        'discount': discount,
        'total': total,
        'cart_count': cart_count
    })

@app.route('/api/cart/remove', methods=['POST'])
def api_cart_remove():
    if not g.user:
        return jsonify({'error': 'unauthorized'}), 401
        
    data = request.get_json() or {}
    product_id = data.get('product_id')
    
    if not product_id:
        return jsonify({'error': 'bad_request'}), 400
        
    db = get_db()
    db.execute('DELETE FROM cart WHERE user_id = ? AND product_id = ?', (g.user['id'], product_id))
    db.commit()
    
    # Calculate new totals
    items = db.execute('''
        SELECT c.quantity, p.price
        FROM cart c
        JOIN products p ON c.product_id = p.id
        WHERE c.user_id = ?
    ''', (g.user['id'],)).fetchall()
    
    subtotal = sum(item['price'] * item['quantity'] for item in items)
    shipping = 0 if subtotal > 1000 or subtotal == 0 else 99
    discount = int(subtotal * 0.05)
    total = subtotal - discount + shipping
    cart_count = sum(item['quantity'] for item in items)
    
    return jsonify({
        'success': True,
        'subtotal': subtotal,
        'shipping': shipping,
        'discount': discount,
        'total': total,
        'cart_count': cart_count,
        'is_empty': len(items) == 0
    })

@app.route('/api/product/<int:product_id>/review', methods=['POST'])
@login_required
def api_add_review(product_id):
    rating = request.form.get('rating', type=int)
    comment = request.form.get('comment', '').strip()
    
    if not rating or not comment or rating < 1 or rating > 5:
        flash('Invalid rating score or empty comment.', 'danger')
        return redirect(url_for('product_detail', product_id=product_id))
        
    db = get_db()
    date_str = datetime.now().strftime('%Y-%m-%d')
    
    db.execute('''
        INSERT INTO reviews (product_id, user_id, username, rating, comment, date)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (product_id, g.user['id'], g.user['username'], rating, comment, date_str))
    
    # Recalculate and cache average rating in products table
    reviews = db.execute('SELECT rating FROM reviews WHERE product_id = ?', (product_id,)).fetchall()
    avg_rating = round(sum(r['rating'] for r in reviews) / len(reviews), 1)
    db.execute('UPDATE products SET rating = ? WHERE id = ?', (avg_rating, product_id))
    
    db.commit()
    flash('Review submitted successfully!', 'success')
    return redirect(url_for('product_detail', product_id=product_id))

@app.route('/api/search')
def api_search():
    q = request.args.get('q', '').strip()
    if len(q) < 2:
        return jsonify([])
        
    db = get_db()
    products = db.execute('''
        SELECT id, name, category, price, image_url 
        FROM products 
        WHERE name LIKE ? OR description LIKE ?
        LIMIT 5
    ''', (f'%{q}%', f'%{q}%')).fetchall()
    
    results = []
    for p in products:
        results.append({
            'id': p['id'],
            'name': p['name'],
            'category': p['category'],
            'price': p['price'],
            'image_url': p['image_url']
        })
        
    return jsonify(results)

# --- WISHLIST & CHECKOUT COUPONS ---

@app.route('/wishlist')
@login_required
def wishlist():
    db = get_db()
    products = db.execute('''
        SELECT p.* FROM wishlist w
        JOIN products p ON w.product_id = p.id
        WHERE w.user_id = ?
        ORDER BY w.id DESC
    ''', (g.user['id'],)).fetchall()
    return render_template('wishlist.html', products=products)

@app.route('/api/wishlist/toggle', methods=['POST'])
def api_wishlist_toggle():
    if not g.user:
        return jsonify({'error': 'unauthorized', 'message': 'Please log in to save items to your wishlist.'}), 401
        
    data = request.get_json() or {}
    product_id = data.get('product_id')
    
    if not product_id:
        return jsonify({'error': 'bad_request', 'message': 'Product ID is missing.'}), 400
        
    db = get_db()
    product = db.execute('SELECT name FROM products WHERE id = ?', (product_id,)).fetchone()
    if not product:
        return jsonify({'error': 'not_found', 'message': 'Product not found.'}), 404
        
    # Check if already wishlisted
    row = db.execute('SELECT id FROM wishlist WHERE user_id = ? AND product_id = ?',
                     (g.user['id'], product_id)).fetchone()
                     
    if row:
        db.execute('DELETE FROM wishlist WHERE id = ?', (row['id'],))
        state = 'removed'
        message = f"Removed '{product['name']}' from wishlist."
    else:
        db.execute('INSERT INTO wishlist (user_id, product_id) VALUES (?, ?)',
                   (g.user['id'], product_id))
        state = 'added'
        message = f"Added '{product['name']}' to wishlist."
        
    db.commit()
    
    # Calculate updated count
    row_count = db.execute('SELECT COUNT(*) as count FROM wishlist WHERE user_id = ?', (g.user['id'],)).fetchone()
    count = row_count['count'] or 0
    
    return jsonify({
        'success': True,
        'state': state,
        'message': message,
        'wishlist_count': count
    })

@app.route('/api/checkout/coupon', methods=['POST'])
def api_checkout_coupon():
    if not g.user:
        return jsonify({'error': 'unauthorized'}), 401
        
    data = request.get_json() or {}
    promo_code = data.get('promo_code', '').strip().upper()
    
    if not promo_code:
        return jsonify({'error': 'bad_request', 'message': 'Coupon code is missing.'}), 400
        
    db = get_db()
    # Get cart subtotal
    cart_items = db.execute('''
        SELECT c.quantity, p.price
        FROM cart c
        JOIN products p ON c.product_id = p.id
        WHERE c.user_id = ?
    ''', (g.user['id'],)).fetchall()
    
    if not cart_items:
        return jsonify({'error': 'empty_cart', 'message': 'Your cart is empty.'}), 400
        
    subtotal = sum(item['price'] * item['quantity'] for item in cart_items)
    shipping = 0 if subtotal > 1000 else 99
    base_discount = int(subtotal * 0.05)
    
    coupon_discount = 0
    if promo_code == 'SE10':
        coupon_discount = int(subtotal * 0.10)
        msg = "Coupon 'SE10' applied successfully! Extra 10% discount."
    elif promo_code == 'SUPER500':
        if subtotal >= 2000:
            coupon_discount = 500
            msg = "Coupon 'SUPER500' applied successfully! Flat ₹500 discount."
        else:
            return jsonify({'error': 'invalid_code', 'message': 'Coupon SUPER500 requires a minimum order of ₹2,000.'}), 400
    else:
        return jsonify({'error': 'invalid_code', 'message': 'Invalid coupon code.'}), 400
        
    total_discount = base_discount + coupon_discount
    final_total = subtotal - total_discount + shipping
    
    return jsonify({
        'success': True,
        'message': msg,
        'coupon_discount': coupon_discount,
        'total_discount': total_discount,
        'new_total': final_total
    })

# --- ADMIN DECORATED ROUTES & ENDPOINTS ---

@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    db = get_db()
    
    # Fetch statistics
    total_sales_row = db.execute('SELECT SUM(total_price) as sum FROM orders').fetchone()
    total_sales = total_sales_row['sum'] or 0
    
    total_orders_row = db.execute('SELECT COUNT(*) as count FROM orders').fetchone()
    total_orders = total_orders_row['count'] or 0
    
    total_users_row = db.execute('SELECT COUNT(*) as count FROM users WHERE is_admin = 0').fetchone()
    total_users = total_users_row['count'] or 0
    
    low_stock_row = db.execute('SELECT COUNT(*) as count FROM products WHERE stock <= 5').fetchone()
    low_stock_count = low_stock_row['count'] or 0
    
    # Fetch all orders (with user details)
    all_orders = db.execute('''
        SELECT o.*, u.username, u.email 
        FROM orders o
        JOIN users u ON o.user_id = u.id
        ORDER BY o.id DESC
    ''').fetchall()
    
    orders_list = []
    for order in all_orders:
        items = db.execute('''
            SELECT oi.quantity, oi.price_at_purchase, p.name 
            FROM order_items oi
            JOIN products p ON oi.product_id = p.id
            WHERE oi.order_id = ?
        ''', (order['id'],)).fetchall()
        orders_list.append({
            'details': order,
            'items': items
        })
        
    # Fetch all products
    all_products = db.execute('SELECT * FROM products ORDER BY category ASC, name ASC').fetchall()
    
    return render_template('admin.html', 
                           total_sales=total_sales,
                           total_orders=total_orders,
                           total_users=total_users,
                           low_stock_count=low_stock_count,
                           orders=orders_list,
                           products=all_products)

@app.route('/api/admin/order/status', methods=['POST'])
@login_required
@admin_required
def api_admin_order_status():
    data = request.get_json() or {}
    order_id = data.get('order_id')
    status = data.get('status')
    
    if not order_id or not status:
        return jsonify({'error': 'bad_request', 'message': 'Missing parameters.'}), 400
        
    db = get_db()
    order = db.execute('SELECT id FROM orders WHERE id = ?', (order_id,)).fetchone()
    if not order:
        return jsonify({'error': 'not_found', 'message': 'Order not found.'}), 404
        
    db.execute('UPDATE orders SET status = ? WHERE id = ?', (status, order_id))
    db.commit()
    
    return jsonify({'success': True, 'message': f'Order status updated to {status}.'})

@app.route('/api/admin/product/stock', methods=['POST'])
@login_required
@admin_required
def api_admin_product_stock():
    data = request.get_json() or {}
    product_id = data.get('product_id')
    stock = data.get('stock')
    
    if not product_id or stock is None:
        return jsonify({'error': 'bad_request', 'message': 'Missing parameters.'}), 400
        
    try:
        stock = int(stock)
        if stock < 0:
            raise ValueError()
    except ValueError:
        return jsonify({'error': 'bad_request', 'message': 'Stock must be a non-negative integer.'}), 400
        
    db = get_db()
    product = db.execute('SELECT name FROM products WHERE id = ?', (product_id,)).fetchone()
    if not product:
        return jsonify({'error': 'not_found', 'message': 'Product not found.'}), 404
        
    db.execute('UPDATE products SET stock = ? WHERE id = ?', (stock, product_id))
    db.commit()
    
    return jsonify({'success': True, 'message': f"Stock for '{product['name']}' updated to {stock}."})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
