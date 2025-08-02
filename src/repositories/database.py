from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.models.models import Base

class DatabaseConfig:
    def __init__(self, database_url="sqlite:///leiloes.db"):
        self.engine = create_engine(database_url, echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def create_tables(self):
        """Cria todas as tabelas no banco de dados"""
        Base.metadata.create_all(bind=self.engine)
    
    def drop_tables(self):
        """Remove todas as tabelas do banco de dados"""
        Base.metadata.drop_all(bind=self.engine)
    
    def get_session(self):
        """Retorna uma nova sessão do banco de dados"""
        return self.SessionLocal()

# Instância global da configuração do banco
db_config = DatabaseConfig()