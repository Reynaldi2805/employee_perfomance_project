from airflow.models import DAG
from airflow.operators.python import PythonOperator
#from airflow.providers.postgres.operators.postgres import PostgresOperator
# from airflow.utils.task_group import TaskGroup
from datetime import datetime
from sqlalchemy import create_engine #koneksi ke postgres
import pandas as pd

from elasticsearch import Elasticsearch
from airflow.utils.task_group import TaskGroup
# from elasticsearch.helpers import bulk


def load_csv_to_postgres():

    """
    Loading raw CSV file to postgres
    
    """

    database = "milestone_3"
    username = "milestone_3"
    password = "milestone_3"
    host = "postgres"

    # Membuat URL koneksi PostgreSQL
    postgres_url = f"postgresql+psycopg2://{username}:{password}@{host}/{database}"

    # Gunakan URL ini saat membuat koneksi SQLAlchemy
    engine = create_engine(postgres_url)
    # engine= create_engine("postgresql+psycopg2://airflow:airflow@postgres/airflow")
    conn = engine.connect()

    df = pd.read_csv('/opt/airflow/dags/P2M3_reynaldi_evans_adam_data_raw.csv')
    #df.to_sql(nama_table_db, conn, index=False, if_exists='replace')
    df.to_sql('table_m3_new', conn, index=False, if_exists='replace')  
    

def fetch_data_from_postgres():
    """
    Loading table from postgres to pandas
    
    """

    # fetch data
    database = "milestone_3"
    username = "milestone_3"
    password = "milestone_3"
    host = "postgres"

    # Membuat URL koneksi PostgreSQL
    postgres_url = f"postgresql+psycopg2://{username}:{password}@{host}/{database}"

    # Gunakan URL ini saat membuat koneksi SQLAlchemy
    engine = create_engine(postgres_url)
    conn = engine.connect()

    df = pd.read_sql_query("select * from table_m3_new", conn) #nama table sesuaikan sama nama table di postgres
    df.to_csv('/opt/airflow/dags/P2M3_reynaldi_evans_adam_data_raw.csv', sep=',', index=False)
    


def data_preprocessing(): 
    ''' 
    Cleaning the dataset for analysis purposes
    '''
    # pembisihan data
    df = pd.read_csv("/opt/airflow/dags/P2M3_reynaldi_evans_adam_data_raw.csv")

    # Step 1: Data Cleaning

    #Changing Datetime Format
    df['DOB'] = pd.to_datetime(df['DOB'], format='%Y-%m-%d')
    df['StartDate'] = pd.to_datetime(df['StartDate'], format='%Y-%m-%d')

    #Dropping index
    df.drop(columns=['Unnamed: 0'], inplace=True)

    # Remove duplicate rows
    df.drop_duplicates(inplace=True)

    # Normalize column names
    df.columns = df.columns.str.lower() # Convert column names to lowercase
    df.columns = df.columns.str.strip() # Remove leading/trailing whitespaces
    df.columns = df.columns.str.replace(' ', '_') # Replace spaces with underscores

    # Handling Missing Values
    # Drop rows with missing values (you can use other methods as well depending on your data)
    df.dropna(inplace=True)

    # Save cleaned data to a CSV file
    df.to_csv('/opt/airflow/dags/P2M3_reynaldi_evans_adam_data_cleaned.csv', sep=',', index=False)
    
def upload_to_elasticsearch():

    """
    Uploading the cleaned dataset into elasticsearch
    """

    es = Elasticsearch("http://elasticsearch:9200")
    df = pd.read_csv('/opt/airflow/dags/P2M3_reynaldi_evans_adam_data_cleaned.csv')
    
    for i, r in df.iterrows():
        doc = r.to_dict()  # Convert the row to a dictionary
        res = es.index(index="table_m3_new", id=i+1, body=doc)
        print(f"Response from Elasticsearch: {res}")
        
        
# Define default configuration settings for a task or workflow in Apache Airflow
default_args = {
    'owner': 'aldi',
    'start_date': datetime(2020, 12 , 25, 12, 00) # Set start date behind project due date to:
    # 1. Avoid accidental execution before due date
    # 2. Allow time for testing before the actual deadline
    # 3. Ensure consistency in workflow scheduling
    # 4. Facilitate backfilling of historical data without triggering premature executions
}
with DAG(
    "P2M3_Reynaldi_Evans_Adam_DAG_hck", # Adjust according to your project name
    description='Milestone_3',
    schedule_interval='30 6 * * *', # Set the schedule interval for executing the Airflow DAG
    default_args=default_args, # Set the default arguments for the DAG
    catchup=False # Disable catch-up scheduling to prevent backfilling for past intervals
) as dag:
        
    load_csv_task = PythonOperator(
        task_id='load_csv_to_postgres',
        python_callable=load_csv_to_postgres)
    
    data_fetch = PythonOperator(
        task_id='fetch_data_from_postgres',
        python_callable=fetch_data_from_postgres)
    
    data_processing = PythonOperator(
        task_id='data_manipulation',
        python_callable=data_preprocessing)

    upload_data = PythonOperator(
        task_id='upload_data_elastic',
        python_callable=upload_to_elasticsearch)

    load_csv_task >> data_fetch >> data_processing >> upload_data
    
"""
In Cron notation (which Apache Airflow uses for scheduling), the format is as follows: minute, hour, day_of_month, month, day_of_week.

So, if you change schedule_interval='10 5 * * *', it means:

10: Execute at the 10th minute of the hour.
5: Execute at 5 AM.
*: Execute every day of the month.
*: Execute every month.
*: Execute every day of the week.
"""



