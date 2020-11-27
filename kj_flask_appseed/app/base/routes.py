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
from app.base.models import User, PushSubscription

from app.base.util import verify_pass
from app.base.webpush_handler import trigger_push_notifications_for_subscriptions

from twilio.rest import Client
import requests
import json

base_url = "http://127.0.0.1:10027"


@blueprint.route('/')
def route_default():
    return redirect(url_for('base_blueprint.login'))

## Login & Registration


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


@blueprint.route('/api/emergency/predict/server', methods=['POST'])
def predict_server():
    # get data
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
    result = "Normal"
    emergency = True

    # TODO: emergency predict algorithm

    # curs.execute(
    #     "SELECT User_ID FROM User WHERE MAC_Address = {}}".format(_mac))
    # row = curs.fetchone()
    # user = row[0]
    user = "공예슬"
    body = "{}님의 집에 고양이가...".format(user)
    # push notifications & send messages
    if emergency:
        result = "Emergency"
        push_url = base_url + "/admin-api/trigger-push-notifications"
        requests.post(url=push_url, data=json.dumps(
            {"title": "경고: 응급상황이 발생했습니다.", "body": body}))
        # send_url = base_url + "/admin-api/send-messages"
        # requests.post(url=send_url, data=json.dumps(
        #     {"title": "경고: 응급상황이 발생했습니다.", "body": body}))

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
        {"title": "경고: 응급상황이 발생했습니다.", "body": result}))
    # send_url = base_url + "/admin-api/send-messages"
    # requests.post(url=send_url, data=json.dumps(
    #     {"title": "경고: 응급상황이 발생했습니다.", "body": result}))

    # mysql insert emergency log
    conn = mysql.connect()
    curs = conn.cursor()
    curs.callproc('p_insert_emergency', (result, _time, _mac))
    conn.commit()
    conn.close()

    return jsonify({
        "status": "success"
    })


@blueprint.route('/api/emergency/decision', methods=['POST'])
def emergency_decision():
    # get data
    json_data = request.get_json()
    _time = json_data.get('time')
    _mac = json_data.get('mac')
    result = json_data.get('result')

    if result == "Confirm":
        # 119 부르기
        # push notifications & send messages
        push_url = base_url + "/admin-api/trigger-push-notifications"
        requests.post(url=push_url, data=json.dumps(
            {"title": "비상: 응급상황이 발생했습니다.", "body": result}))
        send_url = base_url + "/admin-api/send-messages"
        requests.post(url=send_url, data=json.dumps(
            {"title": "비상: 응급상황이 발생했습니다.", "body": result}))

        # mysql insert emergency log
        conn = mysql.connect()
        curs = conn.cursor()
        curs.callproc('p_insert_emergency', (result, _time, _mac))
        conn.commit()
        conn.close()

    return jsonify({
        "status": "success"
    })
