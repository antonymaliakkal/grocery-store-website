from flask import request,jsonify
from celery_app import app, sendProductSummary
from db_instance import db
from app import redis_store
from models import*
from flask_jwt_extended import create_access_token,jwt_required,get_jwt_identity
import json
from datetime import datetime

def fetch_redis(x):
    data = redis_store.get(x)
    if data is not None:
        data = data.decode('utf-8')
    else:
        data = "Key doesn't exist in Redis"
    return data



@app.route('/signup' , methods = ['POST'])
def signup():
    data = request.get_json()
    new_user = User(username = data.get('email') , password = data.get('password') , role = 'user')
    db.session.add(new_user)
    db.session.commit()

    # access_token = create_access_token(identity=new_user.id, additional_claims={'role': 'user'})

    if data.get('role') == 'manager':
        user = User.query.filter_by(username=data['email']).first()
        new_request = Manager_request(user_id = user.id)
        db.session.add(new_request)
        db.session.commit()

    return jsonify({'message': 'Item added successfully'})

@app.route('/login' , methods = ['POST','GET'])
def login():
    data = request.get_json()
    user = User.query.filter_by(username=data['email']).first()
    if not user or user.password != data['password']:
       return jsonify({'message' : 'Incorrect password/user' , 'login' : False})
    # access_token = create_access_token(identity=user.id, additional_claims={'role': user.role})
    user.last_visited = func.now()
    db.session.commit()
    access_token = create_access_token(identity={'id': user.id, 'role': user.role},expires_delta=False)   
    print(access_token)
    return jsonify({'message' : 'Login successful' , 'login' : True , 'access_token' : access_token , 'role' : user.role, 'username': user.username , 'user_id' : user.id})
        
    
@app.route('/manager_request' , methods = ['POST','GET', 'PUT'])
@jwt_required()
def manager_request():

    if request.method == 'GET':
  
        print('11111111111')
        current_user = get_jwt_identity()
        print(current_user)

        if current_user['role'] != 'admin': 
            print(current_user['id'])
            return jsonify({'message' : 'only admin access'})

        name = {}
        temp = db.session.query(User).join(Manager_request).filter(User.id == Manager_request.user_id).all()
        print(temp)
        for i in temp:
            name[i.id] = i.username
        return jsonify({'user': name})

    elif request.method == 'POST':

        current_user = get_jwt_identity()
        print(current_user)

        if current_user['role'] != 'admin': 
            print(current_user['id'])
            return jsonify({'message' : 'only admin access'})

        data = request.get_json()
        Manager_request.query.filter(Manager_request.user_id == data['key']).delete()
        temp = User.query.filter(User.id == data['key']).first()
        temp.role = 'manager'
        db.session.commit()
        return jsonify({'message' : 'changed role'})

    elif request.method == 'PUT':

        current_user = get_jwt_identity()
        print(current_user)

        if current_user['role'] != 'admin': 
            print(current_user['id'])
            return jsonify({'message' : 'only admin access'})

        data = request.get_json()
        Manager_request.query.filter(Manager_request.user_id == data['key']).delete()
        User.query.filter(User.id == data['key']).delete()
        db.session.commit()
        return jsonify({'message' : 'request rejected'})

@app.route('/create_category',methods = ['POST','GET'])
def create_cat():
    data = request.get_json()
    new_cat = Category(name = data.get('name') , description = data.get('desc') )
    db.session.add(new_cat)
    db.session.commit()
    data = {'key': new_cat.id, 'value':{'name': new_cat.name, 'desc':new_cat.description}}
    return jsonify({'message' : 'Category created', 'data':data})

@app.route('/category_request',methods = ['POST', 'GET', 'PUT', 'DELETE'])
def create_cat_req():
    if request.method == 'POST':
        data = request.get_json()
        new_cat = CategoryRequest(name = data.get('name') , description = data.get('description') )
        db.session.add(new_cat)
        db.session.commit()
        data = {'key': new_cat.id, 'value':{'name': new_cat.name, 'description':new_cat.description}}
        return jsonify({'message' : 'Category created', 'data':data})
    
    elif request.method == 'GET':
        requests = CategoryRequest.query.filter_by(status=StatusEnum.PENDING).all()
        req_doc = {}
        for i in requests:
            req_doc[i.id] = {'name': i.name, 'description': i.description}
        return jsonify({'requests': req_doc})
    
    elif request.method == 'PUT':
        data = request.get_json()
        req = CategoryRequest.query.filter_by(id=data['id']).first()
        new_cat = Category(name = req.name , description = req.description)
        db.session.add(new_cat)
        req.status = StatusEnum.INACTIVE
        db.session.commit()
        return jsonify({'message' : 'Request accepted'})
    
    elif request.method == 'DELETE':
        data = request.get_json()
        CategoryRequest.query.filter_by(id = data['id']).update({'status': StatusEnum.INACTIVE})
        db.session.commit()
        return jsonify({'message' : 'Request rejected'})

@app.route('/edit_category' , methods = ['PATCH','GET','POST'])
def edit_cat():
    if request.method == 'GET':
        cat = []
        cat_new = {}
        temp = Category.query.all()
        for i in temp:
            cat.append({'key' : i.id , 'value' : {'name' : i.name , 'desc' : i.description}})
            cat_new[i.id] = {'name' : i.name , 'desc' : i.description}
        return jsonify({'category':cat , 'category_new' : cat_new})
    
    elif request.method == 'PATCH':
        data = request.get_json()
        print(data)
        print(data.get('id'))
        cat = Category.query.get(data.get('id'))
        print(cat)
        if cat:
            cat.name = data.get('name')
            cat.description = data.get('desc')
            db.session.commit()
            data = {'key': cat.id, 'value':{'name': cat.name, 'desc': cat.description}}
            return {'message' : 'Category edited', 'data': data}
        return jsonify({'message' : 'Category error'})
    
    elif request.method == 'POST':
        temp = request.get_json()
        print(temp)
        prod = Product.query.filter_by(cat_id=temp['cat']).all()
        print(prod)
        for i in prod:
            db.session.delete(i)
        cat = Category.query.get(temp['cid'])
        db.session.delete(cat)
        db.session.commit()
        return jsonify({'message' : 'Category deleted'})

@app.route('/create_product' , methods = ['POST','GET'])
def create_prod():
    if request.method == 'GET':
        name = []
        temp = Category.query.all()
        for i in temp:
            # name[i.id] = i.name
            name.append({'key':i.id , 'value' : i.name })
        return jsonify({'category':name})
    
    if request.method == 'POST':
        data = request.get_json()
        new_prod = Product(cat_id = data.get('cat_id'),name = data.get('name') , description = data.get('desc') , price = data.get('price'),stock = data.get('stock'))
        db.session.add(new_prod)
        db.session.commit()
        return jsonify({'message' : 'Product created'})
    


@app.route('/view_product',methods=['GET'])
def view_prod():
    product = {}
    temp = db.session.query(Product)
    for i in temp:
        product[i.id] = {'id' : i.id , 'name' : i.name , 'cat' : i.cat_id , 'desc' : i.description , 'price' : i.price , 'stock' : i.stock}
    return jsonify({'product': product})

@app.route('/edit_product',methods=['POST'])
def edit_prod():
    data = request.get_json()
    print(data.get('id'))

    prod = Product.query.filter_by(id=data['id']).update(data)
    # if cat:
    #     cat.name = data.get('name')
    #     cat.description = data.get('desc')
    db.session.commit()
    # data = {'key': cat.id, 'value':{'name': cat.name, 'desc': cat.description}}
    return {'message' : 'Product edited', 'data': prod}
    # return jsonify({'message' : 'Category error'})

# @app.route('/filter_products',methods=['GET'])
    


@app.route('/delete_product',methods=['POST','GET'])
def delete_prod():
    data = request.get_json()
    print(data)
    p_id = data['pid']
    prod = Product.query.get(p_id)
    print(prod)
    db.session.delete(prod)
    db.session.commit()
    return jsonify({'message' : 'Product deleted'})

@app.route('/view_category',methods=['GET','POST'])
def view_cat():
    category = {}
    temp = db.session.query(Category)
    for i in temp:
        category[i.id] = i.name

    return jsonify({'category': category})

@app.route('/delete_category',methods=['GET','POST'])
def delete_category():
    products = []
    temp = request.get_json()
    print(temp)
    prod = Product.query.filter_by(cat_id=temp['id']).all()
    print(prod)
    for i in prod:
        db.session.delete(i)
    cat = Category.query.get(temp['id'])
    db.session.delete(cat)
    db.session.commit()
    return jsonify({'message' : 'Category deleted'})

@app.route('/cart',methods=['POST','DELETE','GET'])
@jwt_required()
def add_cart():
    if request.method == 'POST':
        current_user = get_jwt_identity()
        print(current_user)
        data = request.get_json()
        print(data)
        new_cart = Cart(user_id = data.get('user_id') , product_id = data.get('p_id') , quantity = data.get('qty'))
        db.session.add(new_cart)
        db.session.commit()
        return jsonify({'message' : 'added to cart'})

    elif request.method =='GET':
        print('before')
        current_user = get_jwt_identity()
        current_user = current_user['id']
        # print('after')
        print('CURRENT USER ID  : ',current_user)
        user = db.session.query(Cart,Product).join(Product , Cart.product_id == Product.id).filter(Cart.user_id == current_user).all()
        # print(user)
        temp = {}
        for cart,product in user:
            temp[cart.id] = {'id' : cart.id ,'quantity' : cart.quantity , 'name' : product.name , 'price' : product.price}
        # print(temp)
        return jsonify({'cart' : temp})    


@app.route('/cart_delete' , methods = ['POST','DELETE'])
def cart_deleted():
        print('cart delete')
        data = request.get_json()
        cart = Cart.query.get(data['id'])
        db.session.delete(cart)
        db.session.commit()
        return jsonify({'message' : 'Cart Item deleted'})

@app.route('/cache',methods=['POST','GET'])
def caching():    
    data = request.get_json()
    print(data)
    search = data['search']
    print(search)
    data = redis_store.get(search)
    print('redis data : ',data)
    if data is not None:
        data = json.loads(data)
        return jsonify({'product' : data , 'message' : 'fetched from redis'})
    else:
        prod = Product.query.filter(Product.name.ilike('%{}%'.format(search))).all()
        print(prod)
        if prod == []:
            return jsonify({'product' : {} , 'message' : 'no product'})
        else:
            temp = {}
            for i in prod:
                x = {}
                temp[i.id] = { 'id' : i.id , 'name' : i.name , 'cat' : i.cat_id , 'desc' : i.description , 'price' : i.price , 'stock' : i.stock }
                x[i.id] = temp[i.id]
                x = json.dumps(x)
                print(x)
                redis_store.set(i.name, x)
                redis_store.expire(i.name,3600)
                print('ADDED TO REDIS' , i.name)
            return jsonify({'product' : temp , 'message':'fetched from database'})
        
@app.route("/productsummary", methods=['POST'])
@jwt_required()
def mailProds():
    mail = request.get_json()['mail']
    sendProductSummary(mail)
    return jsonify({'message':'Sumary report email scheduled'})
    
@app.route('/order' , methods=['POST','GET'])
@jwt_required()
def checkout():
    current_user = get_jwt_identity()
    current_user = current_user['id']
    print(current_user)

    cart = Cart.query.filter_by(user_id=current_user).all()
    print(cart)
    print(datetime.now())

    #creating a new order
    new_order = Orders(order_user = current_user , date = datetime.now())
    db.session.add(new_order)
    db.session.commit()

    order = new_order.order_id
    print(new_order.order_id)

    for i in cart:
        #reduce the product stock
        print('reducing stock')
        print(i.product_id)
        prod = Product.query.filter(Product.id == i.product_id).first()
        print(prod , i.quantity)
        prod.stock = prod.stock - i.quantity
        db.session.commit()
        print('reduced stock')

        #add products to OrderProducts table
        print('adding product to orders')
        new_product = OrderProducts(order_id = order , product_id = i.product_id , quantity = i.quantity)
        db.session.add(new_product)
        db.session.commit() 
        print('added product to orders')

        #delete product from cart
        print('deleting product from cart')
        db.session.delete(i)
        db.session.commit()
        print('deleted product from cart')


    return jsonify({'message' : 'added to order'})
