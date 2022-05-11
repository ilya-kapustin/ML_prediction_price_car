import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from joblib import dump, load


def get_data(table, db):
    return pd.read_sql(f'SELECT * FROM {table}', con=db.engine)


def transform(data):
    data['transmission'] = data['transmission'].astype('category')
    data['fuelType'] = data['fuelType'].astype('category')
    data['car'] = data['car'].astype('category')
    data['year'] = data['year'].astype('category')

    data['transmission'] = data['transmission'].cat.codes
    data['fuelType'] = data['fuelType'].cat.codes
    data['car'] = data['car'].cat.codes
    data['year'] = data['year'].cat.codes

    data['mileage'] = data['mileage'] / np.max(data['mileage'])

    X = data[['year', 'transmission', 'mileage', 'fuelType', 'engineSize', 'car']]
    Y = data['price']

    return (X, Y)


def fit(data):
    x_train, x_test, y_train, y_test = train_test_split(data[0], data[1], test_size=0.25)

    model = LinearRegression()
    model.fit(x_train, y_train)

    return model

def save_model(model, path):
    dump(model, f'./models/{path}.joblib')


def predict(data, path):
    model = load(f'./models/{path}.joblib')
    return model.predict(data)