from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3
import os
from datetime import datetime

app = Flask(__name__, static_folder='static')
CORS(app)

def init_database():
    os.makedirs('data', exist_ok=True)
    conn = sqlite3.connect('data/database.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inverters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            brand TEXT NOT NULL,
            model TEXT NOT NULL,
            model_series TEXT,
            supported_protocols TEXT,
            max_voltage REAL,
            max_current INTEGER,
            firmware_version TEXT,
            photo_url TEXT,
            notes TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS batteries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            brand TEXT NOT NULL,
            model TEXT NOT NULL,
            model_series TEXT,
            voltage REAL,
            capacity_ah INTEGER,
            chemistry TEXT,
            max_charge_current INTEGER,
            max_discharge_current INTEGER,
            firmware_version TEXT,
            photo_url TEXT,
            notes TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS compatibility (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            inverter_id INTEGER,
            battery_id INTEGER,
            protocol TEXT NOT NULL,
            baud_rate TEXT,
            pin_definition_can_h TEXT,
            pin_definition_can_l TEXT,
            pin_definition_rs485_a TEXT,
            pin_definition_rs485_b TEXT,
            pin_definition_gnd TEXT,
            cable_type TEXT,
            inverter_firmware_required TEXT,
            battery_firmware_required TEXT,
            inverter_setup_instructions TEXT,
            additional_notes TEXT,
            wiring_diagram_url TEXT,
            compatibility_status TEXT DEFAULT 'verified',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (inverter_id) REFERENCES inverters(id),
            FOREIGN KEY (battery_id) REFERENCES batteries(id)
        )
    ''')
    
    conn.commit()
    conn.close()

def insert_initial_data():
    conn = sqlite3.connect('data/database.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM inverters")
    if cursor.fetchone()[0] > 0:
        conn.close()
        return
    
    inverters_data = [
        ('Growatt', 'SPF 3000TL LVM-ES', 'TL-LVM-ES', 'CAN,RS485', 48, 3000, 'V1.05', None, None),
        ('Growatt', 'SPF 5000TL HVM-ES', 'TL-HVM-ES', 'CAN,RS485', 48, 5000, 'V1.04', None, None),
        ('Victron', 'MultiPlus-II 48/3000/35-32', 'MultiPlus-II', 'CAN,RS485', 48, 3000, 'V1.08', None, None),
        ('SMA', 'Sunny Boy Storage 3.7', 'SBS', 'CAN', 48, 3700, '1.00.20.R', None, None),
        ('Deye', 'SUN-3K-SG04LP1-EU', 'SG04LP1', 'CAN,RS485', 48, 3000, 'V1.02', None, None),
    ]
    
    cursor.executemany('''
        INSERT INTO inverters 
        (brand, model, model_series, supported_protocols, max_voltage, max_current, firmware_version, photo_url, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', inverters_data)
    
    batteries_data = [
        ('Pylontech', 'US2000C', 'US', 48, 2400, 'LiFePO4', 100, 100, 'V3.012R', None, None),
        ('Pylontech', 'US3000C', 'US', 48, 3600, 'LiFePO4', 100, 100, 'V3.012R', None, None),
        ('BYD', 'Battery-Box Premium HVS 5.1', 'HVS', 48, 5100, 'LiFePO4', 100, 100, 'V3.012R', None, None),
    ]
    
    cursor.executemany('''
        INSERT INTO batteries 
        (brand, model, model_series, voltage, capacity_ah, chemistry, max_charge_current, max_discharge_current, firmware_version, photo_url, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', batteries_data)
    
    cursor.execute("SELECT id, brand, model FROM inverters")
    inverters_dict = {f"{row[1]}_{row[2]}": row[0] for row in cursor.fetchall()}
    
    cursor.execute("SELECT id, brand, model FROM batteries")
    batteries_dict = {f"{row[1]}_{row[2]}": row[0] for row in cursor.fetchall()}
    
    compatibility_data = [
        (inverters_dict['Growatt_SPF 3000TL LVM-ES'], batteries_dict['Pylontech_US2000C'], 
         'CAN', '500K', '4', '5', None, None, '6', 'Straight', 'V1.05', 'V3.012R',
         'اضبط الإعداد: Lithium Mode = 00 (Pylontech)', 
         'يجب استخدام كيبل شبكة مستقيم (Straight) مع تعريفات CAN على PIN 4 و5',
         None, 'verified'),
        (inverters_dict['Victron_MultiPlus-II 48/3000/35-32'], batteries_dict['Pylontech_US3000C'],
         'CAN', '500K', '7', '8', None, None, '3', 'Crossover', 'V1.08', 'V3.012R',
         'اضبط الإعداد: Battery Type = Lithium, Protocol = Pylontech',
         'Victron يستخدم PIN 7 و8 لـ CAN بينما Pylontech يستخدم 4 و5. استخدم كابل متقاطع (Crossover)',
         None, 'verified'),
        (inverters_dict['SMA_Sunny Boy Storage 3.7'], batteries_dict['BYD_Battery-Box Premium HVS 5.1'],
         'CAN', '500K', '4', '5', None, None, '6', 'Straight', '1.00.20.R', 'V3.012R',
         'اضبط الإعداد: CAN Protocol = BYD',
         'يجب تحديث الإنفرتر إلى الإصدار 1.00.20.R أو أحدث',
         None, 'verified'),
    ]
    
    cursor.executemany('''
        INSERT INTO compatibility 
        (inverter_id, battery_id, protocol, baud_rate, 
         pin_definition_can_h, pin_definition_can_l, 
         pin_definition_rs485_a, pin_definition_rs485_b, pin_definition_gnd, cable_type,
         inverter_firmware_required, battery_firmware_required,
         inverter_setup_instructions, additional_notes, wiring_diagram_url, compatibility_status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', compatibility_data)
    
    conn.commit()
    conn.close()
    print("✅ تم إدخال البيانات الأولية بنجاح!")

def get_db_connection():
    conn = sqlite3.connect('data/database.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/api/data', methods=['GET'])
def get_data():
    conn = get_db_connection()
    inverters = conn.execute('SELECT * FROM inverters ORDER BY brand, model').fetchall()
    batteries = conn.execute('SELECT * FROM batteries ORDER BY brand, model').fetchall()
    compatibility = conn.execute('SELECT * FROM compatibility ORDER BY id DESC').fetchall()
    conn.close()
    return jsonify({
        'inverters': [dict(row) for row in inverters],
        'batteries': [dict(row) for row in batteries],
        'compatibility': [dict(row) for row in compatibility]
    })

@app.route('/api/compatibility', methods=['POST'])
def add_compatibility():
    data = request.json
    required = ['inverter_id', 'battery_id', 'protocol']
    for field in required:
        if field not in data:
            return jsonify({'error': f'Missing field: {field}'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO compatibility 
        (inverter_id, battery_id, protocol, baud_rate, 
         pin_definition_can_h, pin_definition_can_l, 
         pin_definition_rs485_a, pin_definition_rs485_b, pin_definition_gnd,
         cable_type, inverter_firmware_required, battery_firmware_required,
         inverter_setup_instructions, additional_notes, 
         wiring_diagram_url, compatibility_status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data['inverter_id'], data['battery_id'], data['protocol'],
        data.get('baud_rate', ''), data.get('pin_definition_can_h', ''),
        data.get('pin_definition_can_l', ''), data.get('pin_definition_rs485_a', ''),
        data.get('pin_definition_rs485_b', ''), data.get('pin_definition_gnd', ''),
        data.get('cable_type', ''), data.get('inverter_firmware_required', ''),
        data.get('battery_firmware_required', ''), data.get('inverter_setup_instructions', ''),
        data.get('additional_notes', ''), data.get('wiring_diagram_url', ''),
        data.get('compatibility_status', 'experimental')
    ))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return jsonify({'status': 'success', 'id': new_id}), 201

@app.route('/api/search', methods=['POST'])
def search_compatibility():
    data = request.json
    inverter_id = data.get('inverter_id')
    battery_id = data.get('battery_id')
    if not inverter_id or not battery_id:
        return jsonify({'error': 'Missing inverter_id or battery_id'}), 400
    
    conn = get_db_connection()
    result = conn.execute('''
        SELECT c.*, 
               i.brand as inverter_brand, i.model as inverter_model,
               b.brand as battery_brand, b.model as battery_model
        FROM compatibility c
        JOIN inverters i ON c.inverter_id = i.id
        JOIN batteries b ON c.battery_id = b.id
        WHERE c.inverter_id = ? AND c.battery_id = ?
    ''', (inverter_id, battery_id)).fetchone()
    conn.close()
    
    if result:
        return jsonify(dict(result))
    else:
        return jsonify({'found': False}), 404

if __name__ == '__main__':
    init_database()
    insert_initial_data()
    print("🚀 تشغيل الخادم على http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
