#!/usr/bin/env python3
import subprocess
import re

# Количество прогонов каждого теста
RUNS = 5

def extract_results(output):
    results = {}
    for line in output.split('\n'):
        match = re.search(r'(Получение.+): (\d+\.\d+) ms', line)
        if match:
            operation = match.group(1)
            time_ms = float(match.group(2))
            if operation not in results:
                results[operation] = []
            results[operation].append(time_ms)
    return results

def run_benchmarks():
    orm_results = {}
    raw_results = {}
    
    print(f"Запуск каждого бенчмарка {RUNS} раз...\n")
    
    # Запускаем ORM бенчмарк несколько раз
    print("Запуск бенчмарка с SQLAlchemy ORM:")
    for i in range(RUNS):
        print(f"  Прогон {i+1}/{RUNS}...")
        process = subprocess.run(['./benchmark.py'], capture_output=True, text=True)
        run_results = extract_results(process.stdout)
        
        for operation, times in run_results.items():
            if operation not in orm_results:
                orm_results[operation] = []
            orm_results[operation].extend(times)
    
    # Запускаем RAW SQL бенчмарк несколько раз
    print("\nЗапуск бенчмарка с чистым SQL:")
    for i in range(RUNS):
        print(f"  Прогон {i+1}/{RUNS}...")
        process = subprocess.run(['./benchmark_raw.py'], capture_output=True, text=True)
        run_results = extract_results(process.stdout)
        
        for operation, times in run_results.items():
            if operation not in raw_results:
                raw_results[operation] = []
            raw_results[operation].extend(times)
    
    # Вычисляем средние результаты
    print("\n=== РЕЗУЛЬТАТЫ БЕНЧМАРКА ===")
    print("\nСреднее время выполнения с SQLAlchemy ORM:")
    for operation, times in orm_results.items():
        avg_time = sum(times) / len(times)
        print(f"{operation}: {avg_time:.2f} ms")
    
    print("\nСреднее время выполнения с чистым SQL:")
    for operation, times in raw_results.items():
        avg_time = sum(times) / len(times)
        print(f"{operation}: {avg_time:.2f} ms")
    
    print("\nСравнение (ORM vs SQL):")
    for operation in orm_results.keys():
        orm_avg = sum(orm_results[operation]) / len(orm_results[operation])
        raw_avg = sum(raw_results[operation]) / len(raw_results[operation])
        ratio = orm_avg / raw_avg
        print(f"{operation}: ORM в {ratio:.2f}x раз медленнее чистого SQL")

if __name__ == "__main__":
    run_benchmarks() 