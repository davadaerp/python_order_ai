from flask import Flask, request, jsonify, render_template
import sqlite3
import pandas as pd

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('OrderStatistics.db')
    conn.row_factory = sqlite3.Row
    return conn

def create_table():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS product (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_code TEXT,
            product_name TEXT,
            alcohol_type TEXT,
            unit TEXT,
            quantity_per_box INTEGER,
            product_price REAL,
            product_amount REAL,
            product_nickname TEXT
        )
    ''')
    conn.commit()
    conn.close()

create_table()

@app.route('/product', methods=['GET'])
def list_products(alcohol_type, product_name):

    conn = get_db_connection()
    query = 'SELECT * FROM product WHERE 1=1'
    params = []

    if alcohol_type:
        query += ' AND alcohol_type = ?'
        params.append(alcohol_type)
    if product_name:
        query += ' AND product_name LIKE ?'
        params.append(f'%{product_name}%')

    products = conn.execute(query, params).fetchall()
    conn.close()
    return products

@app.route('/product/<int:product_id>', methods=['GET'])
def get_product(product_id):
    conn = get_db_connection()
    product = conn.execute('SELECT * FROM product WHERE id = ?', (product_id,)).fetchone()
    conn.close()
    return product
    '''
    if product is None:
        return jsonify({'error': 'Product not found'}), 404
        '''

@app.route('/product', methods=['POST'])
def add_product(data):
    conn = get_db_connection()
    try:
        # Get a cursor object from the connection
        cursor = conn.cursor()

        # 현재 product_code의 최대값 조회
        cursor.execute('SELECT MAX(product_code) FROM product')
        max_code = cursor.fetchone()[0]
        new_product_code = int(max_code) + 1 if max_code is not None else 1

        # 5자리 문자열 포맷으로 변환
        new_product_code = f"{new_product_code:05d}"

        cursor.execute('''
               INSERT INTO product (product_code, product_name, alcohol_type, unit, quantity_per_box, product_price, product_amount, product_nickname)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                     (new_product_code, data['product_name'], data['alcohol_type'], data['unit'],
                      data['quantity_per_box'], data['product_price'], data['product_amount'],
                      data['product_nickname']))

        conn.commit()

        # Get the ID of the newly inserted product
        new_id = cursor.lastrowid

        # Return the success message with the new ID
        return {'message': 'Product added successfully', 'product_id': new_id, 'product_code': new_product_code}

    except Exception as e:
        return {'message': f'Error: {str(e)}'}
    finally:
        conn.close()

@app.route('/product/<int:product_id>', methods=['PUT'])
def edit_product(product_id, data):
    conn = get_db_connection()
    try:
        conn.execute('''
            UPDATE product SET product_name=?, alcohol_type=?, unit=?, quantity_per_box=?, product_price=?, product_amount=?, product_nickname=?
            WHERE id=?''',
            (data['product_name'], data['alcohol_type'], data['unit'],
             data['quantity_per_box'], data['product_price'], data['product_amount'], data['product_nickname'], product_id))
        conn.commit()
        return {'message': 'Product updated successfully'}  # ✅ dict로 반환
    except Exception as e:
        return {'message': f'Error: {str(e)}'}
    finally:
        conn.close()

@app.route('/product/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    try:
        conn = get_db_connection()
        conn.execute('DELETE FROM product WHERE id = ?', (product_id,))
        conn.commit()
        return {'message': 'Product deleted successfully'}  # ✅ dict로 반환
    except Exception as e:
        return {'message': f'Error: {str(e)}'}
    finally:
        conn.close()

if __name__ == '__main__':
    app.run(debug=True)
