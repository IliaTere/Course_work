#!/usr/bin/env python3
import time
import random
from sqlalchemy import create_engine, Column, Integer, String, MetaData, Table
from sqlalchemy.orm import sessionmaker, declarative_base

# Параметры подключения к PostgreSQL
DB_USER = "benchmark"
DB_PASSWORD = "benchmark"
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "benchmark"
DB_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Инициализация SQLAlchemy
engine = create_engine(DB_URL)
Base = declarative_base()
Session = sessionmaker(bind=engine)

# Определение модели User
class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    name = Column(String)
    email = Column(String)
    phone = Column(String)
    address = Column(String)
    city = Column(String)
    country = Column(String)
    zipcode = Column(String)
    
    def __repr__(self):
        return f"<User(id={self.id}, name='{self.name}')>"

# Функция для форматирования результата
def print_result(operation, time_ms):
    print(f"{operation}: {time_ms:.2f} ms")

# Функция для замера времени выполнения
def measure_time(func):
    start_time = time.time()
    result = func()
    end_time = time.time()
    return (end_time - start_time) * 1000, result  # Время в миллисекундах

def run_benchmark():
    try:
        # Удаляем таблицу users, если она существует
        Base.metadata.drop_all(engine)
        
        # Создаем таблицу users
        Base.metadata.create_all(engine)
        
        # Создаем сессию
        session = Session()
        
        print("Создаю 100000 пользователей...")
        
        # Создаем 10000 пользователей
        users = []
        for i in range(1, 100001):
            user = User(
                id=i,
                name=f"User {i}",
                email=f"user{i}@example.com",
                phone=f"+7{random.randint(9000000000, 9999999999)}",
                address=f"Street {i}",
                city=f"City {i % 100}",
                country=f"Country {i % 10}",
                zipcode=f"{10000 + i}"
            )
            users.append(user)
        
        # Вставляем данные пользователей
        batch_size = 1000
        for i in range(0, len(users), batch_size):
            batch = users[i:i + batch_size]
            session.add_all(batch)
            session.commit()
        
        print("База данных создана и заполнена.")
        print("\nНачинаю тесты производительности:")
        
        # Тест 1: Получение пользователя с ID 123
        single_user_time, single_user = measure_time(
            lambda: session.query(User).filter(User.id == 123).first()
        )
        print_result("Получение пользователя с ID 123", single_user_time)
        
        # Тест 2: Получение таблицы с 10 пользователями
        ten_users_time, ten_users = measure_time(
            lambda: session.query(User).limit(10).all()
        )
        print_result("Получение таблицы с 10 пользователями", ten_users_time)
        
        # Тест 3: Получение таблицы с 10000 пользователями
        all_users_time, all_users = measure_time(
            lambda: session.query(User).all()
        )
        print_result("Получение таблицы с 10000 пользователями", all_users_time)
        
        # Закрываем сессию
        session.close()
        
    except Exception as e:
        print(f"Произошла ошибка: {e}")
        if 'session' in locals():
            session.close()

if __name__ == "__main__":
    run_benchmark() 