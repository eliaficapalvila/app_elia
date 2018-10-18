from flask import Flask
from flask import render_template
from flask_pymongo import PyMongo
from flask import abort, jsonify, redirect, render_template
from flask import request, url_for
from forms import ProductForm
from bson.objectid import ObjectId
from flask_login import LoginManager, current_user
from flask_login import login_user, logout_user
from flask_login import login_required

from forms import LoginForm
from models import User

import json

import bson

app = Flask(__name__)

app.config['MONGO_DBNAME'] = 'ads'
app.config['MONGO_URI'] = 'mongodb://elia.fivi:Elefant9213@ds135653.mlab.com:35653/ads'

mongo = PyMongo(app)

app.config['SECRET_KEY'] = 'enydM2ANhdcoKwdVa0jWvEsbPFuQpMjf' # Create your own.
app.config['SESSION_PROTECTION'] = 'strong'


# Use Flask-Login to track current user in Flask's session.
login_manager = LoginManager()
login_manager.setup_app(app)
login_manager.login_view = 'login'



@login_manager.user_loader
def load_user(user_id):
    """Flask-Login hook to load a User instance from ID."""
    u = mongo.db.users.find_one({"username":user_id})
    if not u:
        return None
    return User(u['username'])

@app.errorhandler(404)
def error_not_found(error):
    return render_template('error/not_found.html'), 404

@app.errorhandler(bson.errors.InvalidId)
def error_not_found(error):
    return render_template('error/not_found.html'), 404

@app.route('/products/create/', methods=['GET', 'POST'])
@login_required
def product_create():
    """Provide HTML form to create a new product."""
    form = ProductForm(request.form)
    if request.method == 'POST' and form.validate():
        mongo.db.products.insert_one(form.data)
        # Success. Send user back to full product list.
        return redirect(url_for('products_list'))
    # Either first load or validation error at this point.
    return render_template('product/edit.html', form=form)


@app.route('/products/')
def products_list():
    """Provide HTML listing of all Products."""
    # Query: Get all Products objects, sorted by date.
    products = mongo.db.products.find()[:]
    return render_template('product/index.html',
                           products=products)

@app.route('/')
def index():
    return redirect(url_for('products_list'))

@app.route('/products/<product_id>/')
def product_detail(product_id):
    """Provide HTML page with a given product."""
    # Query: get Product object by ID.
    product = mongo.db.products.find_one({ "_id": ObjectId(product_id) })
    print (product)
    if product is None:
        # Abort with Not Found.
        abort(404)
    return render_template('product/detail.html',
                           product=product)

@app.route('/products/<product_id>/delete/', methods=['DELETE'])
@login_required
def product_delete(product_id):
    """Delete record using HTTP DELETE, respond with JSON."""
    result = mongo.db.products.delete_one({ "_id": ObjectId(product_id) })
    if result.deleted_count == 0:
        # Abort with Not Found, but with simple JSON response.
        response = jsonify({'status': 'Not Found'})
        response.status = 404
        return response
    return jsonify({'status': 'OK'})

@app.route( '/products/<product_id>/edit/',methods=['GET', 'POST'])
@login_required
def product_edit(product_id):
    """Provide HTML form to edit a product."""
    form = ProductForm(request.form)
    if request.method == 'POST' and form.validate():
        
        mongo.db.products.update_one({'_id':ObjectId(product_id)},{'$set':{'name':request.form['name'], 'description':request.form['description'], 'price':request.form['price']}})
        
        # Success. Send user back to full product list.
        return redirect(url_for('products_list'))
    # Either first load or validation error at this point.
    return render_template('product/edit.html', form=form)


@app.route('/login/', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('products_list'))
    form = LoginForm(request.form)
    error = None
    if request.method == 'POST' and form.validate():
        username = form.username.data.lower().strip()
        password = form.password.data.lower().strip()
        user = mongo.db.users.find_one({"username": form.username.data})
        if user and User.validate_login(user['password'], form.password.data):
            user_obj = User(user['username'])
            login_user(user_obj)
            return redirect(url_for('products_list'))
        else:
            error = 'Incorrect username or password.'
    return render_template('user/login.html',
                           form=form, error=error)

@app.route('/logout/')
def logout():
    logout_user()
    return redirect(url_for('products_list'))

if __name__ == '__main__':
    app.run()

