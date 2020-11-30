from flask import Blueprint, request, render_template, flash, redirect, url_for
from flask import current_app as app
from app.module import dbModule
from flask_bootstrap import Bootstrap

# 추가할 모듈이 있다면 추가

main = Blueprint('main', __name__, url_prefix='/')

@main.route('/main', methods=['GET'])
def index():
      data = dbModule.DataHandler()
      data.execute("select * from Sensor_Data")
      print("Time : " ,data.time_0)
      print("Temperature : " ,data.temperature_0)
      print("Humidity : " ,data.humidity_0)
      print("Heart Rate : " ,data.heart_0)
      data.close()
      testData = 'testData array'

      return render_template('/main/index.html',Time_0 = data.time_0,
                                                Temperature_0 = data.temperature_0,
                                                Humidity_0 = data.humidity_0,
                                                Heart_Rate_0 = data.heart_0)
