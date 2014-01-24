#!/usr/bin/env python
# -*- coding: utf-8 -*-
from sys import exit
from os import urandom
from functools import wraps
from datetime import datetime
from flask import Flask
from flask import flash
from flask import abort
from flask import request
from flask import session
from flask import url_for
from flask import redirect
from flask import render_template
from flask.ext.sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///./stufff.db'
app.config['PASSWORD'] = 'admin'
db = SQLAlchemy(app)


class Box(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True)

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return '<Box %s>' % self.name


class Thing(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text)
    done = db.Column(db.Boolean)
    added_date = db.Column(db.DateTime)
    box_id = db.Column(db.Integer, db.ForeignKey('box.id'))
    box = db.relationship('Box', backref=db.backref('things', lazy='dynamic'))

    def __init__(self, name, box, done=None, added_date=None):
        if done is None:
            done = False
        if added_date is None:
            added_date = datetime.utcnow()

        self.name = name
        self.box = box
        self.done = done
        self.added_date = added_date

    def __repr__(self):
        return '<Thing %s>' % self.name


def create_db():
    db.create_all()
    box = Box('Stufff')
    db.session.add(box)
    thing_01 = Thing('Doing stufff', box)
    thing_02 = Thing('Doing moar stufff', box)
    db.session.add(thing_01)
    db.session.add(thing_02)
    db.session.commit()


def login_required(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not session.get('logged_in'):
                return redirect(url_for('login_view', next=request.url))
            return f(*args, **kwargs)
        return decorated_function


@app.route("/login", methods=['GET', 'POST'])
def login_view():
    if request.method == 'GET':
        return render_template('login.html')
    else:
        password = request.form.get('password')
        if password == app.config.get('PASSWORD'):
            session['logged_in'] = True
        else:
            flash('Bad credentials')
            session['logged_in'] = False
    return redirect(url_for('home_view'))


@app.route("/logout")
def logout_view():
    session['logged_in'] = False
    return redirect(url_for('login_view'))


@app.route("/")
@login_required
def home_view():
    box = Box.query.first()
    return redirect(url_for('box_view', box_id=box.id))


@app.route("/thing/add", methods=['POST'])
@login_required
def add_thing():
    box_id = request.form.get('box_id')
    thing_name = request.form.get('thing_name')

    box = Box.query.filter_by(id=box_id).one()
    if not box:
        abort(404)

    thing = Thing(thing_name, box=box)
    db.session.add(thing)
    db.session.commit()
    return redirect(url_for('box_view', box_id=box.id))


@app.route("/thing/done/<thing_id>", methods=['GET'])
@login_required
def done_thing(thing_id):
    thing = Thing.query.filter_by(id=thing_id).one()
    if not thing:
        abort(404)

    thing.done = True
    db.session.commit()
    return redirect(url_for('box_view', box_id=thing.box.id))


@app.route("/thing/delete/<thing_id>", methods=['GET'])
@login_required
def delete_thing(thing_id):
    thing = Thing.query.filter_by(id=thing_id).one()
    if not thing:
        abort(404)

    box_id = thing.box.id
    db.session.delete(thing)
    db.session.commit()
    return redirect(url_for('box_view', box_id=box_id))


@app.route("/thing/undone/<thing_id>", methods=['GET'])
@login_required
def undone_thing(thing_id):
    thing = Thing.query.filter_by(id=thing_id).one()
    if not thing:
        abort(404)

    thing.done = False
    db.session.commit()
    return redirect(url_for('box_view', box_id=thing.box.id))


@app.route("/<int:box_id>")
@login_required
def box_view(box_id):
    box = Box.query.filter_by(id=box_id).one()
    if not box:
        abort(404)

    boxes = Box.query.all()
    count = box.things.filter_by(done=False).count()
    deletable = False
    if not count:
        deletable = True

    return render_template(
        'box.html', box=box, boxes=boxes, deletable=deletable)


@app.route("/", methods=['POST'])
@login_required
def go_box():
    box_id = request.form.get('box_id')

    if not box_id:
        abort(404)
    return redirect(url_for('box_view', box_id=box_id))


@app.route("/box/add", methods=['POST'])
@login_required
def add_box():
    box_name = request.form.get('box_name')

    box = Box(box_name)
    db.session.add(box)
    db.session.commit()

    return redirect(url_for('box_view', box_id=box.id))


@app.route("/box/delete/<box_id>", methods=['GET'])
@login_required
def delete_box(box_id):
    box = Box.query.filter_by(id=box_id).one()
    if not box:
        abort(404)

    if Box.query.count() == 1:
        flash('Impossible to delete latest box')
        return redirect(url_for('box_view', box_id=box_id))

    db.session.delete(box)
    db.session.commit()
    return redirect(url_for('home_view'))

if __name__ == "__main__":
    try:
        if Box.query.count() == 0:
            db.create_db()
    except Exception as err:
        print(
            'Error with your database. Maybe you need to create it like that:')
        print('>> from app import create_db')
        print('>> create_db()')
        print(err)
        exit(1)

    app.run(debug=True)
