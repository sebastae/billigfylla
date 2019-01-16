import csv
import sqlite3
from sqlite3 import Cursor
import sys
from time import time


def timed(method):
    def measure(*args, **kwargs):
        ts = time()
        result = method(*args, **kwargs)
        te = time()

        print("Finished in %2.2f ms" % ((te - ts)*1000))
        return result
    return measure

class Inserter:

    def __init__(self, cursor: Cursor):
        cursor.execute("SELECT Id FROM Products ORDER BY Id DESC LIMIT 1")
        id = cursor.fetchone()
        if id is not None:
            self.next_id = id[0] + 1
        else:
            self.next_id = 1
        self.inserted = 0
        self.cursor = cursor

    def insert(self, values):
        values = list(values)
        values.insert(0, self.next_id)
        self.cursor.execute("INSERT INTO Products VALUES(?,?,?,?,?,?,?,?,?,?,?)", tuple(values))
        self.next_id += 1
        self.inserted += 1
        # print(f"INSERT {values[0]}")

    def stats(self):
        print(f"Inserted {self.inserted} elements")


class Updater:

    def __init__(self, cursor: Cursor):
        self.cursor = cursor
        self.updated = 0

    def update(self, data: tuple, values: tuple, columns: dict):
        data = data[1:]
        for i in range(len(data)):
            if data[i] != values[i]:
                key = str(list(columns.keys())[i])
                query = f"UPDATE Products SET {key}=?"
                self.cursor.execute(query, (key,))
        # print(f"UPDATE {values[0]}")

    def stats(self):
        print(f"Updated {self.updated} elements")


def calculate_ranking(data: str, columns: tuple):
    volume_col, price_col, alcohol_col = columns
    volume = float(data[volume_col].replace(",", "."))
    price = float(data[price_col].replace(",", "."))
    alcohol = float(data[alcohol_col].replace(",", "."))

    return 100 * (volume * alcohol) / price


def cast(values, datatypes: dict):
    for i in range(len(values)):
        values[i] = list(datatypes.values())[i](values[i])
    return values


def extract_data(data: list, columns: dict):
    extracted = []
    for k, v in columns.items():
        if isinstance(v, tuple):
            func, args = v
            d = func(data, args)
        else:
            d = data[v].replace(",", ".")
        extracted.append(d)
    return extracted


@timed
def update(filename: str, dbname: str):
    f = open(filename, "r", encoding="iso-8859-1")
    reader = csv.reader(f, delimiter=";")
    db = sqlite3.connect(dbname)
    cursor = db.cursor()

    columns = {
        'Name': 2,
        'ProductNumber': 1,
        'ProductType': 6,
        'Volume': 3,
        'Price': 4,
        'VolumePrice': 5,
        'Alcohol': 26,
        'OrderOnly': (lambda d, c: int(d[c] == "Bestillingsutvalget"), 7),
        'URL': 35,
        'Ranking': (calculate_ranking, (3, 4, 26)),
    }

    datatypes = {
        'Name': str,
        'ProductNumber': int,
        'ProductType': str,
        'Volume': float,
        'Price': float,
        'VolumePrice': float,
        'Alcohol': float,
        'OrderOnly': int,
        'URL': str,
        'Ranking': float,
    }

    inserter = Inserter(cursor)
    updater = Updater(cursor)

    cursor.execute("SELECT Type FROM ProductTypes")
    p_t = cursor.fetchall()

    p_types = []

    cursor.execute("SELECT Id FROM ProductTypes ORDER BY Id DESC LIMIT 1")
    p_types_next_id = cursor.fetchone()

    if p_types_next_id is None:
        p_types_next_id = 1
    else:
        p_types_next_id = p_types_next_id[0] + 1

    for t in p_t:
        p_types.append(t[0])


    next(reader, None)  # Skip header

    progress = 0
    for row in reader:

        row_data = extract_data(row, columns)
        row_data = cast(row_data, datatypes)

        # Product has volume, i.e is a drink
        if float(row[columns.get('Volume')].replace(",", ".")) > 0:

            # Insert into database if not already present
            prod_num = (row[columns.get('ProductNumber')],)
            cursor.execute('SELECT * FROM Products WHERE ProductNumber=?', prod_num)
            result = cursor.fetchone()

            if result is not None:
                # Product exists in database, update entry
                updater.update(result, row_data, columns)
            else:
                # Add product to database
                inserter.insert(row_data)

            # Update ProductTypes
            product_type = row[columns.get('ProductType')]
            if product_type not in p_types:
                cursor.execute("INSERT INTO ProductTypes VALUES (?,?)", (p_types_next_id, product_type))
                p_types_next_id += 1

        progress += 1
        if progress % 100 == 0:
            txt = f"Progress: {progress}"
            print(txt, end='\r')

    cursor.close()
    db.commit()
    inserter.stats()
    updater.stats()


@timed
def rebuild(fn, dbname):
    f = open(fn, "r", encoding="iso-8859-1")
    reader = csv.reader(f, delimiter=";")
    db = sqlite3.connect(dbname)
    cursor = db.cursor()

    columns = {
        'Name': 2,
        'ProductNumber': 1,
        'ProductType': 6,
        'Volume': 3,
        'Price': 4,
        'VolumePrice': 5,
        'Alcohol': 26,
        'OrderOnly': (lambda d, c: int(d[c] == "Bestillingsutvalget"), 7),
        'URL': 35,
        'Ranking': (calculate_ranking, (3, 4, 26)),
    }

    datatypes = {
        'Name': str,
        'ProductNumber': int,
        'ProductType': str,
        'Volume': float,
        'Price': float,
        'VolumePrice': float,
        'Alcohol': float,
        'OrderOnly': int,
        'URL': str,
        'Ranking': float,
    }

    inserter = Inserter(cursor)
    updater = Updater(cursor)

    types = []

    # Drop DB
    cursor.execute("DELETE FROM Products")
    cursor.execute("DELETE FROM ProductTypes")

    db.commit()
    progress = 0
    next(reader, None)
    for row in reader:
        data = extract_data(row, columns)
        data = cast(data, datatypes)

        if data[3] > 0:
            p_type = data[2]
            if p_type not in types:
                types.append(p_type)

            inserter.insert(data)
            progress += 1
            if progress % 100 == 0:
                txt = f"Progress: {progress}"
                print(txt, end='\r')

    for i in range(len(types)):
        cursor.execute("INSERT INTO ProductTypes VALUES(?,?)", (i, types[i]))
    cursor.close()

    db.commit()

    inserter.stats()


if __name__ == "__main__":
    if len(sys.argv) < 3:
        exit("Expected at least 2 arguments (path to csv, path to db)")

    data = sys.argv[1]
    db = sys.argv[2]

    if len(sys.argv) == 3:
        rebuild(data, db)
    else:
        if sys.argv[3] == 'r':
            print("Rebuilding Database")
            rebuild(data, db)
        elif sys.argv[3] == 'u':
            print("Updating Database")
            update(data, db)
        else:
            exit(f"Unknown argument '{sys.argv[3]}'")



    #update("./produkter.csv", "./produkter.db")
