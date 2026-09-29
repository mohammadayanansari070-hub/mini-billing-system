# app.py
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from datetime import datetime
import sqlite3

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

DATABASE = 'inventory.db'

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database with tables"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Products table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL,
            stock_quantity INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Sales table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_number TEXT UNIQUE NOT NULL,
            total_amount REAL NOT NULL,
            paid_amount REAL,
            balance REAL,
            sale_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Sale items table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sale_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sale_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL,
            total REAL NOT NULL,
            FOREIGN KEY (sale_id) REFERENCES sales (id),
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
    ''')
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'staff',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Settings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE NOT NULL,
            value TEXT
        )
    ''')
    
    # Insert default shop name if not exists
    cursor.execute('''
        INSERT OR IGNORE INTO settings (key, value) VALUES ('shop_name', 'Mini Billing System')
    ''')
    
    # Insert default admin user if not exists
    cursor.execute('''
        INSERT OR IGNORE INTO users (username, password, role) 
        VALUES ('admin', 'admin123', 'admin')
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Database created successfully!")

# Initialize database
init_db()

# ==================== HOME / DASHBOARD ====================
@app.route('/')
def index():
    """Dashboard with statistics"""
    conn = get_db()
    
    total_products = conn.execute('SELECT COUNT(*) as count FROM products').fetchone()['count']
    total_stock = conn.execute('SELECT SUM(stock_quantity) as total FROM products').fetchone()['total'] or 0
    total_sales = conn.execute('SELECT SUM(total_amount) as total FROM sales').fetchone()['total'] or 0
    
    today = datetime.now().strftime('%Y-%m-%d')
    today_sales = conn.execute('''
        SELECT SUM(total_amount) as total 
        FROM sales 
        WHERE DATE(sale_date) = ?
    ''', (today,)).fetchone()['total'] or 0
    
    recent_sales = conn.execute('''
        SELECT * FROM sales 
        ORDER BY sale_date DESC 
        LIMIT 5
    ''').fetchall()
    
    low_stock = conn.execute('''
        SELECT * FROM products 
        WHERE stock_quantity < 10 
        ORDER BY stock_quantity ASC 
        LIMIT 5
    ''').fetchall()
    
    conn.close()
    
    return render_template('index.html',
                         total_products=total_products,
                         total_stock=total_stock,
                         total_sales=total_sales,
                         today_sales=today_sales,
                         recent_sales=recent_sales,
                         low_stock=low_stock)

# ==================== PRODUCT ROUTES ====================
@app.route('/products')
def products():
    """Display all products"""
    conn = get_db()
    products = conn.execute('SELECT * FROM products ORDER BY id DESC').fetchall()
    conn.close()
    return render_template('products.html', products=products)

@app.route('/add_product', methods=['GET', 'POST'])
def add_product():
    """Add new product"""
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = float(request.form['price'])
        stock_quantity = int(request.form['stock_quantity'])
        
        conn = get_db()
        conn.execute(
            'INSERT INTO products (name, description, price, stock_quantity) VALUES (?, ?, ?, ?)',
            (name, description, price, stock_quantity)
        )
        conn.commit()
        conn.close()
        flash('✅ Product added successfully!')
        return redirect(url_for('products'))
    
    return render_template('add_product.html')

@app.route('/edit_product/<int:id>', methods=['GET', 'POST'])
def edit_product(id):
    """Edit existing product"""
    conn = get_db()
    
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = float(request.form['price'])
        stock_quantity = int(request.form['stock_quantity'])
        
        conn.execute(
            'UPDATE products SET name=?, description=?, price=?, stock_quantity=? WHERE id=?',
            (name, description, price, stock_quantity, id)
        )
        conn.commit()
        conn.close()
        flash('✅ Product updated successfully!')
        return redirect(url_for('products'))
    
    product = conn.execute('SELECT * FROM products WHERE id=?', (id,)).fetchone()
    conn.close()
    return render_template('edit_product.html', product=product)

@app.route('/delete_product/<int:id>')
def delete_product(id):
    """Delete product"""
    conn = get_db()
    conn.execute('DELETE FROM products WHERE id=?', (id,))
    conn.commit()
    conn.close()
    flash('✅ Product deleted successfully!')
    return redirect(url_for('products'))

# ==================== BILLING ROUTES ====================
@app.route('/billing')
def billing():
    """Billing page"""
    conn = get_db()
    products = conn.execute('SELECT * FROM products WHERE stock_quantity > 0').fetchall()
    conn.close()
    return render_template('billing.html', products=products)

@app.route('/search_products')
def search_products():
    """Search products for billing (AJAX)"""
    query = request.args.get('q', '')
    conn = get_db()
    products = conn.execute(
        'SELECT * FROM products WHERE name LIKE ? AND stock_quantity > 0',
        ('%' + query + '%',)
    ).fetchall()
    conn.close()
    return jsonify([dict(product) for product in products])

@app.route('/save_bill', methods=['POST'])
def save_bill():
    """Save bill to database and update stock"""
    try:
        data = request.json
        cart_items = data['cart_items']
        total_amount = data['total_amount']
        paid_amount = data['paid_amount']
        balance = data['balance']
        
        conn = get_db()
        cursor = conn.cursor()
        
        invoice_number = f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        cursor.execute(
            'INSERT INTO sales (invoice_number, total_amount, paid_amount, balance) VALUES (?, ?, ?, ?)',
            (invoice_number, total_amount, paid_amount, balance)
        )
        sale_id = cursor.lastrowid
        
        for item in cart_items:
            cursor.execute(
                'INSERT INTO sale_items (sale_id, product_id, quantity, price, total) VALUES (?, ?, ?, ?, ?)',
                (sale_id, item['id'], item['quantity'], item['price'], item['quantity'] * item['price'])
            )
            cursor.execute(
                'UPDATE products SET stock_quantity = stock_quantity - ? WHERE id = ?',
                (item['quantity'], item['id'])
            )
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'invoice_number': invoice_number,
            'message': 'Bill saved successfully!'
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/invoice/<invoice_number>')
def view_invoice(invoice_number):
    """View invoice details"""
    conn = get_db()
    
    sale = conn.execute(
        'SELECT * FROM sales WHERE invoice_number = ?',
        (invoice_number,)
    ).fetchone()
    
    items = conn.execute('''
        SELECT si.*, p.name 
        FROM sale_items si 
        JOIN products p ON si.product_id = p.id 
        WHERE si.sale_id = ?
    ''', (sale['id'],)).fetchall()
    
    conn.close()
    return render_template('invoice.html', sale=sale, items=items)

# ==================== SALES HISTORY ROUTES ====================
@app.route('/sales')
def sales_history():
    """Display all sales history"""
    search = request.args.get('search', '')
    
    conn = get_db()
    
    if search:
        sales = conn.execute('''
            SELECT * FROM sales 
            WHERE invoice_number LIKE ? 
            OR sale_date LIKE ?
            ORDER BY sale_date DESC
        ''', (f'%{search}%', f'%{search}%')).fetchall()
    else:
        sales = conn.execute('SELECT * FROM sales ORDER BY sale_date DESC').fetchall()
    
    total_sales = conn.execute('SELECT SUM(total_amount) as total FROM sales').fetchone()['total'] or 0
    total_invoices = conn.execute('SELECT COUNT(*) as count FROM sales').fetchone()['count']
    
    conn.close()
    
    return render_template('sales.html', 
                         sales=sales, 
                         total_sales=total_sales,
                         total_invoices=total_invoices,
                         search=search)

@app.route('/sale/<int:sale_id>')
def sale_details(sale_id):
    """View individual sale details"""
    conn = get_db()
    
    sale = conn.execute('SELECT * FROM sales WHERE id=?', (sale_id,)).fetchone()
    
    items = conn.execute('''
        SELECT si.*, p.name 
        FROM sale_items si 
        JOIN products p ON si.product_id = p.id 
        WHERE si.sale_id = ?
    ''', (sale_id,)).fetchall()
    
    conn.close()
    return render_template('sale_details.html', sale=sale, items=items)

if __name__ == '__main__':
    app.run(debug=True)