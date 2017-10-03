#!/usr/bin/env python3.4

import logging
from flask import Flask, request, redirect, render_template
from werkzeug.serving import run_simple
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DATE
from sqlalchemy.orm import sessionmaker
from flask_socketio import SocketIO, emit
import datetime

HOST = "coding42.diphda.uberspace.de"
PORT = 62155

PROJECTNAME = "iBuy"
DBNAME = PROJECTNAME+".sqlite"

engine = create_engine("sqlite:///"+PROJECTNAME+".sqlite", echo=True)
Base = declarative_base()
Session = sessionmaker(bind=engine)
app = Flask(__name__)
app.config["SECRET_KEY"] = "BlaBlub42"
socketio = SocketIO(app)
app.config.update(PROPAGATE_EXCEPTIONS=True)

class Brand(Base):
    __tablename__ = "brands"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    def __repr__(self):
        return "<Marke(name='%s')>" % (self.name)#TODO
class Product(Base):
    __tablename__ = "product"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    brandID = Column(Integer)
    amount = Column(Integer)#volume, weight, ...
    unitID = Column(Integer)
    categoryID = Column(Integer)
    def __repr__(self):
        return "<Product(name='%s')>" % (self.name)#TODO
class Unit(Base):
    __tablename__ = "units"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    def __repr__(self):
        return "<Unit(name='%s')>" % (self.name)#TODO
class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    def __repr__(self):
        return "<Category(name='%s')>" % (self.name)#TODO
class Buy(Base):
    __tablename__ = "buys"
    id = Column(Integer, primary_key=True)
    productID = Column(Integer)
    n = Column(Integer)
    date = Column(DATE)
    price = Column(Integer)#price in cent per n
    def __repr__(self):
        return "<Buy(productID='%s')>" % (self.productID)#TODO

logger = logging.getLogger(PROJECTNAME)
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler(PROJECTNAME+".log")
fh.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
logger.addHandler(fh)
logger.addHandler(ch)

def initDB():
    """logger.info("init: "+"database")
    connection = sqlite3.connect(DBNAME, check_same_thread = False)
    cursor = connection.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS tags(id INTEGER, tagGroup TEXT, tag TEXT, PRIMARY KEY(id))")
    try:
        cursor.execute("INSERT INTO playlists (id, name) VALUES (1, 'erotic')")
        cursor.execute("INSERT INTO playlists (name) VALUES ('porn')")
    except sqlite3.IntegrityError:
        pass"""
    Base.metadata.create_all(engine)
    
@app.route("/", methods=["GET", "POST"])
def root():
    return redirect(request.url[0:request.url.rfind("/")+1]+"buy", code=302)
    
@app.route("/buy", methods=["GET", "POST"])
def buy():
    if request.method == "POST":
        i = 0
        session = Session()
        while ("product["+str(i)+"]") in request.form:
            brand = request.form["brand["+str(i)+"]"]
            product = request.form["product["+str(i)+"]"]
            category = request.form["category["+str(i)+"]"]
            n = request.form["n["+str(i)+"]"]
            price = request.form["price["+str(i)+"]"]
            amount = request.form["amount["+str(i)+"]"]
            unit = request.form["unit["+str(i)+"]"]
            date = request.form["date"]
            categoryID = -1
            if category != "":
                for instance in session.query(Category).filter_by(name=category):
                    categoryID = instance.id
                if categoryID == -1:
                    newCategory = Category(name=category)
                    session.add(newCategory)
                    categoryID = session.query(Category).filter_by(name=category).first().id
                logger.info(categoryID)
            #TODO error if categoryID==-1
            brandID = -1
            if brand != "":
                for instance in session.query(Brand).filter_by(name=brand):
                    brandID = instance.id
                if brandID == -1:
                    newBrand = Brand(name=brand)
                    session.add(newBrand)
                    brandID = session.query(Brand).filter_by(name=brand).first().id
                logger.info(brandID)
            unitID = -1
            if unit != "":
                for instance in session.query(Unit).filter_by(name=unit):
                    unitID = instance.id
                if unitID == -1:
                    newUnit = Unit(name=unit)
                    session.add(newUnit)
                    unitID = session.query(Unit).filter_by(name=unit).first().id
                logger.info(unitID)
            productID = -1
            if product != "":
                for instance in session.query(Product).filter_by(name=product, amount=amount, brandID=brandID, categoryID=categoryID, unitID=unitID):
                    productID = instance.id
                if productID == -1:
                    newUnit = Product(name=product, amount=amount, brandID=brandID, categoryID=categoryID, unitID=unitID)
                    session.add(newUnit)
                    productID = session.query(Product).filter_by(name=product).first().id
                logger.info(productID)
            date = date.split("-")
            date = datetime.datetime.strptime(date[0]+date[1]+date[2], "%Y%m%d").date()
            newBuy = Buy(n=n, date=date, price=price, productID=productID)
            session.add(newBuy)
            i += 1
        session.commit()
    return render_template("buy.html")
    
@app.route("/edit", methods=["GET", "POST"])
def edit():
    return render_template("edit.html")
    
@app.route("/overview", methods=["GET", "POST"])
def overview():
    return render_template("overview.html")
    
@app.route("/impressum", methods=["GET", "POST"])
def impressum():
    return render_template("impressum.html")

@socketio.on("requestBrands")
def requestBrands(json):
    logger.info("requestBrands")
    logger.info(json)
    letters = json["letters"]
    session = Session()
    brands = session.query(Brand.name).filter(Brand.name.like(letters+"%")).all()
    json["brands"] = brands
    logger.info(json)
    emit("respondBrands", json, room=None)

if __name__ == "__main__":
    initDB()
    socketio.run(app, host=HOST, port=PORT, debug=False)