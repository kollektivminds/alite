import factory
from factory.faker import Faker
from factory.declarations import Sequence, SubFactory
from factory.alchemy import SQLAlchemyModelFactory
from alite_backend.db import models, schemas
from alite_backend.db.db_session import SessionLocal

class BaseFactory(SQLAlchemyModelFactory):
    class Meta: # type: ignore
        abstract = True
        sqlalchemy_session = SessionLocal()
        
class UserFactory(BaseFactory):
    class Meta: # type: ignore
        model = models.User
        
    id = Sequence(lambda n: n)
    username = Faker("user_name")
    
class StudentFactory(UserFactory):
    user_role = models.EnumUserRole.STUDENT
    
class InstructorFactory(UserFactory):
    user_role = models.EnumUserRole.INSTRUCTOR
    
class ExerciseFactory(BaseFactory):
    class Meta: # type: ignore
        model = models.Exercise
        
    user_id = SubFactory(UserFactory)