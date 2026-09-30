from fastapi import FastAPI, Request
from fastapi import Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from config.db import admins , categories, customers
from config.db import menus, orders, tables
from bson import ObjectId
from fastapi import UploadFile, File
import shutil
import os
import json
from fastapi import Cookie

app = FastAPI()

app.mount("/static",StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        request= request,
        name= "index.html"
    )

@app.get("/create_admin")
def create_admin():
    admin = {
        "name": "Mohd Nazakat Ali",
        "email": "nazakat@gmail.com",
        "password": "1234"
    }

    admins.insert_one(admin)
    return {"message": "Admin Created."}

@app.get("/admin-login")
def admin_login(request: Request):
    return templates.TemplateResponse(
        name="admin/login.html",
        request= request
    )

@app.post("/admin-login")
def admin_login_check(
    email: str = Form(...),
    password: str = Form(...)
):
    admin = admins.find_one({
        "email": email,
        "password": password
    })
    if admin:
        return RedirectResponse(
            "/dashboard",
            status_code = 302
        )
    return {"message": "Invalid Admin."}

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    return templates.TemplateResponse(
        name = "admin/dashboard.html",
        request =  request,
    )

@app.get("/add-category", response_class=HTMLResponse)
def add_category_page(request: Request):
    return templates.TemplateResponse(
        name = "category/add_category.html",
        request = request
    )

@app.post("/add-category")
def add_category(
    name: str = Form(...)
):
    category = {
        "name": name
    }

    categories.insert_one(category)

    response=  RedirectResponse(
        "/view-category",
        status_code=302
    )

    response.set_cookie(
        "message",
        "Category Added"
    )
    return response

@app.get("/view-category", response_class=HTMLResponse)
def view_category(request: Request):
    data = categories.find()

    return templates.TemplateResponse(
        request = request,
        name= "category/view_category.html",
        context={
            "categories" : data
            }
        )

@app.get("/delete-category/{id}")
def delete_category(id: str):
    categories.delete_one({
        "_id":ObjectId(id)
    })
    return RedirectResponse(
        "/view-category",
        status_code=302
    )

# ----------------------------------- menus -----------------------------------

@app.get("/add-menu", response_class=HTMLResponse)
def add_menu_page(request: Request):
    category_data = categories.find()

    return templates.TemplateResponse(
        name = "menu/add_menu.html",
        request = request,
        context={
            "categories":category_data,
        }
    )

@app.post("/add-menu")
def add_menu(
    name: str = Form(...),
    price: int = Form(...),
    description: str = Form(...),
    category: str = Form(...),
    image: UploadFile = File(...)
):
    image_path = "static/images/" + image.filename

    with open(image_path,"wb") as buffer:
        shutil.copyfileobj(
            image.file,
            buffer
        )   

    menu = {
        "name": name,
        "price": price,
        "description": description,
        "category": category,
        "image": image.filename
    } 

    menus.insert_one(menu)
    return RedirectResponse(
        "/view-menu",
        status_code=302
    )

@app.get("/view-menu", response_class=HTMLResponse)
def view_menu(request: Request):
    print("VIEW MENU ROUTE CALLED")
    data = menus.find()
    return templates.TemplateResponse(
        request= request,
        name= "menu/view_menu.html",
        context={  
            "menus": data
        }
    )

@app.get("/delete-menu/{id}")
def delete_menu(id: str):
    menus.delete_one({
        "_id":ObjectId(id)
    })
    return RedirectResponse(
        "/view-menu",
        status_code=302
    )

# -------------------------------------Table------------------------------------

@app.get("/add-table", response_class=HTMLResponse)
def add_table_page(request: Request):
    return templates.TemplateResponse(
        name= "table/add_table.html",
        request= request
    )

@app.post("/add-table")
def add_table(
    table_no: int = Form(...),
    seats: int = Form(...),
    status: str = Form(...)
):
    table = {
        "table_no": table_no,
        "seats": seats, 
        "status": status
    }

    tables.insert_one(table)
    return RedirectResponse(
        "/view-table",
        status_code=302
    )

@app.get("/view-table", response_class=HTMLResponse)
def view_table(request: Request):
    data = tables.find()
    return templates.TemplateResponse(
        name ="table/view_table.html",
        request = request,
        context={
            "tables":data
        }
    )

@app.get("/delete-table/{id}")
def delete_table(id: str):
    tables.delete(
        {
            "_id": ObjectId(id)
        }
    )

    return RedirectResponse(
        "/view-table",
        status_code=302
    )

# ------------------------------------- orders -----------------------------

@app.get("/create-order", response_class=HTMLResponse)
def create_order_page(request: Request):
    menu_data = menus.find()
    table_data = tables.find({
        "status": "Available"
    })

    return templates.TemplateResponse(
        name= "order/create_order.html",
        request  = request,
        context={
            "tables": table_data,
            "menus": menu_data 
        }
    )

@app.post("/create-order")
def create_order(
    customer_name: str = Form(...),
    food: str = Form(...),
    quantity: int = Form(...),
    table: int = Form(...)
):
    menu = menus.find_one()

    total = menu["price"] * quantity

    order = {
        "customer_name": customer_name,
        "food": food,
        "quantity": quantity,
        "table": table,
        "total": total,
        "status": "pending"
    }

    orders.insert_one(order)
    return RedirectResponse(
        "/view-order",
        status_code=302
    )

@app.get("/view-order", response_class=HTMLResponse)
def view_order(request: Request):
    order_data = orders.find()
    return templates.TemplateResponse(
        name= "order/view_order.html",
        request = request,
        context={
            "orders": order_data
        }
    )

# --------------------------------- bill generation --------------------------
@app.get("/bill/{id}", response_class=HTMLResponse)
def generate_bill(
    request: Request,
    id: str
):
    order = orders.find_one({
        "_id": ObjectId(id)
    })
    gst = order["total"] * 0.18

    final_amount = order["total"] + gst

    return templates.TemplateResponse(
        name = "bill/bill.html",
        request = request,
        context = {
            "order": order,
            "gst": gst,
            "final_amount": final_amount
        }
    )

@app.get("/update-order-status/{id}/{status}")
def update_order_status(
    id: str,
    status: str
):
    orders.update_one(
        {
        "id": id,
        },
        {
            "$set" : {
                "status": status
            }
        }
    )
    return RedirectResponse(
        "/view-order",
        status_code=302
    )

#
# --------------------- delete-menu ------------------------------
# @app.get("/delete-menu/{id}")
# def delete_menu(id: str):
#     menus.delete_one(
#         {
#             "_id":ObjectId(id)
#         }
#     )   

#     return RedirectResponse(
#         "/view-menu",
#         status_code=303
#     )

# -------------------- update-menu --------------------------

@app.get("/update-menu/{id}", response_class=HTMLResponse)
def update_menu_page(
    request: Request,
    id: str
):
    menu = menus.find_one({
        "_id":ObjectId(id)
    })

    return templates.TemplateResponse(
        name = "menu/update_menu.html",
        request = request,
        context={
            "menu": menu
        }
    )

@app.post("/update-menu/{id}")
def update_menu(
    id: str,
    name: str = Form(...),
    price: int = Form(...),
    description: str = Form(...)
    ):

    menus.update_one(
        {
            "_id": ObjectId(id)
        },
        {
         "$set": {
             "name": name,
             "price": price,
             "description": description
         }  
        }
    )

    return RedirectResponse(
        "/view-menu",
        status_code= 302
    )

# ------------------------------------- search-menu -------------------------------------
@app.get("/search-menu", response_class=HTMLResponse)
def search_menu(
    request: Request,
    q: str
):
    result = menus.find(
        {
        "name":
        {
            "$regex": q,
            "$options": "i"
        }
    }
    )
    return templates.TemplateResponse(
        name = "menu/view_menu.html",
        request = request,
        context = {
            "menus": result
        }
    )

# ------------------------------- Add To Cart Route with cookies ------------------------------
@app.get("/add-cart/{id}")
def add_cart(
    id: str,
    cart: str = Cookie(None)
):
    if cart: 
        cart_data = json.loads(cart)
    else:
        cart_data = []

    found = False

    for item in cart_data:
        if item["id"] == id:
            item["qty"] += 1
            found = True

        if not found:
            cart_data.append({
                "id": id,
                "qty": 1
            })

    response = RedirectResponse(
        "/cart",
        status_code= 302
    )

    response.set_cookie(
        "cart",
        json.dumps(cart_data)
    )
    return response

@app.get("/cart", response_class=HTMLResponse)
def cart_page(
    request: Request,
    cart: str = Cookie(None)
):
    items = []
    total = 0
    if cart :
        cart_data = json.loads(cart)
        for item in cart_data:
            food = menus.find_one({
                "_id":ObjectId(id)
            })

            food["qty"] = item["qty"]
            food["subtotal"] = food["price"] * item["qty"]
            total += food["subtotal"]
            items.append(food)

    return templates.TemplateResponse(
        request= request,
        name = "customer/cart.html",
            context= {
            "items": items,
            "total": total
            }
        )

@app.get("/checkout")
def checkout(
    cart: str = Cookie(None),
    customer: str = Cookie(None)
):
    items = []
    total = 0

    cart_data = json.loads(cart)

    for item in cart_data:
        food = menus.find_one({
            "_id": ObjectId(item["id"])
        })

        items.append({
            "name": food["name"],
            "price": food["price"],
            "qty": food["qty"]
        })

        total += food["price"] * item["qty"]

        order = {
            "customer": customer,
            "items": items,
            "total": total,
            "status": "pending"
        }

        orders.insert_one(order)

        response = RedirectResponse(
            "/my-order",
            status_code= 302
        )

        response.delete_cookie(
            "cart"
        )

    return response

@app.get("/my-order", response_class=HTMLResponse)
def my_order(
    request: Request,
    customer: str = Cookie(None)
):
    data = orders.find_one({
        "customer": customer
    })

    return templates.TemplateResponse(
        name = "customer/my_order.html",
        request = request,
        context={
            "orders": data
        } 
   )


#  ---------------- customer Menu  -------------------

@app.get("/menu", response_class=HTMLResponse)
def customer_menu(request: Request):
    menu_data = menus.find()

    return templates.TemplateResponse(
        request = request,
        name = "customer/menu.html",
        context= {
            "menus": menu_data   
        }
    )

# -------------------- customer registration --------------------------------
@app.get("/registration", response_class=HTMLResponse)
def registration(request: Request):
    return templates.TemplateResponse(
        name= "customer/registration.html",
        request= request
    )

@app.post("/registration")
def registration(
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...)
):
    customer = {
        "name": name,
        "email": email,
        "password": password
    }

    if customer:
        return {"message":"Invalid"}

    customers.insert_one(customer)

    return RedirectResponse(
        "/login",
        status_code=302
    )

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(
        name = "customer/login.html",
        request = request
    )

@app.post("/login")
def login(
    email: str = Form(...),
    password: str = Form(...)
):
    customer = customers.find_one({
        "email": email,
        "password": password
    })
    if customer:
        response = RedirectResponse(
            "/menu",
            status_code= 302
        )
        response.set_cookie(
            "customer",
            email
        )
        return response
    return{"message": "Invalid Login"}

# ------------------------------- 404 ERROR -------------------------------

@app.exception_handler(404)
async def not_found(
    request: Request,
    exc
):
    return templates.TemplateResponse(
        request= request,
        name= "error/404.html",
        context={
            "status_code": 404
        }
    )