from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
import json
import os

app = Flask(__name__)
CORS(app)

MONGO_URI = os.getenv('MONGO_URI', 'mongodb+srv://root:root@cluster0.43xtneg.mongodb.net/')
client = MongoClient(MONGO_URI)
db = client['BazarUniversal']
productCollection = db['products']
SaleCollection = db['sales']

if productCollection.count_documents({}) == 0:
    with open('products.json') as f:
        products = json.load(f)
        productCollection.insert_many(products)

@app.route('/api/items', methods=['GET'])
def get_items():
    query = request.args.get('search', '')
    if query:
        regex = {'$regex': query, '$options': 'i'}
        res = list(productCollection.find({
            '$or': [
                {'title': regex},
                {'description': regex},
                {'category': regex},
                {'brand': regex}
            ]
        }))
    else:
        res = list(productCollection.find())

    for item in res:
        item['_id'] = str(item['_id'])

    return jsonify(res), 200

@app.route('/api/items/<int:productId>', methods=['GET'])
def get_item(productId):
    item = productCollection.find_one({'id': productId})
    if item:
        item['_id'] = str(item['_id']) 
        return jsonify(item), 200
    else:
        return jsonify({'error': 'Producto no encontrado'}), 404
    
    
@app.route('/api/addSale', methods=['POST'])
def add_sale():
    data = request.json
    if not data or 'item_id' not in data:
        return jsonify({'success': False, 'message': 'Datos inválidos'}), 400

    from bson.objectid import ObjectId
    item = productCollection.find_one({'_id': ObjectId(data['item_id'])})
    if not item:
        return jsonify({'success': False, 'message': 'Item no encontrado'}), 404

    # Registro venta
    sale = {
        'item_id': data['item_id'],
        'id': item.get('id'),
        'title': item.get('title'),
        'price': item.get('price'),
        'quantity': data.get('quantity', 1),
        'date': data.get('date') 
    }
    result = SaleCollection.insert_one(sale)
    if result.inserted_id:
        return jsonify({'success': True}), 201
    else:
        return jsonify({'success': False}), 500

@app.route('/api/sales', methods=['GET'])
def get_sales():
    sales = list(SaleCollection.find())
    for sale in sales:
        sale['_id'] = str(sale['_id'])
    return jsonify(sales), 200

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)