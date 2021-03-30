# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from flask import jsonify, render_template, redirect, request, url_for
from flask import current_app
from flask_login import (
    current_user,
    login_required,
    login_user,
    logout_user
)

from app import db, mysql, login_manager
from app.base import blueprint
from app.base.forms import LoginForm, CreateAccountForm
from app.base.models import PushSubscription, User

from app.base.util import verify_pass
from app.base.webpush_handler import trigger_push_notifications_for_subscriptions

from twilio.rest import Client
import requests
import json
from collections import OrderedDict

base_url = "http://127.0.0.1:10027"


@blueprint.route('/')
def route_default():
    return redirect(url_for('base_blueprint.login'))

# Login & Registration


@blueprint.route('/login', methods=['GET', 'POST'])
def login():
    login_form = LoginForm(request.form)
    if 'login' in request.form:

        # read form data
        username = request.form['username']
        password = request.form['password']

        # Locate user
        user = User.query.filter_by(username=username).first()

        # Check the password
        if user and verify_pass(password, user.password):

            login_user(user)
            return redirect(url_for('base_blueprint.route_default'))

        # Something (user or pass) is not ok
        return render_template('accounts/login.html', msg='Wrong user or password', form=login_form)

    if not current_user.is_authenticated:
        return render_template('accounts/login.html',
                               form=login_form)
    return redirect(url_for('home_blueprint.index'))


@blueprint.route('/register', methods=['GET', 'POST'])
def register():
    login_form = LoginForm(request.form)
    create_account_form = CreateAccountForm(request.form)
    if 'register' in request.form:

        username = request.form['username']
        email = request.form['email']

        # Check usename exists
        user = User.query.filter_by(username=username).first()
        if user:
            return render_template('accounts/register.html',
                                   msg='Username already registered',
                                   success=False,
                                   form=create_account_form)

        # Check email exists
        user = User.query.filter_by(email=email).first()
        if user:
            return render_template('accounts/register.html',
                                   msg='Email already registered',
                                   success=False,
                                   form=create_account_form)

        # else we can create the user
        user = User(**request.form)
        db.session.add(user)
        db.session.commit()

        return render_template('accounts/register.html',
                               msg='User created please <a href="/login">login</a>',
                               success=True,
                               form=create_account_form)

    else:
        return render_template('accounts/register.html', form=create_account_form)


@blueprint.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('base_blueprint.login'))


@blueprint.route('/shutdown')
def shutdown():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()
    return 'Server shutting down...'

# Errors


@login_manager.unauthorized_handler
def unauthorized_handler():
    return render_template('page-403.html'), 403


@blueprint.errorhandler(403)
def access_forbidden(error):
    return render_template('page-403.html'), 403


@blueprint.errorhandler(404)
def not_found_error(error):
    return render_template('page-404.html'), 404


@blueprint.errorhandler(500)
def internal_error(error):
    return render_template('page-500.html'), 500

# API


@blueprint.route('/admin-api/get-graph-data', methods=['GET'])
def get_graph_data():
    conn = mysql.connect()
    curs = conn.cursor()

    query = "SELECT Heart_Rate, Temperature, Humidity FROM Sensor_Data ORDER BY Sensor_Sequence ASC LIMIT 6"
    curs.execute(query)
    rows = curs.fetchall()
    rowarray_list = []
    for row in rows:
        t = (row[0], row[1], row[2])
        rowarray_list.append(t)
    objects_list = []
    for row in rows:
        d = OrderedDict()
        d["Heart_Rate"] = row[0]
        d["Temperature"] = row[1]
        d["Humidity"] = row[2]
        objects_list.append(d)
    conn.commit()
    conn.close()

    return jsonify(objects_list)

@blueprint.route('/admin-api/get-table-data', methods=['GET'])
def get_table_data():
    conn = mysql.connect()
    curs = conn.cursor()
    query = "SELECT User.Name,Emergency_Record.Time,Emergency_Record.Description FROM User,Emergency_Record WHERE User.MAC_Address = Emergency_Record.MAC_Address ORDER BY Emergency_Record.Emergency_ID DESC LIMIT 20;"
    curs.execute(query)
    rows = curs.fetchall()
    objects_list = []
    for row in rows:
        d = OrderedDict()
        d["Name"] = row[0]
        d["Time"] = row[1]
        d["Description"] = row[2]

        objects_list.append(d)


    conn.commit()
    conn.close()

    return jsonify(objects_list)

@blueprint.route('/admin-api/table-data', methods=['GET'])
def table_data():
    conn = mysql.connect()
    curs = conn.cursor()
    query = "SELECT User.Name,User.User_ID,Sensor_Data.Heart_Rate,Sensor_Data.Temperature,Sensor_Data.Humidity FROM User,Sensor_Data WHERE User.MAC_Address = Sensor_Data.MAC_Address ORDER BY User.User_ID;"
    curs.execute(query)
    rows = curs.fetchall()
    objects_list2 = []
    for row in rows:
        d = OrderedDict()
        d["Name"] = row[0]
        d["User_ID"] = row[1]
        d["Heart_Rate"] = row[2]
        d["Temperature"] = row[3]
        d["Humidity"] = row[4]

        objects_list2.append(d)


    conn.commit()
    conn.close()

    return jsonify(objects_list2)


@blueprint.route('/admin-api/push-subscriptions', methods=['POST'])
def create_push_subscription():
    json_data = request.get_json()
    subscription = PushSubscription.query.filter_by(
        subscription_json=json_data['subscription_json']
    ).first()
    if subscription is None:
        subscription = PushSubscription(
            subscription_json=json_data['subscription_json']
        )
        db.session.add(subscription)
        db.session.commit()

    return jsonify({
        "status": "success",
        "result": {
            "id": subscription.id,
            "subscription_json": subscription.subscription_json
        }
    })


@blueprint.route('/admin-api/trigger-push-notifications', methods=['POST'])
def trigger_push_notifications():
    json_data = request.get_json(force=True)
    subscriptions = PushSubscription.query.all()
    results = trigger_push_notifications_for_subscriptions(
        subscriptions,
        json_data.get('title'),
        json_data.get('body')
    )

    return jsonify({
        "status": "success",
        "result": results
    })


@blueprint.route('/admin-api/send-messages', methods=['POST'])
def send_messages():
    account_sid = current_app.config["TWILIO_ACCOUNT_SID"]
    auth_token = current_app.config["TWILIO_AUTH_TOKEN"]
    client = Client(account_sid, auth_token)

    from_ = current_app.config["TWILIO_FROM"]
    to = current_app.config["TWILIO_TO"]

    json_data = request.get_json(force=True)
    description = json_data.get('title') + '\n' + json_data.get('body')
    message = client.messages.create(
        body=description,
        from_=from_,
        to=to
    )

    return jsonify({
        "status": "success"
    })


@blueprint.route('/api/emergency/predict/android', methods=['POST'])
def predict_android():
    # get data
    json_data = request.get_json()
    _time = json_data.get('time')
    _mac = json_data.get('mac')
    result = json_data.get('result')

    # push notifications & send messages
    push_url = base_url + "/admin-api/trigger-push-notifications"
    requests.post(url=push_url, data=json.dumps(
        {"title": "응급상황이 발생했습니다.", "body": result}))
    # send_url = base_url + "/admin-api/send-messages"
    # requests.post(url=send_url, data=json.dumps(
    #     {"title": "응급상황이 발생했습니다.", "body": result}))

    # mysql insert emergency log
    conn = mysql.connect()
    curs = conn.cursor()
    curs.callproc('p_insert_emergency', (result, _time, _mac))
    conn.commit()
    conn.close()

    return jsonify({
        "status": "success"
    })


@blueprint.route('/api/emergency/predict/server', methods=['POST'])
def predict():
    # get data
    # _time = request.form['time']
    # _mac = request.form['mac']
    # _temp = request.form['temp']
    # _hum = request.form['hum']
    # _bio = request.form['bio']
    # _pir = request.form['pir']
    # _door = request.form['door']
    # _fire = request.form['fire']
    # _p_btn = request.form['p_btn']
    json_data = request.get_json()
    _time = json_data.get('time')
    _mac = json_data.get('mac')
    _temp = json_data.get('temp')
    _hum = json_data.get('hum')
    _bio = json_data.get('bio')
    _pir = json_data.get('pir')
    _door = json_data.get('door')
    _fire = json_data.get('fire')
    _p_btn = json_data.get('p_btn')

    # conn = mysql.connect()
    # curs = conn.cursor()

    emergency = True
    result = "Normal"
    # TODO: emergency predict algorithm

    # curs.execute(
    #     "SELECT User_ID FROM User WHERE MAC_Address = {}}".format(_mac))
    # row = curs.fetchone()
    user = "공예슬"
    body = "{}님의 집에 고양이가...".format(user)

    # push notifications & send messages
    if emergency:
        push_url = base_url + "/admin-api/trigger-push-notifications"
        requests.post(url=push_url, data=json.dumps(
            {"title": "응급상황이 발생했습니다.", "body": body}))
        # send_url = base_url + "/admin-api/send-messages"
        # requests.post(url=send_url, data=json.dumps(
        #     {"title": "응급상황이 발생했습니다.", "body": body}))
        # mysql insert emergency log
        # curs.callproc('p_insert_emergency', (body, _time, _mac))
        # conn.commit()

    # mysql insert data
    # curs.callproc('p_insert_data', (_time, _mac, _temp,
    #                                 _hum, _bio, _pir, _door, _fire, _p_btn))
    # conn.commit()
    # conn.close()

    return jsonify({
        "status": "success",
        "result": result
    })
