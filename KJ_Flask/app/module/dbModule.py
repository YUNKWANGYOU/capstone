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
        self.time = rows[len(rows)-1][1]
        self.temperature = rows[len(rows)-1][3]
        self.humidity = rows[len(rows)-1][4]
        self.heart = rows[len(rows)-1][5]

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
