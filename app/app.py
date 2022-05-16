import time
from flask import Flask, render_template, flash, redirect, request, url_for
from sqlalchemy.sql import func
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import SubmitField, IntegerField, SelectField, RadioField
from wtforms.validators import NumberRange

from mapping import transmission_dict, fuelType_dict, car_dict
from utils import load_first_dataset
from fitting import save_model, fit, predict_p, get_data, transform, pd, scale_data

from dotenv import load_dotenv
from os import getenv


load_dotenv()
app = Flask(__name__, template_folder='template')


# Config
app.config['SQLALCHEMY_DATABASE_URI'] = getenv('SQLALCHEMY_DATABASE_URI', None)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = getenv('SECRET_KEY', None)

# DataBases
db = SQLAlchemy(app)


class Cars(db.Model):
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


class ModelDB(db.Model):
    id = db.Column('fit_id', db.Integer, primary_key=True)
    date = db.Column(db.DateTime(timezone=True), server_default=func.now())
    name = db.Column(db.String, default='')
    mae = db.Column(db.String, default='')


# Forms
class FormForPredict(FlaskForm):
    year = IntegerField('year', validators=[NumberRange(min=1970, max=2022)])
    transmission = SelectField('transmission', choices=[('Manual', 'Manual'), ('Automatic', 'Automatic')])
    mileage = IntegerField('mileage', validators=[NumberRange(min=1, max=100000000)])
    fuelType = SelectField('fuelType', choices=[('Petrol', 'Petrol'), ('Diesel', 'Diesel')])
    engineSize = IntegerField('engineSize', validators=[NumberRange(min=0, max=7)])
    car = SelectField('car', choices=[
        ('audi', 'audi'),
        ('bmw', 'bmw'),
        ('cclass', 'cclass'),
        ('focus', 'focus'),
        ('ford', 'ford'),
        ('hyundi', 'hyundi'),
        ('merc', 'merc'),
        ('skoda', 'skoda'),
        ('toyota', 'toyota'),
        ('unclean_cclass', 'unclean_cclass'),
        ('vauxhall', 'vauxhall'),
        ('vw', 'vw')
    ])
    price = IntegerField('price', validators=[NumberRange(min=10, max=100000000)])

    fit = RadioField('fit', choices=[('fit', 'fit'), ('no_fit', 'no_fit')])

    submit = SubmitField("Add/Fit")


# Actions
def add_order(form, db):
    car = Cars(*[col.data for col in form if col.name not in ['fit', 'submit', 'Add/Fit', 'csrf_token']])
    db.session.add(car)
    db.session.commit()


def fit_func(db):
    data = get_data('cars', db)
    data = transform(data)
    model = fit(scale_data(data[0]), data[1])
    save_model(model[0], str(int(db.session.query(func.max(ModelDB.id)).scalar()) + 1))
    db.session.add(ModelDB(name=str(model[0]), mae=model[1]))
    db.session.commit()


def predict_func(form):

    data = pd.DataFrame({
        'year': [int(form.year.data)],
        'transmission': [transmission_dict[form.transmission.data]],
        'mileage': [int(form.mileage.data)],
        'fuelType': [fuelType_dict[form.fuelType.data]],
        'engineSize': [int(form.engineSize.data)],
        'car': [car_dict[form.car.data]]}
    )
    return str(int(predict_p(scale_data(data), request.form['model'])[0]))


def initial_db(db):
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
    model = fit(scale_data(data[0]), data[1])
    save_model(model[0], '1')
    db.session.add(ModelDB(name=str(model[0]), mae=model[1]))
    db.session.commit()


@app.route('/')
def show_all():
   return "Hello world"


@app.route('/submit', methods=['GET', 'POST'])
def submit():
    form = FormForPredict()

    if request.method == 'POST' and form.price.data:
        if any([not col.data for col in form if col.name not in ['fit', 'submit', 'Add/Fit', 'csrf_token']]):
            flash('Please enter all the fields', 'error')
        else:
            flash('Record is adding...')
            add_order(form, db)
            flash('Record was successfully added')

            if form.fit.data == 'fit':
                fit_func(db)
                flash('Model was fitted')

            return redirect('/submit')

    elif request.method == 'POST' and not form.price.data:
        if any([not col.data for col in form if col.name not in ['fit', 'submit', 'Add/Fit', 'csrf_token', 'price']]):
            flash('Please enter all the fields', 'error')
        else:
            flash("Price " + predict_func(form))
        return redirect('/submit')

    if form.validate_on_submit():
        return redirect('/submit')

    return render_template('submit.html', form=form, model_db = ModelDB.query.all())


if __name__ == '__main__':
    initial_db(db)
    app.run(debug=True, host='0.0.0.0')
