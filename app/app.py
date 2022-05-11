import time
from flask import Flask, render_template, flash, redirect, request, url_for
from sqlalchemy.sql import func
from flask_sqlalchemy import SQLAlchemy
from utils import *
import pandas as pd
from fitting import *

app = Flask(__name__, template_folder='template')

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://user:pass@postgres:5432/dwh'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = '12345'

db = SQLAlchemy(app)


class cars(db.Model):
    id = db.Column('cars_id', db.Integer, primary_key=True)
    year = db.Column(db.Integer)
    transmission = db.Column(db.String)
    mileage = db.Column(db.Integer)
    fuelType = db.Column(db.String)
    engineSize = db.Column(db.Integer)
    car = db.Column(db.String)
    price = db.Column(db.Integer)

    def __init__(self, year, transmission, mileage, fuelType, engineSize, car, price):
        self.year = year
        self.transmission = transmission
        self.mileage = mileage
        self.fuelType = fuelType
        self.engineSize = engineSize
        self.car = car
        self.price = price


class model_db(db.Model):
    id = db.Column('fit_id', db.Integer, primary_key=True)
    date = db.Column(db.DateTime(timezone=True), server_default=func.now())


@app.route('/')
def show_all():
   return "Hello world"


@app.route('/new', methods=['GET', 'POST'])
def add_data():
    if request.method == 'POST' and request.form['price']:

        if not request.form['year'] or not request.form['transmission'] or not request.form['mileage'] \
                or not request.form['fuelType'] or not request.form['engineSize'] or not request.form['car']:
            flash('Please enter all the fields', 'error')
        else:
            car = cars(
                request.form['year'],
                request.form['transmission'],
                request.form['mileage'],
                request.form['fuelType'],
                request.form['engineSize'],
                request.form['car'],
                request.form['price']
            )

            db.session.add(car)
            db.session.commit()

            flash('Record was successfully added')

            if request.form['fit'] == 'fit':

                data = get_data('cars', db)
                data = transform(data)
                model = fit(data)
                save_model(model, str(int(db.session.query(func.max(model_db.id)).scalar()) + 1))
                db.session.add(model_db())
                db.session.commit()

                flash('Model was fitted')

            return redirect('/new')

    elif request.method == 'POST' and not request.form['price']:

        if not request.form['year'] or not request.form['transmission'] or not request.form['mileage'] \
                or not request.form['fuelType'] or not request.form['engineSize'] or not request.form['car']:
            flash('Please enter all the fields', 'error')
        else:
            data = pd.DataFrame({
                'year': [int(request.form['year'])],
                'transmission': [request.form['transmission']],
                'mileage': [int(request.form['mileage']) / 323000],
                'fuelType': [request.form['fuelType']],
                'engineSize': [int(request.form['engineSize'])],
                'car': [request.form['car']]}
            )
            flash("Price " + str(int(predict(data, request.form['model'])[0])))
        return redirect('/new')

    return render_template('new.html', model_db = model_db.query.all())


if __name__ == '__main__':

    dbstatus = False
    while dbstatus == False:
        try:
            db.create_all()
        except:
            time.sleep(2)
        else:
            dbstatus = True
    load_first_dataset(table='cars', db_conn=db, file_path='./data/cars.csv')

    data = get_data('cars', db)
    data = transform(data)
    model = fit(data)
    save_model(model, '1')
    db.session.add(model_db())
    db.session.commit()

    app.run(debug=True, host='0.0.0.0')
