# tests/factories.py
import factory
from django.contrib.auth import get_user_model
from faker import Faker

fake = Faker()
User = get_user_model()

class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.LazyAttribute(lambda _: fake.user_name())
    email = factory.LazyAttribute(lambda _: fake.email())
    password = factory.PostGenerationMethodCall('set_password', 'testpass123')
    first_name = factory.LazyAttribute(lambda _: fake.first_name())
    last_name = factory.LazyAttribute(lambda _: fake.last_name())
    is_active = True
    
    # For testing user types
    class Params:
        admin = factory.Trait(
            is_staff=True,
            is_superuser=True
        )
        candidate = factory.Trait(
            user_type='candidate'
        )
        employer = factory.Trait(
            user_type='employer'
        )