from sshtunnel import SSHTunnelForwarder
import pymysql

class DataHandler :
    def __init__(self) :
        self.tunnel = SSHTunnelForwarder(('210.94.185.39', 10025),
                                    ssh_username='woongsup',
                                    ssh_password='1111',
                                    remote_bind_address=('127.0.0.1', 3306),
                                    local_bind_address=('0.0.0.0', 3305))

        self.tunnel.start()
        self.conn = pymysql.connect(host=self.tunnel.local_bind_host,
                               port=self.tunnel.local_bind_port,
                               user='root',
                               passwd='1111',
                               db='healthcare')
        self.cur = self.conn.cursor()

    def execute(self, query, args = {}) :
        print("*")
        self.cur.execute(query,args)
        rows = self.cur.fetchall()

        #Initializing Data
        self.time_50 = rows[len(rows)-6][1]
        self.temperature_50 = rows[len(rows)-6][3]
        self.humidity_50 = rows[len(rows)-6][4]
        self.heart_50 = rows[len(rows)-6][5]

        self.time_40 = rows[len(rows)-5][1]
        self.temperature_40 = rows[len(rows)-5][3]
        self.humidity_40 = rows[len(rows)-5][4]
        self.heart_40 = rows[len(rows)-5][5]

        self.time_30 = rows[len(rows)-4][1]
        self.temperature_30 = rows[len(rows)-4][3]
        self.humidity_30 = rows[len(rows)-4][4]
        self.heart_30 = rows[len(rows)-4][5]

        self.time_20 = rows[len(rows)-3][1]
        self.temperature_20 = rows[len(rows)-3][3]
        self.humidity_20 = rows[len(rows)-3][4]
        self.heart_20 = rows[len(rows)-3][5]

        self.time_10 = rows[len(rows)-2][1]
        self.temperature_10 = rows[len(rows)-2][3]
        self.humidity_10 = rows[len(rows)-2][4]
        self.heart_10 = rows[len(rows)-2][5]

        self.time_0 = rows[len(rows)-1][1]
        self.temperature_0 = rows[len(rows)-1][3]
        self.humidity_0 = rows[len(rows)-1][4]
        self.heart_0 = rows[len(rows)-1][5]

    # close connection
    def close(self) :
        self.cur.close()
        self.conn.close()
        self.tunnel.close()



# Average of Heart_Rate
#cur.execute('select avg(Heart_Rate) from Sensor_Data')
#rows = cur.fetchall()
#print("Heart_Rate_AVG : ",rows[len(rows)-1][0])
#heart = rows[len(rows)-1][0]
"""
if __name__ == "__main__" :
    # SSH address mapping setup (not actually connects)

    data = DataHandler()
    data.execute("select * from Sensor_Data")
    print("Time : " ,data.time)
    print("temperature : " ,data.temperature)
    print("Humidity : " ,data.hum)
    print("Heart Rate : " ,data.heart)
    data.close()
"""
