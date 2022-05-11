import pandas as pd


def load_first_dataset(table, db_conn, file_path):
    data = pd.read_csv(file_path)
    data.to_sql(name=table, con=db_conn.engine, index=False, if_exists='append')