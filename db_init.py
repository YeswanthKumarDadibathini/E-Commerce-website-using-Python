import sqlite3
import json
import os

DB_PATH = 'shop.db'

def init_db():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print("Existing database removed.")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create tables
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        address TEXT,
        phone TEXT,
        is_admin INTEGER DEFAULT 0
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        price INTEGER NOT NULL,
        image_url TEXT NOT NULL,
        description TEXT NOT NULL,
        rating REAL DEFAULT 4.0,
        stock INTEGER NOT NULL,
        specifications TEXT NOT NULL
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS cart (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL DEFAULT 1,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
        UNIQUE(user_id, product_id)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS wishlist (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
        UNIQUE(user_id, product_id)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        total_price INTEGER NOT NULL,
        date TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'Processing',
        address TEXT NOT NULL,
        phone TEXT NOT NULL,
        payment_method TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS order_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        price_at_purchase INTEGER NOT NULL,
        FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
        FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER NOT NULL,
        user_id INTEGER,
        username TEXT NOT NULL,
        rating INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),
        comment TEXT NOT NULL,
        date TEXT NOT NULL,
        FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
    )
    ''')

    # Seed products
    products_to_seed = []

    # --- MOBILES ---
    mobiles = [
        ("Apple iPhone 16 Pro Max", 144999, "https://images.unsplash.com/photo-1695048133142-1a20484d2569?w=500&auto=format&fit=crop", 
         "The ultimate iPhone with the all-new A18 Pro chip, larger 6.9-inch Super Retina XDR display, Camera Control, and a massive leap in battery life.", 
         {"Brand": "Apple", "Model": "iPhone 16 Pro Max", "Storage": "256 GB", "RAM": "8 GB", "Processor": "A18 Pro", "Display": "6.9-inch OLED"}),
        ("Apple iPhone 16 Plus", 89999, "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=500&auto=format&fit=crop",
         "Features Camera Control, a 48MP Fusion camera, 5 vibrant colors, the A18 chip, and a big boost in battery life.",
         {"Brand": "Apple", "Model": "iPhone 16 Plus", "Storage": "128 GB", "RAM": "8 GB", "Processor": "A18", "Display": "6.7-inch OLED"}),
        ("Apple iPhone 16 Pro", 119999, "https://images.unsplash.com/photo-1598327105666-5b89351aff97?w=500&auto=format&fit=crop",
         "Pro camera system with 5x Telephoto, 48MP Ultra Wide, A18 Pro chip, and premium Titanium design.",
         {"Brand": "Apple", "Model": "iPhone 16 Pro", "Storage": "128 GB", "RAM": "8 GB", "Processor": "A18 Pro", "Display": "6.3-inch OLED"}),
        ("Apple iPhone 16", 79999, "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=500&auto=format&fit=crop",
         "The power-packed base model with the A18 chip, Camera Control, Action Button, and stunning color options.",
         {"Brand": "Apple", "Model": "iPhone 16", "Storage": "128 GB", "RAM": "8 GB", "Processor": "A18", "Display": "6.1-inch OLED"}),
        ("Samsung Galaxy S25 Ultra", 129999, "https://images.unsplash.com/photo-1610945265064-0e34e5519bbf?w=500&auto=format&fit=crop",
         "Samsung's premier flagship featuring Galaxy AI, Snapdragon 8 Gen 4, a 200MP Quad-Camera setup, and built-in S Pen.",
         {"Brand": "Samsung", "Model": "Galaxy S25 Ultra", "Storage": "256 GB", "RAM": "12 GB", "Processor": "Snapdragon 8 Gen 4", "Display": "6.8-inch Dynamic AMOLED"}),
        ("Samsung Galaxy S25+", 84999, "https://images.unsplash.com/photo-1580910051074-3eb694886505?w=500&auto=format&fit=crop",
         "A refined display, advanced cameras, and intelligent Galaxy AI features in a sleek armor aluminum frame.",
         {"Brand": "Samsung", "Model": "Galaxy S25+", "Storage": "256 GB", "RAM": "12 GB", "Processor": "Exynos 2500", "Display": "6.7-inch Dynamic AMOLED"}),
        ("Samsung Galaxy S25", 74999, "https://images.unsplash.com/photo-1598327106026-d9521da673d1?w=500&auto=format&fit=crop",
         "Premium performance, compact form factor, outstanding 50MP triple camera system and smart AI tools.",
         {"Brand": "Samsung", "Model": "Galaxy S25", "Storage": "128 GB", "RAM": "8 GB", "Processor": "Exynos 2500", "Display": "6.2-inch Dynamic AMOLED"}),
        ("OnePlus 13", 69999, "https://images.unsplash.com/photo-1580910051074-3eb694886505?w=500&auto=format&fit=crop",
         "Power-focused flagship with 100W SuperVOOC charging, 2K AMOLED Display, and Hasselblad camera system.",
         {"Brand": "OnePlus", "Model": "13", "Storage": "256 GB", "RAM": "16 GB", "Processor": "Snapdragon 8 Gen 4", "Display": "6.82-inch OLED"}),
        ("OnePlus 13R", 42999, "https://images.unsplash.com/photo-1598327105666-5b89351aff97?w=500&auto=format&fit=crop",
         "The flagship killer returns. Incredible performance, massive battery, and smooth 120Hz display at an amazing price.",
         {"Brand": "OnePlus", "Model": "13R", "Storage": "128 GB", "RAM": "8 GB", "Processor": "Snapdragon 8 Gen 3", "Display": "6.78-inch AMOLED"}),
        ("Google Pixel 9 Pro", 109999, "https://images.unsplash.com/photo-1598327106026-d9521da673d1?w=500&auto=format&fit=crop",
         "Google's AI-focused phone. Superb triple camera system with 30x Zoom, Tensor G4 processor, and Gemini integration.",
         {"Brand": "Google", "Model": "Pixel 9 Pro", "Storage": "128 GB", "RAM": "16 GB", "Processor": "Google Tensor G4", "Display": "6.3-inch Actua Display"}),
        ("Google Pixel 9", 74999, "https://images.unsplash.com/photo-1580910051074-3eb694886505?w=500&auto=format&fit=crop",
         "Advanced Gemini AI, industry-leading camera software, Tensor G4 performance, and 7 years of OS updates.",
         {"Brand": "Google", "Model": "Pixel 9", "Storage": "128 GB", "RAM": "12 GB", "Processor": "Google Tensor G4", "Display": "6.3-inch OLED"}),
        ("Nothing Phone (3)", 49999, "https://images.unsplash.com/photo-1610945265064-0e34e5519bbf?w=500&auto=format&fit=crop",
         "The iconic transparent glyph interface, now with AI features, upgraded dual cameras, and Snapdragon 8s Gen 3.",
         {"Brand": "Nothing", "Model": "Phone (3)", "Storage": "256 GB", "RAM": "12 GB", "Processor": "Snapdragon 8s Gen 3", "Display": "6.7-inch OLED"}),
        ("Motorola Edge 60", 31999, "https://images.unsplash.com/photo-1598327105666-5b89351aff97?w=500&auto=format&fit=crop",
         "Ultra-thin curved design, 144Hz pOLED screen, 68W fast charging, and a clean stock Android UI.",
         {"Brand": "Motorola", "Model": "Edge 60", "Storage": "256 GB", "RAM": "8 GB", "Processor": "Dimensity 7300", "Display": "6.55-inch pOLED"}),
        ("Xiaomi 15", 59999, "https://images.unsplash.com/photo-1598327106026-d9521da673d1?w=500&auto=format&fit=crop",
         "Leica professional optics, compact premium build, Snapdragon 8 Gen 4, and HyperOS efficiency.",
         {"Brand": "Xiaomi", "Model": "15", "Storage": "256 GB", "RAM": "12 GB", "Processor": "Snapdragon 8 Gen 4", "Display": "6.36-inch OLED"}),
        ("Redmi Note 14 Pro", 28999, "https://images.unsplash.com/photo-1580910051074-3eb694886505?w=500&auto=format&fit=crop",
         "Outstanding value with a 200MP camera, 120W HyperCharge, and a 1.5K curved AMOLED display.",
         {"Brand": "Xiaomi", "Model": "Redmi Note 14 Pro", "Storage": "256 GB", "RAM": "8 GB", "Processor": "Dimensity 7300 Ultra", "Display": "6.67-inch AMOLED"}),
    ]
    for name, price, img, desc, specs in mobiles:
        products_to_seed.append((name, "mobiles", price, img, desc, 4.4, 20, json.dumps(specs)))

    # --- LAPTOPS ---
    laptops = [
        ("Apple MacBook Air M4", 99999, "https://images.unsplash.com/photo-1611186871348-b1ce696e52c9?w=500&auto=format&fit=crop",
         "Strikingly thin design, silent fanless architecture, and the incredible speed of the Apple M4 chip. Built for work and play.",
         {"Brand": "Apple", "Model": "MacBook Air M4", "Processor": "Apple M4 (10-core)", "RAM": "16 GB Unified", "Storage": "256 GB SSD", "OS": "macOS Sequoia", "Display": "13.6-inch Liquid Retina"}),
        ("Apple MacBook Pro M4", 179999, "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=500&auto=format&fit=crop",
         "The ultimate pro laptop. Liquid Retina XDR screen, pro port selection, and M4 Pro performance for extreme workloads.",
         {"Brand": "Apple", "Model": "MacBook Pro M4", "Processor": "Apple M4 Pro (12-core)", "RAM": "24 GB Unified", "Storage": "512 GB SSD", "OS": "macOS Sequoia", "Display": "14.2-inch Liquid Retina XDR"}),
        ("ASUS TUF Gaming A15", 82999, "https://images.unsplash.com/photo-1603302576837-37561b2e2302?w=500&auto=format&fit=crop",
         "High durability gaming laptop equipped with AMD Ryzen 7, NVIDIA RTX 3050 Ti, and a fast 144Hz refresh rate panel.",
         {"Brand": "ASUS", "Model": "TUF Gaming A15", "Processor": "AMD Ryzen 7 7445HS", "RAM": "16 GB DDR5", "Storage": "512 GB SSD", "GPU": "NVIDIA RTX 3050 Ti 4GB", "Display": "15.6-inch FHD 144Hz"}),
        ("ASUS ROG Strix G16", 145999, "https://images.unsplash.com/photo-1541807084-5c52b6b3adef?w=500&auto=format&fit=crop",
         "Tournament-ready performance. Intel Core i7 13th Gen, RTX 4060 graphics, and advanced ROG Intelligent Cooling.",
         {"Brand": "ASUS", "Model": "ROG Strix G16", "Processor": "Intel Core i7-13650HX", "RAM": "16 GB DDR5", "Storage": "1 TB SSD", "GPU": "NVIDIA RTX 4060 8GB", "Display": "16-inch WUXGA 165Hz"}),
        ("HP Pavilion 15", 64999, "https://images.unsplash.com/photo-1588872657578-7efd1f1555ed?w=500&auto=format&fit=crop",
         "A classic premium everyday driver with a thin bezel screen, metal casing, Intel Core i5 processor, and back-lit keyboard.",
         {"Brand": "HP", "Model": "Pavilion 15", "Processor": "Intel Core i5-1335U", "RAM": "16 GB", "Storage": "512 GB SSD", "OS": "Windows 11 Home", "Display": "15.6-inch FHD IPS"}),
        ("HP Victus Gaming", 79999, "https://images.unsplash.com/photo-1603302576837-37561b2e2302?w=500&auto=format&fit=crop",
         "Modern design meets gaming power. 12th Gen Intel Core i5 with NVIDIA RTX 3050 graphics and dual fans.",
         {"Brand": "HP", "Model": "Victus Gaming", "Processor": "Intel Core i5-12450H", "RAM": "16 GB", "Storage": "512 GB SSD", "GPU": "NVIDIA RTX 3050 4GB", "Display": "15.6-inch FHD 144Hz"}),
        ("Dell XPS 13", 12999, "https://images.unsplash.com/photo-1593642632823-8f785ba67e45?w=500&auto=format&fit=crop",
         "Ultra-premium infinity edge display, CNC machined aluminum chassis, Intel Evo Core i7, and featherweight design.",
         {"Brand": "Dell", "Model": "XPS 13 9315", "Processor": "Intel Core i7-1250U", "RAM": "16 GB LPDDR5", "Storage": "512 GB SSD", "OS": "Windows 11 Pro", "Display": "13.4-inch FHD+ InfinityEdge"}),
        ("Lenovo LOQ 15", 76999, "https://images.unsplash.com/photo-1541807084-5c52b6b3adef?w=500&auto=format&fit=crop",
         "Excellent value gaming laptop featuring AMD Ryzen 5, NVIDIA RTX 4050, and AI engine controls for optimal FPS.",
         {"Brand": "Lenovo", "Model": "LOQ 15", "Processor": "AMD Ryzen 5 7640HS", "RAM": "16 GB DDR5", "Storage": "512 GB SSD", "GPU": "NVIDIA RTX 4050 6GB", "Display": "15.6-inch FHD 144Hz"}),
        ("Lenovo Legion 5", 109999, "https://images.unsplash.com/photo-1603302576837-37561b2e2302?w=500&auto=format&fit=crop",
         "High-end gaming performance. Ryzen 7, RTX 4060, Legion Coldfront cooling system, and TrueStrike keyboard.",
         {"Brand": "Lenovo", "Model": "Legion 5 Pro", "Processor": "AMD Ryzen 7 7840HS", "RAM": "16 GB", "Storage": "1 TB SSD", "GPU": "NVIDIA RTX 4060 8GB", "Display": "16-inch WQXGA 165Hz"}),
        ("Alienware M16", 219999, "https://images.unsplash.com/photo-1541807084-5c52b6b3adef?w=500&auto=format&fit=crop",
         "Absolute monster for enthusiasts. Core i9, RTX 4080, custom Cryo-tech cooling, and mechanical keyboard keys.",
         {"Brand": "Dell", "Model": "Alienware M16", "Processor": "Intel Core i9-13900HX", "RAM": "32 GB DDR5", "Storage": "1 TB SSD", "GPU": "NVIDIA RTX 4080 12GB", "Display": "16-inch QHD+ 240Hz"}),
    ]
    for name, price, img, desc, specs in laptops:
        products_to_seed.append((name, "laptops", price, img, desc, 4.6, 12, json.dumps(specs)))

    # --- FASHION ---
    fashion = [
        ("Men's Premium T-Shirt", 599, "https://images.unsplash.com/photo-1521572267360-ee0c2909d518?w=500&auto=format&fit=crop",
         "100% combed cotton premium t-shirt. Breathable, preshrunk, and perfect for regular casual wear.",
         {"Brand": "Roadster", "Material": "100% Cotton", "Fit": "Regular Fit", "Sleeve": "Half Sleeve", "Wash Care": "Machine Wash"}),
        ("Formal Shirt", 899, "https://images.unsplash.com/photo-1596755094514-f87e34085b2c?w=500&auto=format&fit=crop",
         "Crisp, wrinkle-free formal cotton blend shirt. Designed for comfortable wear during long office hours.",
         {"Brand": "Peter England", "Material": "Cotton Blend", "Fit": "Slim Fit", "Collar": "Spread Collar", "Pattern": "Solid"}),
        ("Blue Denim Jeans", 1299, "https://images.unsplash.com/photo-1542272604-787c3835535d?w=500&auto=format&fit=crop",
         "Classic blue stretchable denim jeans. Durable stitching, comfortable waist fit, and modern tapered leg look.",
         {"Brand": "Levi's", "Material": "98% Cotton, 2% Elastane", "Fit": "Slim Fit", "Stretch": "Yes", "Wash": "Light Fade"}),
        ("Winter Bomber Jacket", 2499, "https://images.unsplash.com/photo-1551028719-00167b16eac5?w=500&auto=format&fit=crop",
         "Stay warm in style. Wind-resistant outer shell with cozy polyester thermal lining and heavy-duty zippers.",
         {"Brand": "Puma", "Material": "Polyester", "Type": "Bomber Jacket", "Hood": "No", "Pockets": "3 Zip Pockets"}),
        ("Classic Sport Hoodie", 1499, "https://images.unsplash.com/photo-1556821840-3a63f95609a7?w=500&auto=format&fit=crop",
         "Thick fleece pullover hoodie with dynamic drawstring. Relaxed fit suitable for workouts or lounging.",
         {"Brand": "Adidas", "Material": "Fleece Cotton Blend", "Type": "Pullover", "Pocket": "Kangaroo Pocket", "Fit": "Relaxed"}),
        ("Running Shoes", 2199, "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=500&auto=format&fit=crop",
         "Lightweight mesh running shoes with responsive EVA foam cushioning. Perfect for daily jogs and workouts.",
         {"Brand": "Nike", "Type": "Running Shoes", "Material": "Mesh", "Sole": "Rubber", "Closure": "Lace-Up"}),
        ("Premium Sneakers", 2599, "https://images.unsplash.com/photo-1549298916-b41d501d3772?w=500&auto=format&fit=crop",
         "Trendy high-top lifestyle sneakers with synthetic leather panels and soft foam comfort insoles.",
         {"Brand": "Nike", "Type": "Sneakers", "Material": "Synthetic Leather", "Sole": "Rubber", "Color": "White/Pastels"}),
        ("Analogue Leather Watch", 3499, "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=500&auto=format&fit=crop",
         "Minimalist luxury analogue watch. Real leather strap, quartz mechanism, and scratch-resistant mineral glass face.",
         {"Brand": "Fossil", "Strap Material": "Genuine Leather", "Movement": "Quartz", "Water Resistant": "50m", "Dial Color": "Black"}),
        ("Leather Wallet", 899, "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=500&auto=format&fit=crop",
         "Slim, genuine leather bi-fold wallet. Features RFID blocking technology, 6 card slots, and 2 currency slots.",
         {"Brand": "WildHorn", "Material": "Genuine Leather", "Slots": "6 Card, 2 Cash", "RFID Blocking": "Yes", "Style": "Bi-fold"}),
        ("Classic Sunglasses", 1199, "https://images.unsplash.com/photo-1572635196237-14b3f281503f?w=500&auto=format&fit=crop",
         "Polarized retro aviator sunglasses. 100% UV protection, sturdy metallic frames, and scratch-proof lenses.",
         {"Brand": "Ray-Ban Style", "Frame": "Metal", "Lens Type": "Polarized UV400", "Shape": "Aviator", "Gender": "Unisex"}),
    ]
    for name, price, img, desc, specs in fashion:
        products_to_seed.append((name, "fashion", price, img, desc, 4.2, 35, json.dumps(specs)))

    # --- ELECTRONICS ---
    electronics = [
        ("Samsung 55\" Smart TV", 54999, "https://images.unsplash.com/photo-1593305841991-05c297ba4575?w=500&auto=format&fit=crop",
         "Crisp 4K Ultra HD smart screen with PurColor, powerful Crystal Processor 4K, and smart voice assistant integrations.",
         {"Brand": "Samsung", "Screen Size": "55 inches", "Resolution": "4K UHD (3840x2160)", "Refresh Rate": "60 Hz", "Smart OS": "Tizen"}),
        ("LG 43\" LED TV", 36999, "https://images.unsplash.com/photo-1593305841991-05c297ba4575?w=500&auto=format&fit=crop",
         "4K UHD resolution, active HDR optimization, AI Sound Pro, and smart WebOS dashboard with popular streaming apps.",
         {"Brand": "LG", "Screen Size": "43 inches", "Resolution": "4K UHD", "Refresh Rate": "60 Hz", "Smart OS": "WebOS"}),
        ("Wireless Earbuds", 2499, "https://images.unsplash.com/photo-1590658268037-6bf12165a8df?w=500&auto=format&fit=crop",
         "True wireless earbuds with touch controls, deep dynamic bass, 30 hours of playback with case, and IPX5 sweatproofing.",
         {"Brand": "boAt", "Battery Life": "30 Hours total", "Bluetooth": "v5.3", "Water Resistance": "IPX5", "Noise Cancelling": "Environmental (ENC)"}),
        ("Noise Cancelling Headphones", 4999, "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=500&auto=format&fit=crop",
         "Over-ear headphones with hybrid active noise cancellation (ANC), memory foam earcups, and high-res audio drivers.",
         {"Brand": "Sony Style", "Type": "Over-Ear", "Battery": "40 Hours", "ANC": "Yes (Hybrid)", "Charging": "USB Type-C"}),
        ("Bluetooth Speaker", 2999, "https://images.unsplash.com/photo-1608043152269-423dbba4e7e1?w=500&auto=format&fit=crop",
         "Portable outdoor speaker with rich 20W stereo output, passive bass radiators, and IPX7 complete waterproof build.",
         {"Brand": "JBL Style", "Output": "20W RMS", "Battery": "12 Hours", "Waterproof": "IPX7", "Connectivity": "Bluetooth & Aux"}),
        ("Canon DSLR Camera", 59999, "https://images.unsplash.com/photo-1516035069371-29a1b244cc32?w=500&auto=format&fit=crop",
         "Perfect starter DSLR kit. 24.1MP APS-C sensor, built-in Wi-Fi, and 18-55mm IS II zoom lens included.",
         {"Brand": "Canon", "Sensor": "24.1MP APS-C", "Lens Kit": "18-55mm f/3.5-5.6 IS II", "Video": "Full HD 1080p at 30fps", "Connectivity": "Wi-Fi, NFC"}),
        ("HP Ink Tank Printer", 12999, "https://images.unsplash.com/photo-1612815154858-60aa4c59eaa6?w=500&auto=format&fit=crop",
         "High volume, ultra low-cost printing. Print, copy, and scan. Wireless printing from smartphones supported.",
         {"Brand": "HP", "Functions": "Print, Scan, Copy", "Type": "Ink Tank", "Connectivity": "Wi-Fi, USB", "Page Yield": "Up to 8000 color pages"}),
        ("Mechanical Keyboard", 3499, "https://images.unsplash.com/photo-1618384887929-16ec33fab9ef?w=500&auto=format&fit=crop",
         "Tenkeyless mechanical keyboard with customizable RGB backlighting, clicky blue switches, and braided cable.",
         {"Brand": "Redgear", "Layout": "Tenkeyless (87 keys)", "Switch Type": "Blue mechanical", "Backlight": "Full RGB", "Anti-Ghosting": "Yes"}),
        ("Wireless Mouse", 999, "https://images.unsplash.com/photo-1615663245857-ac93bb7c39e7?w=500&auto=format&fit=crop",
         "Ergonomic silent wireless mouse with 2.4GHz USB receiver, adjustable DPI levels, and 18-month battery life.",
         {"Brand": "Logitech", "Type": "Wireless", "Sensor": "Optical 1000-1600 DPI", "Buttons": "3 Buttons", "Battery": "1x AA"}),
        ("20000mAh Power Bank", 1999, "https://images.unsplash.com/photo-1583394838336-acd977736f90?w=500&auto=format&fit=crop",
         "High capacity battery backup with dual USB ports and Type-C 22.5W fast output charging capabilities.",
         {"Brand": "Mi", "Capacity": "20000 mAh", "Max Output": "22.5W Fast Charge", "Input Ports": "Type-C, Micro-USB", "Weight": "430g"}),
    ]
    for name, price, img, desc, specs in electronics:
        products_to_seed.append((name, "electronics", price, img, desc, 4.3, 25, json.dumps(specs)))

    # --- HOME & KITCHEN ---
    home_kitchen = [
        ("Luxury Sofa Set", 29999, "https://images.unsplash.com/photo-1555041469-a586c61ea9bc?w=500&auto=format&fit=crop",
         "Elegant dark beige 3-seater sofa made with premium upholstery fabric and high-density foam padding for luxury comfort.",
         {"Brand": "Durian", "Seating Capacity": "3 Seater", "Material": "Premium Fabric", "Frame": "Solid Wood", "Warranty": "3 Years"}),
        ("King Size Wooden Bed", 24999, "https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?w=500&auto=format&fit=crop",
         "Sturdy king size bed frame crafted from high-grade solid Sheesham wood with classic honey finish and storage deck.",
         {"Brand": "Wakefit", "Size": "King Size", "Wood Type": "Sheesham Wood", "Storage": "Box storage optional", "Finish": "Honey Finish"}),
        ("Modern Dining Table Set", 15999, "https://images.unsplash.com/photo-1615066390971-03e4e1c36ddf?w=500&auto=format&fit=crop",
         "Space-saving 4-seater dining table with dark walnut wood finish and matching padded cushions.",
         {"Brand": "Urban Ladder", "Seating": "4 Seater", "Table Material": "Engineered Wood", "Chair Cushion": "Yes", "Finish": "Walnut"}),
        ("Ergonomic Office Chair", 6999, "https://images.unsplash.com/photo-1580481072645-022f9a6dbf27?w=500&auto=format&fit=crop",
         "Mesh back office chair with adjustable lumbar support, pneumatic gas height lift, and tilt mechanism.",
         {"Brand": "Green Soul", "Backrest": "High mesh", "Lumbar Support": "Adjustable", "Armrest": "2D Adjustable", "Gas Lift": "Class 4"}),
        ("Double Door Refrigerator", 39999, "https://images.unsplash.com/photo-1588854337236-6889d631faa8?w=500&auto=format&fit=crop",
         "260L 3-star frost-free double door refrigerator with smart inverter compressor and convertible freezer zones.",
         {"Brand": "Samsung", "Capacity": "260 Litres", "Energy Star Rating": "3 Star", "Defrost Type": "Frost Free", "Compressor": "Digital Inverter"}),
        ("Front Load Washing Machine", 27999, "https://images.unsplash.com/photo-1626806787461-102c1bfaaea1?w=500&auto=format&fit=crop",
         "Fully automatic front load washing machine with 7kg capacity, built-in heater, and 1200 RPM high-speed dryer.",
         {"Brand": "IFB", "Capacity": "7.0 kg", "Operation": "Fully Automatic Front Load", "Spin Speed": "1200 RPM", "Inbuilt Heater": "Yes"}),
        ("Convection Microwave Oven", 9999, "https://images.unsplash.com/photo-1578683010236-d716f9a3f461?w=500&auto=format&fit=crop",
         "28L convection oven for baking, grilling, reheating, and defrosting. Autocook menus included.",
         {"Brand": "LG", "Capacity": "28 Litres", "Type": "Convection", "Control Type": "Touch Key pad", "Power Output": "900W"}),
        ("Air Fryer", 5999, "https://images.unsplash.com/photo-1621972750749-0fbb1abb7736?w=500&auto=format&fit=crop",
         "Healthy oil-free cooking. Rapid air technology circulates hot air for crispy fries, veggies, and meats.",
         {"Brand": "Philips", "Capacity": "4.1 Litres", "Power": "1400W", "Timer": "Up to 30 mins", "Temp Control": "80-200°C"}),
        ("Water Purifier (RO+UV)", 12999, "https://images.unsplash.com/photo-1602143407151-7111542de6e8?w=500&auto=format&fit=crop",
         "Advanced multi-stage RO + UV purification system with mineral booster and large 7L storage tank.",
         {"Brand": "Kent", "Purification Stages": "RO + UV + UF + TDS Control", "Storage Capacity": "7 Litres", "Installation": "Wall Mounted"}),
        ("Designer Wall Clock", 999, "https://images.unsplash.com/photo-1563861826100-9cb868fdbe1c?w=500&auto=format&fit=crop",
         "Premium round analog wall clock with silent sweep quartz movement and clean wooden border design.",
         {"Brand": "Titan", "Dial Shape": "Round", "Movement": "Silent Sweep Quartz", "Material": "Wood & Glass", "Diameter": "30 cm"}),
    ]
    for name, price, img, desc, specs in home_kitchen:
        products_to_seed.append((name, "home", price, img, desc, 4.4, 15, json.dumps(specs)))

    # --- TOYS & GAMES ---
    toys_games = [
        ("Premium Giant Teddy Bear", 899, "https://images.unsplash.com/photo-1559251606-c623743a6d76?w=500&auto=format&fit=crop",
         "Extra soft, cute giant teddy bear plush toy made with premium hypoallergenic stuffing. Perfect gift.",
         {"Type": "Soft Toy / Plush", "Recommended Age": "0+ Months", "Height": "3 feet", "Washable": "Hand Wash"}),
        ("LEGO Creative Building Set", 2499, "https://images.unsplash.com/photo-1585320806297-9794b3e4eeae?w=500&auto=format&fit=crop",
         "LEGO bricks set containing 790 classic pieces in 33 different colors. Stimulates design imagination.",
         {"Brand": "LEGO", "Pieces": "790 Bricks", "Recommended Age": "4+ Years", "Item Model": "10698"}),
        ("Remote Control High Speed Car", 1799, "https://images.unsplash.com/photo-1594787318286-3d835c1d207f?w=500&auto=format&fit=crop",
         "All-terrain high speed RC racing car with remote, durable shocks, and rechargeable lithium battery.",
         {"Type": "RC Car", "Scale": "1:18", "Frequency": "2.4 GHz", "Control Range": "50 meters", "Battery": "Rechargeable 7.4V"}),
        ("Mini GPS Camera Drone", 4999, "https://images.unsplash.com/photo-1527977966376-1c8408f9f108?w=500&auto=format&fit=crop",
         "Foldable mini drone equipped with 1080p HD camera, altitude hold, one-key return, and WiFi transmission.",
         {"Type": "Quadcopter Drone", "Camera": "1080p HD Wi-Fi", "Flight Time": "15 mins per battery", "Weight": "249g (No registration)"}),
        ("Barbie Dream House Doll", 1299, "https://images.unsplash.com/photo-1596461404969-9ae70f2830c1?w=500&auto=format&fit=crop",
         "Authentic Barbie doll dressed in dynamic fashionable outfit with accessories kit.",
         {"Brand": "Barbie", "Material": "Plastic & Fabric", "Recommended Age": "3+ Years", "Includes": "Doll, dress, shoes, purse"}),
        ("Classic Wooden Chess Board", 999, "https://images.unsplash.com/photo-1529699211952-734e80c4d42b?w=500&auto=format&fit=crop",
         "Premium folding wooden chess set with handcrafted chessmen pieces and built-in drawer slots.",
         {"Material": "Pine Wood", "Board Size": "12 x 12 inches", "Foldable": "Yes", "Recommended Age": "6+ Years"}),
        ("Rubik's Speed Cube 3x3", 399, "https://images.unsplash.com/photo-1587654780291-39c9404d746b?w=500&auto=format&fit=crop",
         "Highly lubricated super-fast 3x3 speed cube with stickerless tiles for professional cubers.",
         {"Brand": "Rubik's Style", "Type": "3x3x3 Cube", "Material": "ABS Plastic (Stickerless)", "Weight": "85g"}),
        ("English Willow Cricket Bat", 1499, "https://images.unsplash.com/photo-1531415074968-036ba1b575da?w=500&auto=format&fit=crop",
         "Short handle english willow cricket bat. Light weight with sweet spot balance for hard tennis or leather balls.",
         {"Sport": "Cricket", "Material": "English Willow", "Handle Type": "Short Handle (Singapore Cane)", "Weight": "1150g"}),
        ("Official Match Soccer Ball", 999, "https://images.unsplash.com/photo-1579952363873-27f3bade9f55?w=500&auto=format&fit=crop",
         "Size 5 soccer ball with TPU outer casing, machine stitched panel construction for perfect round shape.",
         {"Sport": "Football / Soccer", "Size": "Size 5 (Official)", "Material": "TPU / Rubber", "Stitching": "Machine Stitched"}),
        ("Electronic Musical Keyboard", 1499, "https://images.unsplash.com/photo-1552422535-c45813c61732?w=500&auto=format&fit=crop",
         "37-key kids digital piano keyboard with microphone input, demo tracks, and battery-powered portable design.",
         {"Type": "Musical Toy", "Keys": "37 Mini Keys", "Power Source": "4x AA batteries or USB", "Includes": "Keyboard, Mic, Cable"}),
    ]
    for name, price, img, desc, specs in toys_games:
        products_to_seed.append((name, "toys", price, img, desc, 4.5, 18, json.dumps(specs)))

    cursor.executemany('''
    INSERT INTO products (name, category, price, image_url, description, rating, stock, specifications)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', products_to_seed)

    # Seed an admin user (password: admin123) and a guest user (password: user123)
    from werkzeug.security import generate_password_hash
    admin_pw = generate_password_hash("admin123")
    user_pw = generate_password_hash("user123")

    cursor.execute('''
    INSERT INTO users (username, password_hash, email, address, phone, is_admin)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', ("admin", admin_pw, "admin@shopeasy.com", "Admin HQ, Delhi, India", "9999999999", 1))

    cursor.execute('''
    INSERT INTO users (username, password_hash, email, address, phone, is_admin)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', ("user", user_pw, "user@gmail.com", "Sector 62, Noida, UP, India", "8888888888", 0))

    conn.commit()
    conn.close()
    print("Database initialized and seeded successfully.")

if __name__ == '__main__':
    init_db()
