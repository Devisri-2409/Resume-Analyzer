from database import Base, engine
from models import ResumeAnalysis, User

Base.metadata.create_all(bind=engine)
print("Database tables are ready.")
