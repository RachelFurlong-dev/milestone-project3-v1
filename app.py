import os
from flask import (
    Flask, flash, render_template,
    redirect, request, session, url_for)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
if os.path.exists("env.py"):
    import env


app = Flask(__name__)

app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")

mongo = PyMongo(app)


# @login_required decorator
# https://flask.palletsprojects.com/en/2.0.x/patterns/viewdecorators/#login-required-decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # no "user" in session
        if "user" not in session:
            flash("You must log in to view this page")
            return redirect(url_for("login"))
        # user is in session
        return f(*args, **kwargs)
    return decorated_function


@app.route("/")
@app.route("/get_houseplants")
def get_houseplants():
    houseplants = list(mongo.db.houseplants.find())
    return render_template("houseplants.html", houseplants=houseplants)


@app.route("/search", methods=["GET", "POST"])
def search():
    query = request.form.get("query")
    houseplants = list(mongo.db.houseplants.find(
                        {"$text": {"$search": query}}))
    return render_template("houseplants.html", houseplants=houseplants)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # check if username already exists in db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            flash("Username already exists")
            return redirect(url_for("register"))

        register = {
            "username": request.form.get("username").lower(),
            "password": generate_password_hash(request.form.get("password")),
            "avatar": request.form.get("avatar").lower()
        }
        mongo.db.users.insert_one(register)

        # put the new user into 'session' cookie
        session["user"] = request.form.get("username").lower()
        flash("Registration Successful!")
        return redirect(url_for("profile", username=session["user"]))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # check if username exists in db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            # ensure hashed password matches user input
            if check_password_hash(
                    existing_user["password"], request.form.get("password")):
                    session["user"] = request.form.get("username").lower()
                    flash("Welcome, {}".format(request.form.get("username")))
                    return redirect(url_for(
                            "profile", username=session["user"]))
            else:
                # invalid password match
                flash("Incorrect Username and/or Password")
                return redirect(url_for("login"))

        else:
            # username doesn't exist
            flash("Incorrect Username and/or Password")
            return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/profile/<username>", methods=["GET", "POST"])
def profile(username):
    # grab the session user's username from db
    user = mongo.db.users.find_one(
        {"username": session["user"]})

    if session["user"]:
        return render_template("profile.html", user=user)

    return redirect(url_for("login"))


@app.route("/logout")
def logout():
    # remove user from session cookie
    flash("You have been logged out")
    session.pop("user")
    return redirect(url_for("login"))


# function to add houseplant record to database
@app.route("/add_houseplant", methods=["GET", "POST"])
def add_houseplant():
    if request.method == "POST":
        houseplant = {
            "category_name": request.form.get("category_name"),
            "horticultural_name": request.form.get("horticultural_name"),
            "common_name": request.form.get("common_name"),
            "image_url": request.form.get("image_url"),
            "description": request.form.get("description"),
            "houseplant_care": request.form.get("houseplant_care"),
            "date": request.form.get("date"),
            "created_by": session["user"]
        }
        mongo.db.houseplants.insert_one(houseplant)
        flash("Houseplant Successfully Added")
        return redirect(url_for("get_houseplants"))

    categories = mongo.db.categories.find().sort("category_name", 1)
    return render_template("add_houseplant.html", categories=categories)


# function to update houseplant record in database
@app.route("/edit_houseplant/<houseplant_id>", methods=["GET", "POST"])
def edit_houseplant(houseplant_id):
    if request.method == "POST":
        submit = {
            "category_name": request.form.get("category_name"),
            "horticultural_name": request.form.get("horticultural_name"),
            "common_name": request.form.get("common_name"),
            "image_url": request.form.get("image_url"),
            "description": request.form.get("description"),
            "houseplant_care": request.form.get("houseplant_care"),
            "date": request.form.get("date"),
            "created_by": session["user"]
        }
        mongo.db.houseplants.replace_one(
                            {"_id": ObjectId(houseplant_id)}, submit)
        flash("Houseplant Successfully Updated")

    houseplant = mongo.db.houseplants.find_one(
                        {"_id": ObjectId(houseplant_id)})
    categories = mongo.db.categories.find().sort("category_name", 1)
    return render_template(
                        "edit_houseplant.html", houseplant=houseplant,
                        categories=categories)


# function to delete houseplant record from database
@app.route("/delete_houseplant/<houseplant_id>")
def delete_houseplant(houseplant_id):
    mongo.db.houseplants.delete_one({"_id": ObjectId(houseplant_id)})
    flash("Houseplant Successfully Deleted")
    return redirect(url_for("get_houseplants"))


# function to select categories
@app.route("/get_categories")
def get_categories():
    categories = list(mongo.db.categories.find().sort("category_name", 1))
    return render_template("categories.html", categories=categories)


# function to add category to database
@app.route("/add_category", methods=["GET", "POST"])
def add_category():
    if request.method == "POST":
        category = {
            "category_name": request.form.get("category_name")
        }
        mongo.db.categories.insert_one(category)
        flash("New Category Added")
        return redirect(url_for("get_categories"))

    return render_template("add_category.html")


# function to edit category in database
@app.route("/edit_category/<category_id>", methods=["GET", "POST"])
def edit_category(category_id):
    if request.method == "POST":
        submit = {
            "category_name": request.form.get("category_name")
        }
        mongo.db.categories.replace_one({"_id": ObjectId(category_id)}, submit)
        flash("Category Successfully Updated")
        return redirect(url_for("get_categories"))

    category = mongo.db.categories.find_one({"_id": ObjectId(category_id)})
    return render_template("edit_category.html", category=category)


# function to delete category from database
@app.route("/delete_category/<category_id>")
def delete_category(category_id):
    mongo.db.categories.delete_one({"_id": ObjectId(category_id)})
    flash("Category Successfully Deleted")
    return redirect(url_for("get_categories"))


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=True)
