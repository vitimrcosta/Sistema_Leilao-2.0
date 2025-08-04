import pytest
import tempfile
import os
from sqlalchemy import create_engine, text
from src.repositories.database import DatabaseConfig

class TestDatabaseConfig:
    """Testes para a classe DatabaseConfig"""
    
    def test_create_tables(self):
        """Testa método create_tables - Linha 12"""
        # Criar banco temporário para teste
        db_fd, db_path = tempfile.mkstemp(suffix='.db')
        database_url = f"sqlite:///{db_path}"
        
        try:
            # Criar instância do DatabaseConfig
            db_config = DatabaseConfig(database_url)
            
            # Esta linha executa a linha 12 do database.py
            db_config.create_tables()
            
            # Verificar se as tabelas foram criadas
            session = db_config.get_session()
            
            # Verificar se tabelas existem
            result = session.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
            table_names = [row[0] for row in result.fetchall()]
            
            # Deve ter as tabelas do sistema
            assert 'participantes' in table_names
            assert 'leiloes' in table_names
            assert 'lances' in table_names
            
            session.close()
            
        finally:
            # Cleanup
            try:
                os.close(db_fd)
                os.unlink(db_path)
            except:
                pass
    
    def test_drop_tables(self):
        """Testa método drop_tables - Linha 16"""
        # Criar banco temporário para teste
        db_fd, db_path = tempfile.mkstemp(suffix='.db')
        database_url = f"sqlite:///{db_path}"
        
        try:
            # Criar instância do DatabaseConfig
            db_config = DatabaseConfig(database_url)
            
            # Primeiro criar as tabelas
            db_config.create_tables()
            
            # Verificar que tabelas existem
            session = db_config.get_session()
            result = session.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
            table_names_before = [row[0] for row in result.fetchall()]
            session.close()
            
            assert len(table_names_before) > 0  # Deve ter tabelas
            
            # Esta linha executa a linha 16 do database.py
            db_config.drop_tables()
            
            # Verificar se as tabelas foram removidas
            session = db_config.get_session()
            result = session.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
            table_names_after = [row[0] for row in result.fetchall()]
            session.close()
            
            # Não deve ter mais nossas tabelas (pode ter sqlite_sequence)
            our_tables = ['participantes', 'leiloes', 'lances']
            for table in our_tables:
                assert table not in table_names_after
            
        finally:
            # Cleanup
            try:
                os.close(db_fd)
                os.unlink(db_path)
            except:
                pass
    
    def test_get_session(self):
        """Testa método get_session - Linha 20"""
        # Criar banco temporário para teste
        db_fd, db_path = tempfile.mkstemp(suffix='.db')
        database_url = f"sqlite:///{db_path}"
        
        try:
            # Criar instância do DatabaseConfig
            db_config = DatabaseConfig(database_url)
            
            # Esta linha executa a linha 20 do database.py
            session = db_config.get_session()
            
            # Verificar se retornou uma sessão válida
            assert session is not None
            
            # Verificar se é realmente uma sessão SQLAlchemy
            from sqlalchemy.orm import Session
            assert isinstance(session, Session)
            
            # Verificar se a sessão funciona
            # Tentar executar uma query simples
            result = session.execute(text("SELECT 1"))
            assert result.fetchone()[0] == 1
            
            # Fechar sessão
            session.close()
            
        finally:
            # Cleanup
            try:
                os.close(db_fd)
                os.unlink(db_path)
            except:
                pass
    
    def test_database_config_initialization(self):
        """Testa inicialização do DatabaseConfig"""
        # Teste com URL padrão
        db_config_default = DatabaseConfig()
        assert db_config_default.engine is not None
        assert db_config_default.SessionLocal is not None
        
        # Teste com URL customizada
        custom_url = "sqlite:///test_custom.db"
        db_config_custom = DatabaseConfig(custom_url)
        assert db_config_custom.engine is not None
        assert str(db_config_custom.engine.url) == custom_url
    
    def test_multiple_sessions(self):
        """Testa criação de múltiplas sessões"""
        # Criar banco temporário para teste
        db_fd, db_path = tempfile.mkstemp(suffix='.db')
        database_url = f"sqlite:///{db_path}"
        
        try:
            db_config = DatabaseConfig(database_url)
            
            # Criar múltiplas sessões
            session1 = db_config.get_session()  # Linha 20
            session2 = db_config.get_session()  # Linha 20 novamente
            
            # Verificar que são sessões diferentes
            assert session1 is not session2
            
            # Verificar que ambas funcionam
            result1 = session1.execute(text("SELECT 1"))
            result2 = session2.execute(text("SELECT 2"))
            
            assert result1.fetchone()[0] == 1
            assert result2.fetchone()[0] == 2
            
            # Fechar sessões
            session1.close()
            session2.close()
            
        finally:
            # Cleanup
            try:
                os.close(db_fd)
                os.unlink(db_path)
            except:
                pass
    
    def test_create_drop_cycle(self):
        """Testa ciclo completo: criar -> dropar -> criar novamente"""
        # Criar banco temporário para teste
        db_fd, db_path = tempfile.mkstemp(suffix='.db')
        database_url = f"sqlite:///{db_path}"
        
        try:
            db_config = DatabaseConfig(database_url)
            
            # Ciclo 1: Criar tabelas
            db_config.create_tables()  # Linha 12
            
            session = db_config.get_session()  # Linha 20
            result = session.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
            tables_first = [row[0] for row in result.fetchall()]
            session.close()
            
            assert 'participantes' in tables_first
            
            # Ciclo 2: Dropar tabelas
            db_config.drop_tables()  # Linha 16
            
            session = db_config.get_session()  # Linha 20
            result = session.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
            tables_after_drop = [row[0] for row in result.fetchall()]
            session.close()
            
            assert 'participantes' not in tables_after_drop
            
            # Ciclo 3: Criar novamente
            db_config.create_tables()  # Linha 12
            
            session = db_config.get_session()  # Linha 20
            result = session.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
            tables_recreated = [row[0] for row in result.fetchall()]
            session.close()
            
            assert 'participantes' in tables_recreated
            
        finally:
            # Cleanup
            try:
                os.close(db_fd)
                os.unlink(db_path)
            except:
                pass

class TestDatabaseConfigIntegration:
    """Testes de integração com DatabaseConfig"""
    
    def test_integration_with_models(self):
        """Testa integração do DatabaseConfig com models"""
        # Usar banco temporário
        db_fd, db_path = tempfile.mkstemp(suffix='.db')
        database_url = f"sqlite:///{db_path}"
        
        try:
            db_config = DatabaseConfig(database_url)
            
            # Criar tabelas
            db_config.create_tables()  # Linha 12
            
            # Criar sessão
            session = db_config.get_session()  # Linha 20
            
            # Importar models para testar
            from src.models import Participante
            from datetime import datetime
            
            # Criar um participante de teste
            participante = Participante(
                cpf="12345678901",
                nome="Teste Database",
                email="teste@database.com",
                data_nascimento=datetime(1990, 1, 1)
            )
            
            # Salvar no banco
            session.add(participante)
            session.commit()
            session.refresh(participante)
            
            # Verificar se foi salvo
            assert participante.id is not None
            
            # Buscar do banco
            participante_encontrado = session.query(Participante).filter(
                Participante.cpf == "12345678901"
            ).first()
            
            assert participante_encontrado is not None
            assert participante_encontrado.nome == "Teste Database"
            
            session.close()
            
            # Testar drop_tables
            db_config.drop_tables()  # Linha 16
            
            # Verificar que não consegue mais acessar a tabela
            session2 = db_config.get_session()  # Linha 20
            
            # Esta query deve falhar pois a tabela foi dropada
            with pytest.raises(Exception):  # SQLAlchemy vai dar erro
                session2.query(Participante).first()
            
            session2.close()
            
        finally:
            # Cleanup
            try:
                os.close(db_fd)
                os.unlink(db_path)
            except:
                pass
    
    def test_database_config_singleton_behavior(self):
        """Testa se instâncias diferentes do DatabaseConfig funcionam independentemente"""
        # Criar duas instâncias com bancos diferentes
        db_fd1, db_path1 = tempfile.mkstemp(suffix='_test1.db')
        db_fd2, db_path2 = tempfile.mkstemp(suffix='_test2.db')
        
        try:
            db_config1 = DatabaseConfig(f"sqlite:///{db_path1}")
            db_config2 = DatabaseConfig(f"sqlite:///{db_path2}")
            
            # Criar tabelas em ambos
            db_config1.create_tables()  # Linha 12
            db_config2.create_tables()  # Linha 12
            
            # Sessões de cada instância
            session1 = db_config1.get_session()  # Linha 20
            session2 = db_config2.get_session()  # Linha 20
            
            # Verificar que são diferentes
            assert session1 is not session2
            
            # Verificar que apontam para bancos diferentes
            from src.models import Participante
            from datetime import datetime
            
            # Participante no banco 1
            p1 = Participante(
                cpf="11111111111", nome="Banco 1", 
                email="banco1@teste.com", data_nascimento=datetime(1990, 1, 1)
            )
            session1.add(p1)
            session1.commit()
            
            # Participante no banco 2
            p2 = Participante(
                cpf="22222222222", nome="Banco 2", 
                email="banco2@teste.com", data_nascimento=datetime(1990, 1, 1)
            )
            session2.add(p2)
            session2.commit()
            
            # Verificar isolamento
            count1 = session1.query(Participante).count()
            count2 = session2.query(Participante).count()
            
            assert count1 == 1
            assert count2 == 1
            
            # Verificar que cada banco tem apenas seu participante
            p1_found = session1.query(Participante).filter(Participante.cpf == "11111111111").first()
            p2_not_found = session1.query(Participante).filter(Participante.cpf == "22222222222").first()
            
            assert p1_found is not None
            assert p2_not_found is None
            
            session1.close()
            session2.close()
            
        finally:
            # Cleanup
            try:
                os.close(db_fd1)
                os.close(db_fd2)
                os.unlink(db_path1)
                os.unlink(db_path2)
            except:
                pass