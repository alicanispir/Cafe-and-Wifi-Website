from flask import Flask, jsonify, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import select
import random
from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, IntegerField, DecimalField, SubmitField
from wtforms.validators import DataRequired, URL, NumberRange
'''
Install the required packages first: 
Open the Terminal in PyCharm (bottom left). 

On Windows type:
python -m pip install -r requirements.txt

On MacOS type:
pip3 install -r requirements.txt

This will install the packages from requirements.txt for this project.
'''

app = Flask(__name__)

##Connect to Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cafes.db'
db = SQLAlchemy()
db.init_app(app)

app.config['SECRET_KEY'] = 'TopSecretAPIKey'

##Cafe TABLE Configuration
class Cafe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), nullable=False)
    map_url = db.Column(db.String(5000), nullable=False)
    img_url = db.Column(db.String(5000), nullable=False)
    location = db.Column(db.String(250), nullable=False)
    seats = db.Column(db.Integer, nullable=False)
    has_toilet = db.Column(db.Boolean, nullable=False)
    has_wifi = db.Column(db.Boolean, nullable=False)
    has_sockets = db.Column(db.Boolean, nullable=False)
    can_take_calls = db.Column(db.Boolean, nullable=False)
    coffee_price = db.Column(db.String(20), nullable=False)  # Store as a string


class CafeForm(FlaskForm):
    name = StringField("Cafe Name", validators=[DataRequired()])
    map_url = StringField("Google Maps URL", validators=[DataRequired(), URL()])
    img_url = StringField("Image URL", validators=[DataRequired(), URL()])
    location = StringField("Location", validators=[DataRequired()])
    has_sockets = BooleanField("Has Sockets")
    has_toilet = BooleanField("Has Toilet")
    has_wifi = BooleanField("Has WiFi")
    can_take_calls = BooleanField("Can Take Calls")
    seats = IntegerField("Number of Seats", validators=[DataRequired(), NumberRange(min=1)])
    coffee_price = DecimalField("Coffee Price (£)", places=2, validators=[DataRequired()])
    submit = SubmitField("Add Cafe")

with app.app_context():
    db.create_all()


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/random", methods=["GET"])
def get_random_cafe():
    result = db.session.execute(db.select(Cafe))
    all_cafes = result.scalars().all()
    random_cafe = random.choice(all_cafes)
    return render_template("random_cafe.html", cafe=random_cafe)

@app.route("/all", methods=["GET"])
def get_all_cafes_page():
    result = db.session.execute(select(Cafe).order_by(Cafe.name))
    all_cafes = result.scalars().all()

    # Parse latitude and longitude
    cafes_with_coordinates = []
    for cafe in all_cafes:
        lat, lng = None, None
        try:
            # Extract latitude and longitude from map_url
            if "@" in cafe.map_url:
                coordinates = cafe.map_url.split('@')[1].split(',')[:2]
                lat, lng = float(coordinates[0]), float(coordinates[1])
        except (IndexError, ValueError):
            # Handle cases where map_url is malformed
            pass

        cafes_with_coordinates.append({
            "id": cafe.id,
            "name": cafe.name,
            "map_url": cafe.map_url,
            "img_url": cafe.img_url,
            "location": cafe.location,
            "seats": cafe.seats,
            "has_toilet": cafe.has_toilet,
            "has_wifi": cafe.has_wifi,
            "has_sockets": cafe.has_sockets,
            "can_take_calls": cafe.can_take_calls,
            "coffee_price": cafe.coffee_price,
            "latitude": lat,
            "longitude": lng
        })

    return render_template("all_cafes.html", cafes=cafes_with_coordinates)

## HTTP POST - Create Record
@app.route("/add", methods=["GET", "POST"])
def add_cafe():
    form = CafeForm()

    # When the form is submitted and validated
    if form.validate_on_submit():
        coffee_price_with_symbol = f"£{form.coffee_price.data}"
        existing_cafe = db.session.execute(
            db.select(Cafe).where(Cafe.name == form.name.data)
        ).scalar()

        if existing_cafe:
            flash("This cafe has already been added. Please try another place!", "error")
            return redirect(url_for('add_cafe'))

        new_cafe = Cafe(
            name=form.name.data,
            map_url=form.map_url.data,
            img_url=form.img_url.data,
            location=form.location.data,
            has_sockets=form.has_sockets.data,
            has_toilet=form.has_toilet.data,
            has_wifi=form.has_wifi.data,
            can_take_calls=form.can_take_calls.data,
            seats=form.seats.data,
            coffee_price=coffee_price_with_symbol
        )

        db.session.add(new_cafe)
        db.session.commit()
        flash("Cafe added successfully!", "success")
        return redirect(url_for("home"))

    return render_template("post_cafe.html", form=form)

@app.route("/modify", methods=["GET", "POST"])
def modify_cafe():
    if request.method == "POST":
        password = request.form.get("password")
        cafe_id = request.form.get("cafe_id")
        action = request.form.get("action")
        new_price = request.form.get("new_price")

        if new_price and not new_price.isnumeric():
            flash(message="Invalid Input: New price must be a numeric value.", category="error")
            return redirect(url_for('modify_cafe'))

        # Password check
        if password != "TopSecretPassword":
            flash(message="You entered wrong password.", category="error")
            return redirect(url_for('modify_cafe'))

        # Update price
        if action == "update_price":
            try:
                cafe = db.get_or_404(Cafe, cafe_id)
                cafe.coffee_price = "£" + new_price + ".00"
                db.session.commit()
                flash(message="Success: Successfully updated the price.", category="success")
                return redirect(url_for('modify_cafe'))
            except:
                print("No cafe found")
                flash(message="Cafe not found.", category="error")
                return redirect(url_for('modify_cafe'))

        # Delete cafe
        elif action == "delete_cafe":
            try:
                cafe = db.get_or_404(Cafe, cafe_id)
                db.session.delete(cafe)
                db.session.commit()
                flash(message="Success: Successfully deleted the cafe.", category="success")
                return redirect(url_for('modify_cafe'))
            except:
                print("No cafe found")
                flash(message="Cafe not found.", category="error")
                return redirect(url_for('modify_cafe'))

        flash(message="Bad Request", category="error")
        return redirect(url_for('modify_cafe'))

    return render_template("modify_cafe.html")

if __name__ == '__main__':
    app.run(debug=True)
