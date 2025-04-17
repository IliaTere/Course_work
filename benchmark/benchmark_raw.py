#!/usr/bin/env python3
import time
import random
import psycopg2

# Параметры подключения к PostgreSQL
DB_USER = "benchmark"
DB_PASSWORD = "benchmark"
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "benchmark"

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
        
        print("Создаю 10000 пользователей...")
        
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
        
        print("База данных создана и заполнена.")
        print("\nНачинаю тесты производительности:")
        
        # Тест 1: Получение пользователя с ID 123
        single_user_time, _ = measure_time(
            lambda: cur.execute("SELECT * FROM users WHERE id = 123") or cur.fetchone()
        )
        print_result("Получение пользователя с ID 123", single_user_time)
        
        # Тест 2: Получение таблицы с 10 пользователями
        ten_users_time, _ = measure_time(
            lambda: cur.execute("SELECT * FROM users LIMIT 10") or cur.fetchall()
        )
        print_result("Получение таблицы с 10 пользователями", ten_users_time)
        
        # Тест 3: Получение таблицы с 10000 пользователями
        all_users_time, _ = measure_time(
            lambda: cur.execute("SELECT * FROM users") or cur.fetchall()
        )
        print_result("Получение таблицы с 10000 пользователями", all_users_time)
        
        # Закрываем соединение
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"Произошла ошибка: {e}")
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    run_benchmark() 