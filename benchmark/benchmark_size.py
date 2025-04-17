#!/usr/bin/env python3
import time
import random
import psycopg2
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base

# Параметры подключения к PostgreSQL
DB_USER = "benchmark"
DB_PASSWORD = "benchmark"
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "benchmark"
DB_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# ID пользователя для поиска в обоих тестах
TARGET_ID = 123

# Функция для форматирования результата
def print_result(operation, time_ms):
    print(f"{operation}: {time_ms:.2f} ms")

# Функция для замера времени выполнения
def measure_time(func):
    times = []
    # Проводим 10 запросов и берем среднее время для более точных результатов
    for _ in range(10):
        start_time = time.time()
        result = func()
        end_time = time.time()
        times.append((end_time - start_time) * 1000)  # Время в миллисекундах
    
    # Возвращаем среднее время
    return sum(times) / len(times)

def run_orm_benchmark():
    """Бенчмарк с использованием ORM"""
    print("\n=== Бенчмарк с SQLAlchemy ORM ===")
    
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
    
    try:
        # Удаляем таблицу users, если она существует
        Base.metadata.drop_all(engine)
        
        # Создаем таблицу users
        Base.metadata.create_all(engine)
        
        # Создаем сессию
        session = Session()
        
        # === Тест с 10 строками ===
        print(f"\nСоздаю таблицу с 10 пользователями (включая ID {TARGET_ID})...")
        
        # Создаем 10 пользователей
        users = []
        # Создаем пользователей с ID от 120 до 129, чтобы включить ID 123
        for i in range(120, 130):
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
        session.add_all(users)
        session.commit()
        
        # Тест: Получение пользователя с ID TARGET_ID из таблицы в 10 строк
        small_table_time = measure_time(
            lambda: session.query(User).filter(User.id == TARGET_ID).first()
        )
        print_result(f"Получение пользователя с ID {TARGET_ID} из таблицы с 10 строками (ORM)", small_table_time)
        
        # Очищаем таблицу
        session.query(User).delete()
        session.commit()
        
        # === Тест с 10000 строками ===
        print(f"\nСоздаю таблицу с 10000 пользователями (включая ID {TARGET_ID})...")
        
        # Создаем 10000 пользователей
        users = []
        for i in range(1, 10001):
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
        
        # Тест: Получение пользователя с ID TARGET_ID из таблицы в 10000 строк
        large_table_time = measure_time(
            lambda: session.query(User).filter(User.id == TARGET_ID).first()
        )
        print_result(f"Получение пользователя с ID {TARGET_ID} из таблицы с 10000 строками (ORM)", large_table_time)
        
        # Сравнение
        ratio = large_table_time / small_table_time
        print(f"Запрос в большой таблице {'медленнее' if ratio > 1 else 'быстрее'} в {abs(ratio):.2f}x раз")
        
        # Закрываем сессию
        session.close()
        
    except Exception as e:
        print(f"Произошла ошибка: {e}")
        if 'session' in locals():
            session.close()

def run_sql_benchmark():
    """Бенчмарк с использованием чистого SQL"""
    print("\n=== Бенчмарк с чистым SQL через psycopg2 ===")
    
    try:
        # Устанавливаем соединение с базой данных
        conn = psycopg2.connect(
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME
        )
        
        # Создаем курсор для выполнения запросов
        cur = conn.cursor()
        
        # Удаляем таблицу users, если она существует
        cur.execute("DROP TABLE IF EXISTS users")
        conn.commit()
        
        # Создаем таблицу users
        cur.execute("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                name VARCHAR(255),
                email VARCHAR(255),
                phone VARCHAR(255),
                address VARCHAR(255),
                city VARCHAR(255),
                country VARCHAR(255),
                zipcode VARCHAR(255)
            )
        """)
        conn.commit()
        
        # === Тест с 10 строками ===
        print(f"\nСоздаю таблицу с 10 пользователями (включая ID {TARGET_ID})...")
        
        # Создаем 10 пользователей и вставляем их в базу данных
        values = []
        # Создаем пользователей с ID от 120 до 129, чтобы включить ID 123
        for i in range(120, 130):
            values.append((
                i,
                f"User {i}",
                f"user{i}@example.com",
                f"+7{random.randint(9000000000, 9999999999)}",
                f"Street {i}",
                f"City {i % 100}",
                f"Country {i % 10}",
                f"{10000 + i}"
            ))
        
        args_str = ','.join(cur.mogrify("(%s,%s,%s,%s,%s,%s,%s,%s)", v).decode('utf-8') for v in values)
        cur.execute(f"INSERT INTO users (id, name, email, phone, address, city, country, zipcode) VALUES {args_str}")
        conn.commit()
        
        # Тест: Получение пользователя с ID TARGET_ID из таблицы в 10 строк
        small_table_time = measure_time(
            lambda: cur.execute(f"SELECT * FROM users WHERE id = {TARGET_ID}") or cur.fetchone()
        )
        print_result(f"Получение пользователя с ID {TARGET_ID} из таблицы с 10 строками (SQL)", small_table_time)
        
        # Очищаем таблицу
        cur.execute("DELETE FROM users")
        conn.commit()
        
        # === Тест с 10000 строками ===
        print(f"\nСоздаю таблицу с 10000 пользователями (включая ID {TARGET_ID})...")
        
        # Создаем 10000 пользователей и вставляем их в базу данных
        batch_size = 1000
        for batch_start in range(1, 10001, batch_size):
            batch_end = min(batch_start + batch_size - 1, 10000)
            values = []
            
            for i in range(batch_start, batch_end + 1):
                values.append((
                    i,
                    f"User {i}",
                    f"user{i}@example.com",
                    f"+7{random.randint(9000000000, 9999999999)}",
                    f"Street {i}",
                    f"City {i % 100}",
                    f"Country {i % 10}",
                    f"{10000 + i}"
                ))
            
            args_str = ','.join(cur.mogrify("(%s,%s,%s,%s,%s,%s,%s,%s)", v).decode('utf-8') for v in values)
            cur.execute(f"INSERT INTO users (id, name, email, phone, address, city, country, zipcode) VALUES {args_str}")
            conn.commit()
        
        # Тест: Получение пользователя с ID TARGET_ID из таблицы в 10000 строк
        large_table_time = measure_time(
            lambda: cur.execute(f"SELECT * FROM users WHERE id = {TARGET_ID}") or cur.fetchone()
        )
        print_result(f"Получение пользователя с ID {TARGET_ID} из таблицы с 10000 строками (SQL)", large_table_time)
        
        # Сравнение
        ratio = large_table_time / small_table_time
        print(f"Запрос в большой таблице {'медленнее' if ratio > 1 else 'быстрее'} в {abs(ratio):.2f}x раз")
        
        # Закрываем соединение
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"Произошла ошибка: {e}")
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print(f"Бенчмарк для получения пользователя с ID {TARGET_ID} из таблиц разного размера")
    run_orm_benchmark()
    run_sql_benchmark() 