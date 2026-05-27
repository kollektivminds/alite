import factory
from factory.faker import Faker
from factory.declarations import Sequence, SubFactory, LazyAttribute
from factory.alchemy import SQLAlchemyModelFactory
from alite_backend.db import models, schemas
from alite_backend.db.db_session import SessionLocal

TEST_SESSION = None

class BaseFactory(SQLAlchemyModelFactory):
    class Meta: # type: ignore
        abstract = True
        sqlalchemy_session = SessionLocal()
        
    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """
        Overriding standard creation routine to enforce proper session assignment.
        Justification: This configuration guarantees that objects spawned via factory_boy 
        participate in the exact same transactional savepoint as our API Client.
        """
        global TEST_SESSION
        if TEST_SESSION is None:
            raise RuntimeError("Testing session has not been injected into the factory runtime environment.")
        
        # Instantiate object using the transactional session context
        obj = model_class(*args, **kwargs)
        TEST_SESSION.add(obj)
        return obj
        
class UserFactory(BaseFactory):
    class Meta: # type: ignore
        model = models.User
        
    id = Sequence(lambda n: n)
    username = Faker("user_name")
    user_role = models.EnumUserRole.STUDENT
    # email = Sequence(lambda n: f"student_{n}@alite.edu")
    # target_lang = models.EnumTargetLanguage.RU
    
class StudentFactory(UserFactory):
    user_role = models.EnumUserRole.STUDENT
    
class InstructorFactory(UserFactory):
    user_role = models.EnumUserRole.INSTRUCTOR
    
class ExerciseFactory(BaseFactory):
    class Meta: # type: ignore
        model = models.Exercise
        
    user_id = LazyAttribute(lambda obj: StudentFactory().id)
    
    
class ItemResponseFactory(BaseFactory):
    class Meta: # type: ignore
        model = models.ItemResponse
        
    id = Sequence(lambda n: n)
    response_time_ms = Faker("random_int", min=500, max=4000)