import pyodbc
import datetime

conn_str = "Driver={ODBC Driver 18 for SQL Server};Server=tcp:albert-lea.database.windows.net,1433;Database=free-sql-db-2989184;Persist Security Info=False;UID=CloudSA96776960;PWD=window-sailing-83;Encrypt=yes;TrustServerCertificate=no;"
conn = pyodbc.connect(conn_str, autocommit=True)
cursor = conn.cursor()

appt_type = "IB"
appt_date = datetime.date.today().isoformat()
appt_time = "10:00"
scheduled_datetime = f"{appt_date} {appt_time}:00"
bol_shipment_no = "TEST-1234"
delivery_no = ""
notes = "Test appointment"
created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
updated_at = created_at
carrier_id = "1"
customer_id = "1"
product_type_id = "1"

try:
    cursor.execute(
        '''INSERT INTO dbo.core_appointment 
           (appt_type, appt_date, appt_time, scheduled_datetime, bol_shipment_no, delivery_no, status, notes, created_at, updated_at, carrier_id, customer_id, product_type_id, created_by, cancelled_reason)
           VALUES (?, ?, ?, ?, ?, ?, 'Scheduled', ?, ?, ?, ?, ?, ?, '', '')''',
        (appt_type, appt_date, appt_time, scheduled_datetime, bol_shipment_no, delivery_no, notes, created_at, updated_at, carrier_id, customer_id, product_type_id)
    )
    cursor.execute("SELECT @@IDENTITY")
    new_id = cursor.fetchone()[0]
    print("SUCCESS", new_id)
except Exception as e:
    print("ERROR", str(e))
