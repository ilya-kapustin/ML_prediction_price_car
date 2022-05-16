import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import MinMaxScaler
from sklearn.linear_model import Ridge
from sklearn.svm import SVR
from joblib import dump, load
import operator
from mapping import transmission_dict, fuelType_dict, car_dict

def get_data(table, db):
    return pd.read_sql(f'SELECT * FROM {table}', con=db.engine)


def transform(data):
    data['transmission'] = data['transmission'].replace(transmission_dict)
    data['fuelType'] = data['fuelType'].replace(fuelType_dict)
    data['car'] = data['car'].replace(car_dict)

    X = data[['year', 'transmission', 'mileage', 'fuelType', 'engineSize', 'car']]
    Y = data['price']

    return (X, Y)


def scale_data(data):
    scaler = MinMaxScaler(feature_range=(0, 1))
    return scaler.fit_transform(data)


def fit(X, Y):

    x_train, x_test, y_train, y_test = train_test_split(X, Y, test_size=0.25)

    models = {
        LinearRegression(): [],
        Ridge(alpha=1.0): [],
    }

    for ml in models.keys():
        ml.fit(x_train, y_train)
        models[ml].append(np.mean(abs(ml.predict(x_test) - y_test)))

    argmin_model = min(models.items(), key=operator.itemgetter(1))[0]
    return (
        argmin_model,
        models[argmin_model]
    )


def save_model(model, path):
    dump(model, f'./models/{path}.joblib')


def predict_p(data, path):
    model = load(f'./models/{path}.joblib')
    return model.predict(data)