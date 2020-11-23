from flask import Blueprint, request, render_template, flash, redirect, url_for
from flask import current_app as app
from app.module import dbModule

# 추가할 모듈이 있다면 추가

main = Blueprint('main', __name__, url_prefix='/')

@main.route('/main', methods=['GET'])
def index():
      data = dbModule.DataHandler()
      data.execute("select * from Sensor_Data")
      print("Time : " ,data.time)
      print("Temperature : " ,data.temperature)
      print("Humidity : " ,data.humidity)
      print("Heart Rate : " ,data.heart)
      data.close()
      testData = 'testData array'

      return render_template('/main/index.html',Time = data.time,
                                                Temperature = data.temperature,
                                                Humidity = data.humidity,
                                                Heart_Rate = data.heart)
