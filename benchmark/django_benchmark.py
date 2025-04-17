#!/usr/bin/env python3
import time
import random
import statistics
import psycopg2
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, func
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.ext.declarative import declared_attr
from datetime import datetime, timedelta

# Параметры подключения к PostgreSQL
DB_USER = "benchmark"
DB_PASSWORD = "benchmark"
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "benchmark"
DB_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# ID тестового пользователя, который будет запрашиваться
TEST_USER_ID = 42

# Размеры баз данных для тестирования
DB_SIZES = [1, 10, 100, 1000, 10000]

# Количество повторений для каждого теста
NUM_RUNS = 10

# Инициализация SQLAlchemy (имитация Django ORM)
engine = create_engine(DB_URL)
Base = declarative_base()
Session = sessionmaker(bind=engine)

# Базовый класс модели (имитация Django Model)
class DjangoBase:
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()
    
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

# Модель пользователя (имитация Django User model)
class User(Base, DjangoBase):
    username = Column(String(150), unique=True, nullable=False)
    email = Column(String(254), unique=True, nullable=False)
    first_name = Column(String(150), nullable=False, default='')
    last_name = Column(String(150), nullable=False, default='')
    is_active = Column(Boolean, nullable=False, default=True)
    is_staff = Column(Boolean, nullable=False, default=False)
    date_joined = Column(DateTime, nullable=False, default=func.now())
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}')>"

# Модель поста (имитация Django Post model)
class Post(Base, DjangoBase):
    title = Column(String(200), nullable=False)
    content = Column(String(10000), nullable=False)
    author_id = Column(Integer, nullable=False)
    is_published = Column(Boolean, nullable=False, default=True)
    
    def __repr__(self):
        return f"<Post(id={self.id}, title='{self.title}')>"

# Модель комментария (имитация Django Comment model)
class Comment(Base, DjangoBase):
    post_id = Column(Integer, nullable=False)
    author_id = Column(Integer, nullable=False)
    content = Column(String(1000), nullable=False)
    is_approved = Column(Boolean, nullable=False, default=True)
    
    def __repr__(self):
        return f"<Comment(id={self.id}, post_id={self.post_id})>"

# Функция для генерации случайной даты в прошлом
def random_past_date():
    days_ago = random.randint(1, 1000)
    return datetime.now() - timedelta(days=days_ago)

# Функция для замера времени выполнения
def measure_execution_time(func):
    times = []
    for _ in range(NUM_RUNS):
        start_time = time.time()
        result = func()
        end_time = time.time()
        times.append((end_time - start_time) * 1000)  # Время в миллисекундах
    
    return {
        'mean': statistics.mean(times),
        'median': statistics.median(times),
        'stdev': statistics.stdev(times) if len(times) > 1 else 0,
        'min': min(times),
        'max': max(times)
    }

def setup_database(db_size):
    """Настраивает базу данных с заданным количеством записей"""
    print(f"\nНастройка базы данных с {db_size} пользователями...")
    
    # Пересоздаем таблицы
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    
    session = Session()
    
    # Создаем тестового пользователя, которого будем запрашивать
    test_user = User(
        id=TEST_USER_ID,
        username=f"testuser{TEST_USER_ID}",
        email=f"testuser{TEST_USER_ID}@example.com",
        first_name="Test",
        last_name="User",
        is_active=True,
        is_staff=False,
        date_joined=random_past_date()
    )
    session.add(test_user)
    
    # Создаем остальных пользователей
    remaining_users = db_size - 1
    if remaining_users > 0:
        batch_size = 1000
        for i in range(1, remaining_users + 1):
            user_id = i if i < TEST_USER_ID else i + 1  # Пропускаем ID тестового пользователя
            user = User(
                id=user_id,
                username=f"user{user_id}",
                email=f"user{user_id}@example.com",
                first_name=f"First{user_id}",
                last_name=f"Last{user_id}",
                is_active=random.choice([True, True, True, False]),  # 75% активных
                is_staff=random.choice([False, False, False, True]),  # 25% сотрудников
                date_joined=random_past_date()
            )
            session.add(user)
            
            # Добавляем посты для пользователя (в среднем 2 поста на пользователя)
            num_posts = random.randint(0, 4)
            for j in range(num_posts):
                post = Post(
                    title=f"Post {j+1} by User {user_id}",
                    content=f"This is post content {j+1} by user {user_id}. " * random.randint(1, 10),
                    author_id=user_id,
                    is_published=random.choice([True, True, True, False])  # 75% опубликованных
                )
                session.add(post)
                
                # Добавляем комментарии к посту (в среднем 3 комментария на пост)
                num_comments = random.randint(0, 6)
                for k in range(num_comments):
                    comment_author_id = random.randint(1, db_size)
                    if comment_author_id == TEST_USER_ID:
                        comment_author_id = random.randint(1, db_size)  # Повторная попытка, чтобы снизить вероятность
                    
                    comment = Comment(
                        post_id=post.id if post.id else 1,
                        author_id=comment_author_id,
                        content=f"This is comment {k+1} for post {j+1} by user {comment_author_id}. " * random.randint(1, 3),
                        is_approved=random.choice([True, True, True, False])  # 75% одобренных
                    )
                    session.add(comment)
            
            # Сохраняем каждые batch_size записей, чтобы не перегружать память
            if i % batch_size == 0 or i == remaining_users:
                session.commit()
    
    session.commit()
    session.close()
    print(f"База данных настроена: {db_size} пользователей")

def run_django_benchmark():
    """Имитирует запросы Django ORM"""
    results = {}
    
    # Тест 1: Получение пользователя с заданным ID - простой запрос
    for db_size in DB_SIZES:
        setup_database(db_size)
        
        # Создаем новую сессию для тестирования
        session = Session()
        
        # Тест: User.objects.get(id=TEST_USER_ID)
        times = measure_execution_time(
            lambda: session.query(User).filter(User.id == TEST_USER_ID).first()
        )
        results[f'get_by_id_{db_size}'] = times
        
        # Тест: User.objects.filter(id=TEST_USER_ID).first()
        times = measure_execution_time(
            lambda: session.query(User).filter(User.id == TEST_USER_ID).first()
        )
        results[f'filter_by_id_{db_size}'] = times
        
        # Тест: User.objects.get(username='testuser42')
        times = measure_execution_time(
            lambda: session.query(User).filter(User.username == f"testuser{TEST_USER_ID}").first()
        )
        results[f'get_by_username_{db_size}'] = times
        
        # Тест: сложный запрос - поиск активных пользователей с постами
        times = measure_execution_time(
            lambda: session.query(User).filter(
                User.is_active == True,
                User.id == TEST_USER_ID
            ).first()
        )
        results[f'complex_query_{db_size}'] = times
        
        session.close()
    
    # Выводим результаты
    print("\n=== РЕЗУЛЬТАТЫ ТЕСТОВ ===\n")
    
    test_names = [
        ('get_by_id', 'User.objects.get(id=42)'),
        ('filter_by_id', 'User.objects.filter(id=42).first()'),
        ('get_by_username', 'User.objects.get(username="testuser42")'),
        ('complex_query', 'User.objects.filter(is_active=True, id=42).first()')
    ]
    
    for test_code, test_name in test_names:
        print(f"\n{test_name}:")
        print("-" * 80)
        print(f"{'Размер БД':<10} {'Среднее (ms)':<15} {'Медиана (ms)':<15} {'Мин (ms)':<15} {'Макс (ms)':<15} {'Стд. откл.':<15}")
        print("-" * 80)
        
        for db_size in DB_SIZES:
            key = f'{test_code}_{db_size}'
            result = results[key]
            print(f"{db_size:<10} {result['mean']:<15.3f} {result['median']:<15.3f} {result['min']:<15.3f} {result['max']:<15.3f} {result['stdev']:<15.3f}")
        
        # Сравнение с базой в 1 запись
        baseline = results[f'{test_code}_1']['mean']
        print("-" * 80)
        print(f"Относительная производительность (отношение ко времени с 1 записью):")
        for db_size in DB_SIZES[1:]:  # Пропускаем первый элемент (1 запись)
            key = f'{test_code}_{db_size}'
            relative = results[key]['mean'] / baseline
            performance = "медленнее" if relative > 1 else "быстрее"
            print(f"{db_size:<10} {relative:<15.3f}x {performance}")

if __name__ == "__main__":
    run_django_benchmark() 