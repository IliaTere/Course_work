import numpy as np
import pandas as pd
from scipy import stats

def load_numbers(file_path):
    """Загружает числа из файла (поддержка: txt, csv)."""
    try:
        if file_path.endswith('.csv'):
            data = pd.read_csv(file_path, header=None).values.flatten()
        else:  # txt и другие форматы
            with open(file_path, 'r') as file:
                data = [float(line.strip()) for line in file if line.strip()]
        return np.array(data)
    except Exception as e:
        print(f"Ошибка загрузки файла: {e}")
        return None

def calculate_statistics(data):
    """Вычисляет статистические показатели."""
    if data is None or len(data) == 0:
        return None
    
    stats_dict = {
        "Количество чисел": len(data),
        "Среднее": np.mean(data),
        "Медиана": np.median(data),
        "Минимум": np.min(data),
        "Максимум": np.max(data),
        "Стандартное отклонение": np.std(data),
        "Дисперсия": np.var(data),
        "Коэффициент вариации": (np.std(data) / np.mean(data)) * 100 if np.mean(data) != 0 else np.nan,
        "Асимметрия": stats.skew(data),
        "Эксцесс": stats.kurtosis(data),
        "25-й персентиль": np.percentile(data, 25),
        "75-й персентиль": np.percentile(data, 75),
    }
    return stats_dict

def print_statistics(stats_dict):
    """Выводит статистику в читаемом формате."""
    if not stats_dict:
        print("Нет данных для анализа.")
        return
    
    print("\n📊 Статистический анализ данных:")
    for key, value in stats_dict.items():
        if isinstance(value, float):
            print(f"{key}: {value:.4f}")
        else:
            print(f"{key}: {value}")

if __name__ == "__main__":
    file_path = input("Введите путь к файлу с числами (например, data.txt): ").strip()
    data = load_numbers(file_path)
    
    if data is not None:
        stats_results = calculate_statistics(data)
        print_statistics(stats_results)
        
        # Дополнительно: сохранение результатов в CSV
        save_csv = input("Сохранить результаты в CSV? (y/n): ").lower()
        if save_csv == 'y':
            pd.DataFrame.from_dict(stats_results, orient='index', columns=['Значение']).to_csv('statistics.csv')
            print("Результаты сохранены в 'statistics.csv'.")