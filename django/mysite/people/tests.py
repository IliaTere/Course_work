from django.test import TestCase
from .models import Person, Address, Hobby, Category, Product, Review
import time
import random
from django.core.management import call_command


class PersonModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create test data for the first trio of models
        # Create multiple persons
        cls.person1 = Person.objects.create(name="John Doe", age=30, email="john@example.com", bio="Test bio 1")
        cls.person2 = Person.objects.create(name="Jane Smith", age=25, email="jane@example.com", bio="Test bio 2")
        cls.person3 = Person.objects.create(name="Bob Johnson", age=40, email="bob@example.com", bio="Test bio 3")
        
        # Create addresses
        cls.address1 = Address.objects.create(
            person=cls.person1, 
            street="123 Main St", 
            city="New York", 
            state="NY", 
            zip_code="10001", 
            country="USA"
        )
        cls.address2 = Address.objects.create(
            person=cls.person2, 
            street="456 Park Ave", 
            city="Boston", 
            state="MA", 
            zip_code="02108", 
            country="USA"
        )
        cls.address3 = Address.objects.create(
            person=cls.person3, 
            street="789 Oak St", 
            city="Chicago", 
            state="IL", 
            zip_code="60601", 
            country="USA"
        )
        
        # Create hobbies
        cls.hobby1 = Hobby.objects.create(name="Reading", description="Reading books")
        cls.hobby2 = Hobby.objects.create(name="Swimming", description="Swimming in the pool")
        cls.hobby3 = Hobby.objects.create(name="Hiking", description="Hiking in mountains")
        
        # Add hobbies to persons
        cls.person1.hobbies.add(cls.hobby1, cls.hobby2)
        cls.person2.hobbies.add(cls.hobby2, cls.hobby3)
        cls.person3.hobbies.add(cls.hobby1, cls.hobby3)

    def test_filter_person_by_address_and_hobby_small_data(self):
        """Test filtering person by address and hobby with small dataset"""
        # Измеряем только время выполнения запросов
        start_time = time.time()
        
        # Find persons who live in New York and like Reading
        filtered_person = Person.objects.filter(
            address__city="New York",
            hobbies__name="Reading"
        ).first()
        
        # Check if we found the right person
        self.assertIsNotNone(filtered_person)
        self.assertEqual(filtered_person.name, "John Doe")
        
        # Update the person's bio
        filtered_person.bio = "Updated bio for testing"
        filtered_person.save()
        
        # Verify the update was successful
        updated_person = Person.objects.get(id=filtered_person.id)
        self.assertEqual(updated_person.bio, "Updated bio for testing")
        
        end_time = time.time()
        print(f"Small dataset query execution time: {end_time - start_time:.6f} seconds")


class SmallDataProductTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create small dataset for performance testing
        # Create category
        cls.electronics = Category.objects.create(
            name="Electronics",
            description="Electronic devices and gadgets",
            slug="electronics"
        )
        
        # Create product
        cls.laptop = Product.objects.create(
            name="Laptop",
            description="Powerful laptop for testing",
            price=999.99,
            stock=10,
            category=cls.electronics,
            is_active=True
        )
        
        # Create review
        cls.review = Review.objects.create(
            product=cls.laptop,
            author_name="Test Reviewer",
            rating=5,
            comment="Excellent laptop for testing!"
        )

    def test_filter_product_by_category_and_review(self):
        """Test filtering product by category and review rating with small dataset"""
        # Измеряем только время выполнения запросов
        start_time = time.time()
        
        # Find products in Electronics category with 5-star reviews
        filtered_product = Product.objects.filter(
            category__name="Electronics",
            reviews__rating=5
        ).first()
        
        # Check if we found a product
        self.assertIsNotNone(filtered_product, 
                             "No product found in Electronics category with 5-star review.")
        
        # Store the original stock value
        original_stock = filtered_product.stock
        
        # Update the product's stock
        new_stock = original_stock - 1 if original_stock > 0 else original_stock + 1
        filtered_product.stock = new_stock
        filtered_product.save()
        
        # Verify the update was successful
        updated_product = Product.objects.get(id=filtered_product.id)
        self.assertEqual(updated_product.stock, new_stock)
        
        # Restore the original stock value
        updated_product.stock = original_stock
        updated_product.save()
        
        end_time = time.time()
        print(f"Small dataset query execution time: {end_time - start_time:.6f} seconds")


class LargeDataProductTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create large dataset for performance testing
        # Create multiple categories
        cls.categories = []
        for i in range(100):
            category = Category.objects.create(
                name=f"Category {i}",
                description=f"Description for category {i}",
                slug=f"category-{i}"
            )
            cls.categories.append(category)
        
        # Create Electronics category
        cls.electronics = Category.objects.create(
            name="Electronics",
            description="Electronic devices and gadgets",
            slug="electronics"
        )
        cls.categories.append(cls.electronics)
        
        # Create 10000 products
        cls.products = []
        for i in range(10000):
            # 10% of products in Electronics category
            if i < 1000:
                category = cls.electronics
            else:
                category = random.choice(cls.categories)
            
            product = Product.objects.create(
                name=f"Product {i}",
                description=f"Description for product {i}",
                price=random.uniform(10.0, 2000.0),
                stock=random.randint(0, 100),
                category=category,
                is_active=random.choice([True, True, True, False])
            )
            cls.products.append(product)
        
        # Create 10000 reviews
        for i in range(10000):
            # 1% of reviews for Laptop product
            if i < 100:
                product = cls.products[0]  # First product (Laptop)
            else:
                product = random.choice(cls.products)
            
            Review.objects.create(
                product=product,
                author_name=f"Reviewer {i}",
                rating=random.randint(1, 5),
                comment=f"Review comment {i}"
            )
        
        # Ensure we have a 5-star review for the Laptop
        Review.objects.create(
            product=cls.products[0],
            author_name="Test Reviewer",
            rating=5,
            comment="Excellent laptop for testing!"
        )

    def test_filter_product_by_category_and_review(self):
        """Test filtering product by category and review rating with large dataset"""
        # Измеряем только время выполнения запросов
        start_time = time.time()
        
        # Find products in Electronics category with 5-star reviews
        filtered_product = Product.objects.filter(
            category__name="Electronics",
            reviews__rating=5
        ).first()
        
        # Check if we found a product
        self.assertIsNotNone(filtered_product, 
                             "No product found in Electronics category with 5-star review.")
        
        # Store the original stock value
        original_stock = filtered_product.stock
        
        # Update the product's stock
        new_stock = original_stock - 1 if original_stock > 0 else original_stock + 1
        filtered_product.stock = new_stock
        filtered_product.save()
        
        # Verify the update was successful
        updated_product = Product.objects.get(id=filtered_product.id)
        self.assertEqual(updated_product.stock, new_stock)
        
        # Restore the original stock value
        updated_product.stock = original_stock
        updated_product.save()
        
        end_time = time.time()
        print(f"Large dataset query execution time: {end_time - start_time:.6f} seconds")

