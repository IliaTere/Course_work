#!/usr/bin/env python3
import subprocess
import re
import statistics

# Количество запусков бенчмарка
NUM_RUNS = 5

def extract_results(output):
    results = {}
    
    # Регулярное выражение для извлечения результатов
    pattern = r"Получение пользователя с ID 123 из таблицы с (\d+) строками \((ORM|SQL)\): (\d+\.\d+) ms"
    
    for line in output.split('\n'):
        match = re.search(pattern, line)
        if match:
            table_size = match.group(1)
            method = match.group(2)
            time_ms = float(match.group(3))
            
            key = f"{method}_{table_size}"
            if key not in results:
                results[key] = []
            
            results[key].append(time_ms)
            
    return results

def run_multiple_benchmarks():
    all_results = {}
    
    print(f"Запуск бенчмарка {NUM_RUNS} раз...\n")
    
    for i in range(NUM_RUNS):
        print(f"Запуск {i+1}/{NUM_RUNS}...")
        process = subprocess.run(['./benchmark_size.py'], capture_output=True, text=True)
        
        # Извлекаем результаты из вывода
        run_results = extract_results(process.stdout)
        
        # Объединяем результаты
        for key, times in run_results.items():
            if key not in all_results:
                all_results[key] = []
            all_results[key].extend(times)
    
    # Анализируем результаты
    print("\n=== РЕЗУЛЬТАТЫ БЕНЧМАРКА ===\n")
    
    # Форматируем и выводим результаты
    orm_small = all_results.get("ORM_10", [])
    orm_large = all_results.get("ORM_10000", [])
    sql_small = all_results.get("SQL_10", [])
    sql_large = all_results.get("SQL_10000", [])
    
    print("Среднее время запросов:")
    print(f"  ORM, таблица с 10 строками:     {statistics.mean(orm_small):.2f} ms (стд. откл. {statistics.stdev(orm_small):.2f} ms)")
    print(f"  ORM, таблица с 10000 строками:  {statistics.mean(orm_large):.2f} ms (стд. откл. {statistics.stdev(orm_large):.2f} ms)")
    print(f"  SQL, таблица с 10 строками:     {statistics.mean(sql_small):.2f} ms (стд. откл. {statistics.stdev(sql_small):.2f} ms)")
    print(f"  SQL, таблица с 10000 строками:  {statistics.mean(sql_large):.2f} ms (стд. откл. {statistics.stdev(sql_large):.2f} ms)")
    
    print("\nСравнение размеров таблиц:")
    orm_ratio = statistics.mean(orm_large) / statistics.mean(orm_small)
    sql_ratio = statistics.mean(sql_large) / statistics.mean(sql_small)
    
    print(f"  ORM: Запрос в таблице с 10000 строк {'медленнее' if orm_ratio > 1 else 'быстрее'} в {abs(orm_ratio):.2f}x раз")
    print(f"  SQL: Запрос в таблице с 10000 строк {'медленнее' if sql_ratio > 1 else 'быстрее'} в {abs(sql_ratio):.2f}x раз")
    
    print("\nСравнение ORM vs SQL:")
    orm_vs_sql_small = statistics.mean(orm_small) / statistics.mean(sql_small)
    orm_vs_sql_large = statistics.mean(orm_large) / statistics.mean(sql_large)
    
    print(f"  Таблица с 10 строками:    ORM в {orm_vs_sql_small:.2f}x раз медленнее SQL")
    print(f"  Таблица с 10000 строками: ORM в {orm_vs_sql_large:.2f}x раз медленнее SQL")

if __name__ == "__main__":
    run_multiple_benchmarks() 