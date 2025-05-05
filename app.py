from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, firestore
from typing import List, Dict, Any

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "https://updatedatahomesale.netlify.app"}})


# ------------------- Firebase Init -------------------
cred = credentials.Certificate("assets/configkey.json")  # Ganti dengan path file key kamu
firebase_admin.initialize_app(cred)
db = firestore.client()
collection_name = "products"

# ------------------- Helper Functions -------------------
def validate_product_id(product_id: int) -> bool:
    return isinstance(product_id, int) and product_id > 0

def is_duplicate_id(product_id: int) -> bool:
    doc = db.collection(collection_name).document(str(product_id)).get()
    return doc.exists

def is_duplicate_number(number: int) -> bool:
    docs = db.collection(collection_name).where("number", "==", number).stream()
    return any(True for _ in docs)

# ------------------- API Routes -------------------
@app.route('/api/products', methods=['GET'])
def get_products():
    docs = db.collection(collection_name).stream()
    return jsonify([doc.to_dict() for doc in docs])

@app.route('/api/products/<int:product_id>', methods=['GET'])
def get_product(product_id: int):
    doc = db.collection(collection_name).document(str(product_id)).get()
    if doc.exists:
        return jsonify(doc.to_dict())
    return jsonify({"status": "error", "message": "Product not found"}), 404

@app.route('/api/products/add', methods=['POST'])
def add_product():
    form_data = request.form

    try:
        product_id = int(form_data.get('id', 0))
        number = int(form_data.get('number', 0))

        if not validate_product_id(product_id):
            return jsonify({"status": "error", "message": "Invalid product ID"}), 400

        if is_duplicate_id(product_id):
            return jsonify({"status": "error", "message": f"ID {product_id} already exists"}), 400

        if is_duplicate_number(number):
            return jsonify({"status": "error", "message": f"Number {number} already exists"}), 400

        new_product = {
            "id": product_id,
            "number": number,
            "name": form_data.get('name', '').strip(),
            "category": form_data.get('category', '').strip(),
            "price": int(form_data.get('price', 0)),
            "originalPrice": int(form_data.get('originalPrice', 0)),
            "image": form_data.get('image', '').strip(),
            "images": [img for img in request.form.getlist('images[]') if img.strip()],
            "link": form_data.get('link', '').strip(),
            "rating": float(form_data.get('rating', 0)),
            "reviews": int(form_data.get('reviews', 0)),
            "ribuan": form_data.get('ribuan', '').strip(),
            "stock": int(form_data.get('stock', 0)),
            "description": form_data.get('description', '').strip(),
            "specifications": form_data.get('specifications', '').strip(),
            "features": [ft for ft in request.form.getlist('features[]') if ft.strip()]
        }

        db.collection(collection_name).document(str(product_id)).set(new_product)
        return jsonify({"status": "success", "message": "Product added successfully", "product": new_product})

    except ValueError as e:
        return jsonify({"status": "error", "message": f"Invalid input: {str(e)}"}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": f"Server error: {str(e)}"}), 500

@app.route('/api/products/update', methods=['POST'])
def update_product():
    form_data = request.form

    try:
        product_id = int(form_data.get('id', 0))
        if not validate_product_id(product_id):
            return jsonify({"status": "error", "message": "Invalid product ID"}), 400

        ref = db.collection(collection_name).document(str(product_id))
        doc = ref.get()
        if not doc.exists:
            return jsonify({"status": "error", "message": "Product not found"}), 404

        product = doc.to_dict()

        if 'number' in form_data:
            new_number = int(form_data['number'])
            if new_number != product.get('number') and is_duplicate_number(new_number):
                return jsonify({"status": "error", "message": f"Number {new_number} already exists"}), 400

        update_fields = [
            "number", "name", "category", "price", "originalPrice",
            "image", "link", "rating", "reviews", "ribuan",
            "stock", "description", "specifications"
        ]

        for field in update_fields:
            if field in form_data:
                val = form_data[field]
                if val == '':
                    product[field] = 0 if field in ["price", "originalPrice", "reviews", "stock", "number"] else 0.0 if field == "rating" else ''
                else:
                    product[field] = int(val) if field in ["price", "originalPrice", "reviews", "stock", "number"] else float(val) if field == "rating" else val.strip()

        if 'images[]' in form_data:
            product['images'] = [img for img in request.form.getlist('images[]') if img.strip()]
        if 'features[]' in form_data:
            product['features'] = [ft for ft in request.form.getlist('features[]') if ft.strip()]

        ref.set(product)
        return jsonify({"status": "success", "message": "Product updated successfully", "product": product})

    except ValueError as e:
        return jsonify({"status": "error", "message": f"Invalid input: {str(e)}"}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": f"Server error: {str(e)}"}), 500

@app.route('/api/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id: int):
    ref = db.collection(collection_name).document(str(product_id))
    if not ref.get().exists:
        return jsonify({"status": "error", "message": "Product not found"}), 404

    ref.delete()
    return jsonify({"status": "success", "message": "Product deleted successfully"})

@app.route('/images/<path:filename>')
def serve_images(filename):
    return send_from_directory('images', filename)

# ------------------- Main Entry -------------------
if __name__ == '__main__':
    app.run(debug=True, port=5000)
