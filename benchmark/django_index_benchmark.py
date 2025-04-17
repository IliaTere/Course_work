#!/usr/bin/env python3
import time
import random
import statistics
import psycopg2

# Параметры подключения к PostgreSQL
DB_USER = "benchmark"
DB_PASSWORD = "benchmark"
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "benchmark"

# ID тестового пользователя для поиска
TEST_USER_ID = 42
# Строка для поиска по неиндексированному полю
TEST_NAME = "John Doe"

# Размеры баз данных для тестирования
DB_SIZES = [10, 100, 1000, 10000, 100000]

# Количество запусков для каждого теста
NUM_RUNS = 20

def measure_execution_time(func):
    """Замеряет время выполнения функции"""
    times = []
    for _ in range(NUM_RUNS):
        start_time = time.time()
        func()
        end_time = time.time()
        times.append((end_time - start_time) * 1000)  # Время в миллисекундах
    
    return {
        'mean': statistics.mean(times),
        'median': statistics.median(times),
        'stdev': statistics.stdev(times) if len(times) > 1 else 0,
        'min': min(times),
        'max': max(times)
    }

def setup_database(db_size, with_index=True):
    """
    Настраивает базу данных для тестирования
    
    Args:
        db_size: количество записей в таблице
        with_index: создавать ли индекс для поля name
    """
    print(f"\nНастройка базы данных с {db_size} записями (индекс по name: {with_index})...")
    
    try:
        # Соединение с базой данных
        conn = psycopg2.connect(
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME
        )
        
        cursor = conn.cursor()
        
        # Удаляем таблицу, если она существует
        cursor.execute("DROP TABLE IF EXISTS django_users")
        conn.commit()
        
        # Создаем новую таблицу
        cursor.execute("""
        CREATE TABLE django_users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(150) UNIQUE NOT NULL,
            name VARCHAR(150) NOT NULL,
            email VARCHAR(254) UNIQUE NOT NULL,
            is_active BOOLEAN NOT NULL DEFAULT TRUE
        )
        """)
        
        # Создаем индекс для поля name, если указано
        if with_index:
            cursor.execute("CREATE INDEX idx_users_name ON django_users (name)")
        
        conn.commit()
        
        # Вставляем тестового пользователя с заданным ID
        cursor.execute("""
        INSERT INTO django_users (id, username, name, email, is_active)
        VALUES (%s, %s, %s, %s, %s)
        """, (TEST_USER_ID, f"user{TEST_USER_ID}", TEST_NAME, f"user{TEST_USER_ID}@example.com", True))
        
        # Создаем остальных пользователей пакетными вставками
        batch_size = 1000
        for i in range(0, db_size - 1, batch_size):
            values = []
            for j in range(i, min(i + batch_size, db_size - 1)):
                # Пропускаем ID тестового пользователя
                user_id = j + 1
                if user_id >= TEST_USER_ID:
                    user_id += 1
                
                values.append((
                    user_id,
                    f"user{user_id}",
                    f"User Name {user_id}",
                    f"user{user_id}@example.com",
                    random.choice([True, True, True, False])  # 75% активных пользователей
                ))
            
            args_str = ','.join(cursor.mogrify("(%s,%s,%s,%s,%s)", v).decode('utf-8') for v in values)
            if args_str:  # Проверяем, что есть что вставлять
                cursor.execute(f"INSERT INTO django_users (id, username, name, email, is_active) VALUES {args_str}")
                conn.commit()
        
        # Анализируем таблицу для обновления статистики запросов
        cursor.execute("ANALYZE django_users")
        conn.commit()
        
        cursor.close()
        return conn
    
    except Exception as e:
        print(f"Произошла ошибка при настройке базы данных: {e}")
        if 'conn' in locals():
            conn.close()
        return None

def run_benchmark():
    """Запускает бенчмарк с разными размерами баз данных и с/без индексации"""
    
    # Результаты для запросов по первичному ключу
    pk_results_with_index = {}
    
    # Результаты для запросов по имени с индексом
    name_results_with_index = {}
    
    # Результаты для запросов по имени без индекса
    name_results_without_index = {}
    
    # Тесты с индексацией по name
    for db_size in DB_SIZES:
        conn = setup_database(db_size, with_index=True)
        if not conn:
            continue
        
        cursor = conn.cursor()
        
        # Тест: запрос по первичному ключу (id)
        pk_times = measure_execution_time(
            lambda: cursor.execute("SELECT * FROM django_users WHERE id = %s", (TEST_USER_ID,)) or cursor.fetchone()
        )
        pk_results_with_index[db_size] = pk_times
        
        # Тест: запрос по имени (с индексом)
        name_times = measure_execution_time(
            lambda: cursor.execute("SELECT * FROM django_users WHERE name = %s", (TEST_NAME,)) or cursor.fetchone()
        )
        name_results_with_index[db_size] = name_times
        
        cursor.close()
        conn.close()
    
    # Тесты без индексации по name
    for db_size in DB_SIZES:
        conn = setup_database(db_size, with_index=False)
        if not conn:
            continue
        
        cursor = conn.cursor()
        
        # Тест: запрос по имени (без индекса)
        name_times = measure_execution_time(
            lambda: cursor.execute("SELECT * FROM django_users WHERE name = %s", (TEST_NAME,)) or cursor.fetchone()
        )
        name_results_without_index[db_size] = name_times
        
        cursor.close()
        conn.close()
    
    # Выводим результаты
    print("\n=== РЕЗУЛЬТАТЫ БЕНЧМАРКА ===\n")
    
    # Запросы по первичному ключу (id)
    print("\nЗапрос по первичному ключу (id):")
    print("-" * 100)
    print(f"{'Размер БД':<10} {'Среднее (ms)':<15} {'Медиана (ms)':<15} {'Мин (ms)':<15} {'Макс (ms)':<15} {'Стд. откл.':<15}")
    print("-" * 100)
    
    baseline_pk = pk_results_with_index[DB_SIZES[0]]['mean']
    for db_size in DB_SIZES:
        result = pk_results_with_index[db_size]
        print(f"{db_size:<10} {result['mean']:<15.3f} {result['median']:<15.3f} {result['min']:<15.3f} {result['max']:<15.3f} {result['stdev']:<15.3f}")
    
    print("-" * 100)
    print(f"Относительная производительность (отношение ко времени с {DB_SIZES[0]} записями):")
    for db_size in DB_SIZES[1:]:
        relative = pk_results_with_index[db_size]['mean'] / baseline_pk
        performance = "медленнее" if relative > 1 else "быстрее"
        print(f"{db_size:<10} {relative:<15.3f}x {performance}")
    
    # Запросы по имени с индексом
    print("\nЗапрос по имени с индексом:")
    print("-" * 100)
    print(f"{'Размер БД':<10} {'Среднее (ms)':<15} {'Медиана (ms)':<15} {'Мин (ms)':<15} {'Макс (ms)':<15} {'Стд. откл.':<15}")
    print("-" * 100)
    
    baseline_name_idx = name_results_with_index[DB_SIZES[0]]['mean']
    for db_size in DB_SIZES:
        result = name_results_with_index[db_size]
        print(f"{db_size:<10} {result['mean']:<15.3f} {result['median']:<15.3f} {result['min']:<15.3f} {result['max']:<15.3f} {result['stdev']:<15.3f}")
    
    print("-" * 100)
    print(f"Относительная производительность (отношение ко времени с {DB_SIZES[0]} записями):")
    for db_size in DB_SIZES[1:]:
        relative = name_results_with_index[db_size]['mean'] / baseline_name_idx
        performance = "медленнее" if relative > 1 else "быстрее"
        print(f"{db_size:<10} {relative:<15.3f}x {performance}")
    
    # Запросы по имени без индекса
    print("\nЗапрос по имени без индекса:")
    print("-" * 100)
    print(f"{'Размер БД':<10} {'Среднее (ms)':<15} {'Медиана (ms)':<15} {'Мин (ms)':<15} {'Макс (ms)':<15} {'Стд. откл.':<15}")
    print("-" * 100)
    
    baseline_name_no_idx = name_results_without_index[DB_SIZES[0]]['mean']
    for db_size in DB_SIZES:
        result = name_results_without_index[db_size]
        print(f"{db_size:<10} {result['mean']:<15.3f} {result['median']:<15.3f} {result['min']:<15.3f} {result['max']:<15.3f} {result['stdev']:<15.3f}")
    
    print("-" * 100)
    print(f"Относительная производительность (отношение ко времени с {DB_SIZES[0]} записями):")
    for db_size in DB_SIZES[1:]:
        relative = name_results_without_index[db_size]['mean'] / baseline_name_no_idx
        performance = "медленнее" if relative > 1 else "быстрее"
        print(f"{db_size:<10} {relative:<15.3f}x {performance}")
    
    # Сравнение запросов с индексом и без индекса
    print("\nСравнение производительности запросов по имени с индексом и без индекса:")
    print("-" * 100)
    print(f"{'Размер БД':<10} {'Без индекса (ms)':<20} {'С индексом (ms)':<20} {'Ускорение':<15}")
    print("-" * 100)
    
    for db_size in DB_SIZES:
        without_idx = name_results_without_index[db_size]['mean']
        with_idx = name_results_with_index[db_size]['mean']
        speedup = without_idx / with_idx
        print(f"{db_size:<10} {without_idx:<20.3f} {with_idx:<20.3f} {speedup:<15.3f}x")

if __name__ == "__main__":
    run_benchmark() 