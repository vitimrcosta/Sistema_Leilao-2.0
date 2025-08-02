import pytest
from datetime import datetime, timedelta
from src.models import Leilao, Participante, Lance, StatusLeilao
from src.services import EmailService, LeilaoService, ParticipanteService, LanceService

class TestEmailService:
    """Testes para o EmailService"""
    
    def test_email_service_modo_teste(self, clean_database):
        """Teste: EmailService em modo teste (sem credenciais reais)"""
        email_service = EmailService()
        
        # Deve estar em modo teste por padrão
        assert email_service.modo_teste is True
        assert email_service.email_usuario == "sistema.leiloes@exemplo.com"
    
    def test_enviar_email_vencedor_modo_simulacao(self, clean_database):
        """Teste: Enviar email de vitória em modo simulação"""
        # Setup
        participante_service = ParticipanteService()
        participante_service.db_config = clean_database
        
        leilao_service = LeilaoService()
        leilao_service.db_config = clean_database
        
        email_service = EmailService()
        
        # Criar participante
        participante = participante_service.criar_participante(
            "12345678901", "João Silva", "joao@teste.com", datetime(1990, 1, 1)
        )
        
        # Criar leilão
        leilao = leilao_service.criar_leilao(
            "PlayStation 5", 1000.0,
            datetime.now() - timedelta(hours=1),
            datetime.now() - timedelta(minutes=10),
            permitir_passado=True
        )
        
        # Enviar email (modo simulação)
        sucesso = email_service.enviar_email_vencedor(leilao, participante, 1500.0)
        
        assert sucesso is True
    
    def test_criar_email_personalizado(self, clean_database):
        """Teste: Criar email personalizado"""
        email_service = EmailService()
        
        sucesso = email_service.criar_email_personalizado(
            nome_participante="Maria Santos",
            email_destino="maria@teste.com",
            assunto="Teste do Sistema",
            mensagem="Esta é uma mensagem de teste do sistema de leilões."
        )
        
        assert sucesso is True
    
    def test_integracao_email_com_finalizacao_leilao(self, clean_database):
        """Teste de integração: Email automático quando leilão finaliza"""
        # Setup completo
        participante_service = ParticipanteService()
        participante_service.db_config = clean_database
        
        leilao_service = LeilaoService()
        leilao_service.db_config = clean_database
        
        lance_service = LanceService()
        lance_service.db_config = clean_database
        
        # Criar participantes
        p1 = participante_service.criar_participante(
            "12345678901", "João", "joao@teste.com", datetime(1990, 1, 1)
        )
        
        p2 = participante_service.criar_participante(
            "10987654321", "Maria", "maria@teste.com", datetime(1985, 5, 15)
        )
        
        # Criar leilão que vai finalizar
        leilao = leilao_service.criar_leilao(
            "Xbox Series X", 800.0,
            datetime.now() - timedelta(minutes=30),
            datetime.now() + timedelta(minutes=1),  # Vai terminar logo
            permitir_passado=True
        )
        
        # Abrir leilão
        leilao_service.atualizar_status_leiloes(enviar_emails=False)
        
        # Fazer lances
        lance_service.criar_lance(p1.id, leilao.id, 900.0)  # João
        lance_service.criar_lance(p2.id, leilao.id, 1000.0)  # Maria (vencedora)
        
        # Forçar finalização do leilão
        session = clean_database.get_session()
        leilao_db = session.query(Leilao).filter(Leilao.id == leilao.id).first()
        leilao_db.data_termino = datetime.now() - timedelta(minutes=1)
        session.commit()
        session.close()
        
        # Atualizar status COM envio de emails
        resultado = leilao_service.atualizar_status_leiloes(enviar_emails=True)
        
        # Verificar resultados
        assert resultado['finalizados'] == 1
        assert resultado['emails_enviados'] == 1
        
        # Verificar que leilão foi finalizado corretamente
        leilao_final = leilao_service.obter_leilao_por_id(leilao.id)
        assert leilao_final.status == StatusLeilao.FINALIZADO
        assert leilao_final.participante_vencedor_id == p2.id  # Maria venceu
    
    def test_notificar_vencedores_pendentes(self, clean_database):
        """Teste: Notificar múltiplos vencedores pendentes"""
        # Setup
        participante_service = ParticipanteService()
        participante_service.db_config = clean_database
        
        leilao_service = LeilaoService()
        leilao_service.db_config = clean_database
        
        lance_service = LanceService()
        lance_service.db_config = clean_database
        
        email_service = EmailService()
        
        # Criar participantes
        p1 = participante_service.criar_participante(
            "12345678901", "João", "joao@teste.com", datetime(1990, 1, 1)
        )
        
        p2 = participante_service.criar_participante(
            "10987654321", "Maria", "maria@teste.com", datetime(1985, 5, 15)
        )
        
        # Criar 2 leilões finalizados
        leilao1 = leilao_service.criar_leilao(
            "Produto 1", 100.0,
            datetime.now() - timedelta(hours=2),
            datetime.now() - timedelta(hours=1),
            permitir_passado=True
        )
        
        leilao2 = leilao_service.criar_leilao(
            "Produto 2", 200.0,
            datetime.now() - timedelta(hours=2),
            datetime.now() - timedelta(hours=1),
            permitir_passado=True
        )
        
        # Fazer lances e finalizar leilões SEM envio de email
        lance_service.criar_lance(p1.id, leilao1.id, 150.0)  # João vence leilão1
        lance_service.criar_lance(p2.id, leilao2.id, 250.0)  # Maria vence leilão2
        
        leilao_service.atualizar_status_leiloes(enviar_emails=False)
        
        # Agora notificar vencedores pendentes
        resultado = email_service.notificar_vencedores_pendentes(leilao_service)
        
        assert resultado['emails_enviados'] == 2
        assert resultado['emails_falharam'] == 0
        assert len(resultado['detalhes']) == 2
    
    def test_email_service_com_credenciais_reais(self):
        """Teste: EmailService com credenciais reais (modo produção)"""
        email_service = EmailService(
            email_usuario="teste@gmail.com",
            email_senha="senha123"
        )
        
        # Deve estar em modo produção
        assert email_service.modo_teste is False
        assert email_service.email_usuario == "teste@gmail.com"
    
    def test_leiloes_que_precisa_notificar(self, clean_database):
        """Teste: Listar leilões que precisam notificar vencedores"""
        # Setup
        participante_service = ParticipanteService()
        participante_service.db_config = clean_database
        
        leilao_service = LeilaoService()
        leilao_service.db_config = clean_database
        
        lance_service = LanceService()
        lance_service.db_config = clean_database
        
        # Criar participante
        participante = participante_service.criar_participante(
            "12345678901", "João", "joao@teste.com", datetime(1990, 1, 1)
        )
        
        # Criar leilão finalizado
        leilao = leilao_service.criar_leilao(
            "Produto Finalizado", 100.0,
            datetime.now() - timedelta(hours=1),
            datetime.now() - timedelta(minutes=30),
            permitir_passado=True
        )
        
        # Fazer lance e finalizar
        lance_service.criar_lance(participante.id, leilao.id, 150.0)
        leilao_service.atualizar_status_leiloes(enviar_emails=False)
        
        # Buscar leilões que precisam notificar
        leiloes_notificar = leilao_service.leiloes_que_precisa_notificar()
        
        assert len(leiloes_notificar) == 1
        assert leiloes_notificar[0].id == leilao.id
        assert leiloes_notificar[0].status == StatusLeilao.FINALIZADO
        assert leiloes_notificar[0].participante_vencedor_id == participante.id

class TestEmailServiceValidacoes:
    """Testes específicos para validações do EmailService"""
    
    def test_email_sem_vencedor_definido(self, clean_database):
        """Teste: Tentar enviar email para leilão sem vencedor"""
        leilao_service = LeilaoService()
        leilao_service.db_config = clean_database
        
        participante_service = ParticipanteService()
        participante_service.db_config = clean_database
        
        email_service = EmailService()
        
        # Criar leilão sem vencedor
        leilao = leilao_service.criar_leilao(
            "Produto Sem Vencedor", 100.0,
            datetime.now() - timedelta(hours=1),
            datetime.now() - timedelta(minutes=30),
            permitir_passado=True
        )
        
        # Criar participante
        participante = participante_service.criar_participante(
            "12345678901", "João", "joao@teste.com", datetime(1990, 1, 1)
        )
        
        # Tentar enviar email (deve funcionar mesmo sem vencedor formal)
        sucesso = email_service.enviar_email_vencedor(leilao, participante, 150.0)
        
        # Deve funcionar pois é simulação
        assert sucesso is True
    
    def test_notificar_sem_leiloes_finalizados(self, clean_database):
        """Teste: Notificar quando não há leilões finalizados"""
        leilao_service = LeilaoService()
        leilao_service.db_config = clean_database
        
        email_service = EmailService()
        
        # Não criar leilões finalizados
        resultado = email_service.notificar_vencedores_pendentes(leilao_service)
        
        assert resultado['emails_enviados'] == 0
        assert resultado['emails_falharam'] == 0
        assert len(resultado['detalhes']) == 0