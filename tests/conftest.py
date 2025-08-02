import pytest
import os
import tempfile
from datetime import datetime, timedelta
from src.services.leilao_service import LeilaoService
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Importar nossos módulos
import sys
sys.path.append('..')  # Para importar do diretório pai

from src.models import Base, Participante, Leilao, Lance, StatusLeilao
from src.services.participante_service import ParticipanteService
from src.services.lance_service import LanceService

@pytest.fixture
def lance_service(clean_database):
    """
    Fixture que cria uma instância do LanceService com banco limpo
    """
    service = LanceService()
    service.db_config = clean_database
    return service

@pytest.fixture
def cenario_leilao_aberto(clean_database):
    """
    Fixture que cria um cenário completo: participantes + leilão aberto
    """
    participante_service = ParticipanteService()
    participante_service.db_config = clean_database
    
    leilao_service = LeilaoService()
    leilao_service.db_config = clean_database
    
    # Criar participantes
    p1 = participante_service.criar_participante(
        "12345678901", "João Silva", "joao@teste.com", datetime(1990, 1, 1)
    )
    
    p2 = participante_service.criar_participante(
        "10987654321", "Maria Santos", "maria@teste.com", datetime(1985, 5, 15)
    )
    
    # Criar leilão aberto
    leilao = leilao_service.criar_leilao(
        "PlayStation 5", 1000.0,
        datetime.now() - timedelta(minutes=30),
        datetime.now() + timedelta(hours=1),
        permitir_passado=True
    )
    
    # Abrir leilão
    leilao_service.atualizar_status_leiloes()
    leilao = leilao_service.obter_leilao_por_id(leilao.id)
    
    return {
        'participantes': [p1, p2],
        'leilao': leilao,
        'participante_service': participante_service,
        'leilao_service': leilao_service
    }

@pytest.fixture
def participante_service(clean_database):
    """
    Fixture que cria uma instância do ParticipanteService com banco limpo
    """
    service = ParticipanteService()
    service.db_config = clean_database
    return service

@pytest.fixture
def participante_cadastrado(participante_service, dados_participante_valido):
    """
    Fixture que cria um participante já cadastrado no banco
    """
    participante = participante_service.criar_participante(**dados_participante_valido)
    return participante

@pytest.fixture
def varios_participantes(participante_service):
    """
    Fixture que cria vários participantes para testes de listagem
    """
    participantes = []
    
    # Participante 1
    p1 = participante_service.criar_participante(
        cpf="12345678901",
        nome="João Silva",
        email="joao@teste.com",
        data_nascimento=datetime(1990, 1, 1)
    )
    participantes.append(p1)
    
    # Participante 2
    p2 = participante_service.criar_participante(
        cpf="10987654321", 
        nome="Maria Santos",
        email="maria@teste.com",
        data_nascimento=datetime(1985, 5, 15)
    )
    participantes.append(p2)
    
    # Participante 3
    p3 = participante_service.criar_participante(
        cpf="11122233344",
        nome="Pedro Silva",
        email="pedro@teste.com", 
        data_nascimento=datetime(1992, 10, 20)
    )
    participantes.append(p3)
    
    return participantes

class DatabaseConfig:
    """Configuração de banco para testes"""
    def __init__(self, database_url):
        self.engine = create_engine(database_url, echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def create_tables(self):
        Base.metadata.create_all(bind=self.engine)
    
    def drop_tables(self):
        Base.metadata.drop_all(bind=self.engine)
    
    def get_session(self):
        return self.SessionLocal()

@pytest.fixture(scope="session")
def test_database():
    """
    Fixture que cria um banco de dados temporário para os testes
    Escopo 'session' = criado uma vez para toda a sessão de testes
    """
    # Criar arquivo temporário para o banco de teste
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    database_url = f"sqlite:///{db_path}"
    
    # Configurar banco de teste
    test_db_config = DatabaseConfig(database_url)
    test_db_config.create_tables()
    
    yield test_db_config
    
    # Cleanup - fechar todas as conexões antes de remover arquivo
    try:
        test_db_config.engine.dispose()  # Fechar todas as conexões
        os.close(db_fd)
        os.unlink(db_path)
    except (OSError, PermissionError):
        # No Windows, às vezes o arquivo ainda está em uso
        pass

@pytest.fixture(scope="function")
def clean_database(test_database):
    """
    Fixture que limpa o banco antes de cada teste
    Escopo 'function' = executado antes de cada função de teste
    """
    session = test_database.get_session()
    try:
        # Limpar todas as tabelas na ordem correta (devido às foreign keys)
        session.query(Lance).delete()
        session.query(Leilao).delete()
        session.query(Participante).delete()
        session.commit()
    except Exception:
        session.rollback()
    finally:
        session.close()
    
    yield test_database

@pytest.fixture
def leilao_service(clean_database):
    """
    Fixture que cria uma instância do LeilaoService com banco limpo
    """
    # Temporariamente substituir a configuração do banco no serviço
    service = LeilaoService()
    original_db_config = service.db_config
    service.db_config = clean_database
    
    yield service
    
    # Restaurar configuração original
    service.db_config = original_db_config

@pytest.fixture
def participante_valido(clean_database):
    """
    Fixture que cria um participante válido no banco para testes
    """
    session = clean_database.get_session()
    participante = Participante(
        cpf="12345678901",
        nome="João Silva",
        email="joao@exemplo.com",
        data_nascimento=datetime(1990, 5, 15)
    )
    session.add(participante)
    session.commit()
    session.refresh(participante)
    session.close()
    
    return participante

@pytest.fixture
def leilao_valido(leilao_service):
    """
    Fixture que cria um leilão válido para testes
    """
    data_inicio = datetime.now() + timedelta(hours=1)
    data_termino = datetime.now() + timedelta(days=1)
    
    leilao = leilao_service.criar_leilao(
        nome="PlayStation 5",
        lance_minimo=1000.00,
        data_inicio=data_inicio,
        data_termino=data_termino
    )
    
    return leilao

@pytest.fixture
def leilao_aberto(leilao_service):
    """
    Fixture que cria um leilão no estado ABERTO para testes
    """
    # Criar leilão com data de início no passado (para testes)
    data_inicio = datetime.now() - timedelta(minutes=30)
    data_termino = datetime.now() + timedelta(hours=1)
    
    leilao = leilao_service.criar_leilao(
        nome="Xbox Series X",
        lance_minimo=800.00,
        data_inicio=data_inicio,
        data_termino=data_termino,
        permitir_passado=True  # Permitir data no passado para testes
    )
    
    # Atualizar status para ABERTO
    leilao_service.atualizar_status_leiloes()
    
    # Retornar leilão atualizado
    return leilao_service.obter_leilao_por_id(leilao.id)

@pytest.fixture
def varios_leiloes(leilao_service):
    """
    Fixture que cria vários leilões para testes de listagem
    """
    agora = datetime.now()
    leiloes = []
    
    # Leilão 1 - INATIVO
    leilao1 = leilao_service.criar_leilao(
        "Produto 1", 100.0,
        agora + timedelta(hours=1),
        agora + timedelta(days=1)
    )
    leiloes.append(leilao1)
    
    # Leilão 2 - INATIVO (data diferente)
    leilao2 = leilao_service.criar_leilao(
        "Produto 2", 200.0,
        agora + timedelta(days=2),
        agora + timedelta(days=3)
    )
    leiloes.append(leilao2)
    
    # Leilão 3 - ABERTO (data início no passado)
    leilao3 = leilao_service.criar_leilao(
        "Produto 3", 300.0,
        agora - timedelta(minutes=30),
        agora + timedelta(hours=2),
        permitir_passado=True  # Permitir data no passado para testes
    )
    leiloes.append(leilao3)
    
    # Atualizar status
    leilao_service.atualizar_status_leiloes()
    
    return leiloes

# Dados de teste reutilizáveis
@pytest.fixture
def dados_leilao_valido():
    """Dados válidos para criação de leilão"""
    return {
        'nome': 'Nintendo Switch',
        'lance_minimo': 1200.00,
        'data_inicio': datetime.now() + timedelta(hours=2),
        'data_termino': datetime.now() + timedelta(days=2)
    }

@pytest.fixture
def dados_participante_valido():
    """Dados válidos para criação de participante"""
    return {
        'cpf': '98765432100',
        'nome': 'Maria Santos',
        'email': 'maria@exemplo.com',
        'data_nascimento': datetime(1985, 10, 20)
    }