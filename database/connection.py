# database/connection.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pymysql

# Usamos la contraseña preconfigurada "demo" para tu servidor local de MySQL
DATABASE_URL = "mysql+pymysql://root:demo@127.0.0.1:3306/its_murialdo"

engine = create_engine(
    DATABASE_URL,
    pool_recycle=3600,
    pool_pre_ping=True,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_internal_connection():
    try:
        connection = pymysql.connect(
            host="127.0.0.1",
            user="root",
            password="demo",
            database="its_murialdo"
        )
        print("[✔] Conexión interna exitosa desde Python a 'its_murialdo'.")
        connection.close()
        return True
    except Exception as e:
        print(f"[-] Error de conexión interna: {str(e)}")
        return False

if __name__ == "__main__":
    test_internal_connection()