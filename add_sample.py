# add_sample.py
import sqlite3

def add_sample_products():
    """Add sample products to the database"""
    
    # Connect to the database
    conn = sqlite3.connect('inventory.db')
    cursor = conn.cursor()
    
    # Sample products data
    sample_products = [
        ('Laptop', 'High-performance laptop with 16GB RAM', 75000, 10),
        ('Smartphone', 'Latest model smartphone with 5G', 25000, 15),
        ('Headphones', 'Wireless noise-cancelling headphones', 3000, 20),
        ('USB Cable', 'USB-C charging cable, 2 meter', 500, 30),
        ('Mouse', 'Wireless optical mouse', 800, 25),
        ('Keyboard', 'Mechanical gaming keyboard', 1500, 12),
        ('Monitor', '24 inch LED monitor, Full HD', 12000, 8),
        ('Printer', 'Laser printer with Wi-Fi', 18000, 5),
        ('External Hard Drive', '1TB external USB drive', 6000, 7),
        ('Webcam', 'HD webcam with microphone', 2500, 10),
    ]
    
    # Insert products into database
    cursor.executemany(
        'INSERT INTO products (name, description, price, stock_quantity) VALUES (?, ?, ?, ?)',
        sample_products
    )
    
    # Save changes
    conn.commit()
    
    # Check how many products were added
    cursor.execute('SELECT COUNT(*) FROM products')
    count = cursor.fetchone()[0]
    
    # Close connection
    conn.close()
    
    print(f"✅ {len(sample_products)} sample products added successfully!")
    print(f"📊 Total products in database: {count}")

if __name__ == '__main__':
    add_sample_products()