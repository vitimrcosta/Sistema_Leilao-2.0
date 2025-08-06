import pytest
from datetime import datetime, timedelta
from src.models import Leilao, Participante, Lance, StatusLeilao
from src.services import EmailService, LeilaoService, ParticipanteService, LanceService
from src.utils import ValidationError  # ← ADICIONAR ESTA LINHA
from unittest.mock import patch, MagicMock

class TestEmailService:
    """Testes para o EmailService"""
    
    def test_email_service_modo_teste_forcado(self, clean_database):
        """Teste: EmailService em modo teste forçado"""
        # Usar método que força modo teste
        email_service = EmailService.criar_para_testes()
        
        # Deve estar em modo teste quando forçado
        assert email_service.modo_teste is True
        assert email_service.modo_producao is False
    
    def test_email_service_modo_producao_forcado(self, clean_database):
        """Teste: EmailService em modo produção forçado"""
        # Usar método que força modo produção
        email_service = EmailService.criar_para_producao()
        
        # Deve estar em modo produção quando forçado
        assert email_service.modo_producao is True
        assert email_service.modo_teste is False
    
    def test_enviar_email_vencedor_modo_simulacao(self, clean_database):
        """Teste: Enviar email de vitória em modo simulação"""
        # Setup
        participante_service = ParticipanteService()
        participante_service.db_config = clean_database
        
        leilao_service = LeilaoService()
        leilao_service.db_config = clean_database
        
        # Forçar modo teste
        email_service = EmailService.criar_para_testes()
        
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
        # Forçar modo teste
        email_service = EmailService.criar_para_testes()
        
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
        
        # IMPORTANTE: Abrir leilão ANTES de fazer lances
        leilao_service.atualizar_status_leiloes(enviar_emails=False)
        
        # Verificar se o leilão está aberto
        leilao_atualizado = leilao_service.obter_leilao_por_id(leilao.id)
        assert leilao_atualizado.status == StatusLeilao.ABERTO
        
        # Fazer lances
        lance_service.criar_lance(p1.id, leilao.id, 900.0)  # João
        lance_service.criar_lance(p2.id, leilao.id, 1000.0)  # Maria (vencedora)
        
        # Forçar finalização do leilão
        session = clean_database.get_session()
        leilao_db = session.query(Leilao).filter(Leilao.id == leilao.id).first()
        leilao_db.data_termino = datetime.now() - timedelta(minutes=1)
        session.commit()
        session.close()
        
        # Atualizar status COM envio de emails (vai simular)
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
        
        # Forçar modo teste
        email_service = EmailService.criar_para_testes()
        
        # Criar participantes
        p1 = participante_service.criar_participante(
            "12345678901", "João", "joao@teste.com", datetime(1990, 1, 1)
        )
        
        p2 = participante_service.criar_participante(
            "10987654321", "Maria", "maria@teste.com", datetime(1985, 5, 15)
        )
        
        # Criar 2 leilões que vão ser abertos
        leilao1 = leilao_service.criar_leilao(
            "Produto 1", 100.0,
            datetime.now() - timedelta(hours=2),  # Já começou
            datetime.now() + timedelta(minutes=5),  # Ainda não terminou
            permitir_passado=True
        )
        
        leilao2 = leilao_service.criar_leilao(
            "Produto 2", 200.0,
            datetime.now() - timedelta(hours=2),  # Já começou
            datetime.now() + timedelta(minutes=10),  # Ainda não terminou
            permitir_passado=True
        )
        
        # IMPORTANTE: Abrir os leilões ANTES de fazer lances
        leilao_service.atualizar_status_leiloes(enviar_emails=False)
        
        # Verificar se os leilões estão abertos
        leilao1_atualizado = leilao_service.obter_leilao_por_id(leilao1.id)
        leilao2_atualizado = leilao_service.obter_leilao_por_id(leilao2.id)
        assert leilao1_atualizado.status == StatusLeilao.ABERTO
        assert leilao2_atualizado.status == StatusLeilao.ABERTO
        
        # Fazer lances
        lance_service.criar_lance(p1.id, leilao1.id, 150.0)  # João vence leilão1
        lance_service.criar_lance(p2.id, leilao2.id, 250.0)  # Maria vence leilão2
        
        # Forçar finalização dos leilões
        session = clean_database.get_session()
        
        # Finalizar leilão 1
        leilao1_db = session.query(Leilao).filter(Leilao.id == leilao1.id).first()
        leilao1_db.data_termino = datetime.now() - timedelta(minutes=1)
        
        # Finalizar leilão 2
        leilao2_db = session.query(Leilao).filter(Leilao.id == leilao2.id).first()
        leilao2_db.data_termino = datetime.now() - timedelta(minutes=1)
        
        session.commit()
        session.close()
        
        # Finalizar leilões SEM envio de email primeiro
        leilao_service.atualizar_status_leiloes(enviar_emails=False)
        
        # Agora notificar vencedores pendentes
        resultado = email_service.notificar_vencedores_pendentes(leilao_service)
        
        assert resultado['emails_enviados'] == 2
        assert resultado['emails_falharam'] == 0
        assert len(resultado['detalhes']) == 2
    
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
        
        # Criar leilão que vai ser aberto
        leilao = leilao_service.criar_leilao(
            "Produto Finalizado", 100.0,
            datetime.now() - timedelta(hours=1),  # Já começou
            datetime.now() + timedelta(minutes=5),  # Ainda não terminou
            permitir_passado=True
        )
        
        # IMPORTANTE: Abrir leilão ANTES de fazer lance
        leilao_service.atualizar_status_leiloes(enviar_emails=False)
        
        # Verificar se o leilão está aberto
        leilao_atualizado = leilao_service.obter_leilao_por_id(leilao.id)
        assert leilao_atualizado.status == StatusLeilao.ABERTO
        
        # Fazer lance
        lance_service.criar_lance(participante.id, leilao.id, 150.0)
        
        # Forçar finalização
        session = clean_database.get_session()
        leilao_db = session.query(Leilao).filter(Leilao.id == leilao.id).first()
        leilao_db.data_termino = datetime.now() - timedelta(minutes=1)
        session.commit()
        session.close()
        
        # Finalizar sem envio de email
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
        
        # Forçar modo teste
        email_service = EmailService.criar_para_testes()
        
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
        
        # Forçar modo teste
        email_service = EmailService.criar_para_testes()
        
        # Não criar leilões finalizados
        resultado = email_service.notificar_vencedores_pendentes(leilao_service)
        
        assert resultado['emails_enviados'] == 0
        assert resultado['emails_falharam'] == 0
        assert len(resultado['detalhes']) == 0
    
    def test_metodos_conveniencia(self, clean_database):
        """Teste: Métodos de conveniência para criar EmailService"""
        
        # Teste modo
        email_teste = EmailService.criar_para_testes()
        assert email_teste.modo_teste is True
        assert email_teste.modo_producao is False
        
        # Produção forçada
        email_prod = EmailService.criar_para_producao()
        assert email_prod.modo_producao is True
        assert email_prod.modo_teste is False
        
        # Do .env
        email_env = EmailService.criar_do_env()
        assert email_env is not None  # Deve criar sem erro

class TestEmailServiceCobertura:
    """Testes específicos para cobrir linhas não testadas do EmailService"""
    
    def test_modo_production_forcado_linha_63(self, clean_database):
        """Testa linha 63: return True quando EMAIL_MODE=PRODUCTION"""
        import os
        
        # Salvar valor original
        original_mode = os.environ.get('EMAIL_MODE')
        
        try:
            # Forçar modo PRODUCTION via variável de ambiente
            os.environ['EMAIL_MODE'] = 'PRODUCTION'
            
            # Criar EmailService (vai detectar modo PRODUCTION)
            email_service = EmailService(
                email_usuario="teste@gmail.com",
                email_senha="senha_qualquer"
            )
            
            # Deve estar em modo produção (linha 63 executada)
            assert email_service.modo_producao is True
            assert email_service.modo_teste is False
            
        finally:
            # Restaurar valor original
            if original_mode is not None:
                os.environ['EMAIL_MODE'] = original_mode
            else:
                if 'EMAIL_MODE' in os.environ:
                    del os.environ['EMAIL_MODE']
    
    def test_deteccao_credenciais_reais_linhas_68_76(self, clean_database):
        """Testa linhas 68-76: detecção de credenciais reais"""
        import os
        
        # Salvar valor original
        original_mode = os.environ.get('EMAIL_MODE')
        
        try:
            # Usar modo AUTO para forçar detecção automática
            os.environ['EMAIL_MODE'] = 'AUTO'
            
            # Teste 1: Credenciais reais (linhas 68-76 executadas)
            email_service_real = EmailService(
                email_usuario="usuario.real@gmail.com",
                email_senha="senha_app_muito_longa_16_chars"  # > 10 caracteres
            )
            
            # Deve detectar como produção
            assert email_service_real.modo_producao is True
            
            # Teste 2: Credenciais padrão (não reais)
            email_service_fake = EmailService(
                email_usuario="sistema.leiloes@exemplo.com",  # Padrão
                email_senha="senha_do_sistema"  # Padrão
            )
            
            # Deve detectar como teste
            assert email_service_fake.modo_producao is False
            
            # Teste 3: Senha muito curta
            email_service_curta = EmailService(
                email_usuario="real@gmail.com",
                email_senha="123"  # <= 10 caracteres
            )
            
            # Deve detectar como teste
            assert email_service_curta.modo_producao is False
            
        finally:
            # Restaurar valor original
            if original_mode is not None:
                os.environ['EMAIL_MODE'] = original_mode
            else:
                if 'EMAIL_MODE' in os.environ:
                    del os.environ['EMAIL_MODE']
    
    def test_envio_real_email_vencedor_linhas_103_107(self, clean_database):
        """Testa linhas 103-107: envio real + tratamento de erro"""
        # Criar EmailService em modo produção com credenciais falsas
        email_service = EmailService(
            smtp_server="servidor.inexistente.fake",
            smtp_port=999,
            email_usuario="fake@fake.fake",
            email_senha="senha_fake_muito_longa",
            modo_producao=True  # Forçar modo produção
        )
        
        # Criar objetos fake para teste
        class ParticipanteFake:
            def __init__(self):
                self.nome = "João Teste"
                self.email = "joao@teste.fake"
                self.cpf = "12345678901"
        
        class LeilaoFake:
            def __init__(self):
                self.id = 1
                self.nome = "Leilão Fake"
                self.lance_minimo = 100.0
                self.data_inicio = datetime.now()
                self.data_termino = datetime.now()
        
        participante = ParticipanteFake()
        leilao = LeilaoFake()
        
        # Tentar enviar email (vai falhar por servidor fake)
        # Isso executa linhas 103 e 105-107 (try/except)
        sucesso = email_service.enviar_email_vencedor(leilao, participante, 500.0)
        
        # Deve retornar False devido ao erro
        assert sucesso is False
    
    def test_envio_real_email_personalizado_linhas_137_143(self, clean_database):
        """Testa linhas 137 e 141-143: envio real personalizado + erro"""
        # Criar EmailService em modo produção com credenciais falsas
        email_service = EmailService(
            smtp_server="servidor.fake.inexistente",
            smtp_port=9999,
            email_usuario="fake@test.fake",
            email_senha="senha_fake_longa_suficiente",
            modo_producao=True  # Forçar modo produção
        )
        
        # Tentar enviar email personalizado (vai executar linha 137)
        # E vai dar erro (executa linhas 141-143)
        sucesso = email_service.criar_email_personalizado(
            nome_participante="Teste",
            email_destino="teste@fake.fake",
            assunto="Teste",
            mensagem="Mensagem de teste"
        )
        
        # Deve retornar False devido ao erro
        assert sucesso is False
    
    def test_envio_real_smtp_completo_linhas_244_262(self, clean_database):
        """Testa linhas 244-262: método _enviar_email_real completo"""
        # Este teste vai tentar conectar a um servidor SMTP fake
        # para forçar a execução das linhas, incluindo o tratamento de erro
        
        email_service = EmailService(
            smtp_server="smtp.servidor.fake.inexistente",
            smtp_port=587,
            email_usuario="usuario@fake.com",
            email_senha="senha_fake_longa_para_teste",
            modo_producao=True
        )
        
        # Criar mensagem fake
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        
        msg = MIMEMultipart()
        msg['From'] = "teste@fake.com"
        msg['To'] = "destino@fake.com"
        msg['Subject'] = "Teste"
        msg.attach(MIMEText("Corpo do teste", 'plain'))
        
        # Tentar enviar (vai executar linhas 244-262, incluindo o except)
        sucesso = email_service._enviar_email_real(msg, "destino@fake.com")
        
        # Deve retornar False devido ao erro de conexão
        assert sucesso is False
    
    def test_notificar_vencedores_sem_participante_linhas_287_288(self, clean_database):
        """Testa linhas 287-288: continue quando não encontra participante"""
        # Setup básico
        leilao_service = LeilaoService()
        leilao_service.db_config = clean_database
        
        email_service = EmailService.criar_para_testes()
        
        # Criar leilão finalizado com vencedor inexistente
        session = clean_database.get_session()
        from src.models import Leilao, StatusLeilao
        
        leilao_fake = Leilao(
            nome="Leilão com Vencedor Inexistente",
            lance_minimo=100.0,
            data_inicio=datetime.now() - timedelta(hours=1),
            data_termino=datetime.now() - timedelta(minutes=30),
            status=StatusLeilao.FINALIZADO,
            participante_vencedor_id=99999  # ID inexistente
        )
        
        session.add(leilao_fake)
        session.commit()
        session.refresh(leilao_fake)
        session.close()
        
        # Tentar notificar (vai executar linhas 287-288: session.close() + continue)
        resultado = email_service.notificar_vencedores_pendentes(leilao_service)
        
        # Deve pular o leilão sem vencedor
        assert resultado['emails_enviados'] == 0
        assert resultado['emails_falharam'] == 0
    
    def test_notificar_vencedores_sem_lance_linha_300(self, clean_database):
        """Testa linha 300: continue quando não encontra lance vencedor"""
        # Setup completo
        participante_service = ParticipanteService()
        participante_service.db_config = clean_database
        
        leilao_service = LeilaoService()
        leilao_service.db_config = clean_database
        
        email_service = EmailService.criar_para_testes()
        
        # Criar participante
        participante = participante_service.criar_participante(
            "12345678901", "João", "joao@teste.com", datetime(1990, 1, 1)
        )
        
        # Criar leilão finalizado COM vencedor mas SEM lance
        session = clean_database.get_session()
        from src.models import Leilao, StatusLeilao
        
        leilao_sem_lance = Leilao(
            nome="Leilão Sem Lance",
            lance_minimo=100.0,
            data_inicio=datetime.now() - timedelta(hours=1),
            data_termino=datetime.now() - timedelta(minutes=30),
            status=StatusLeilao.FINALIZADO,
            participante_vencedor_id=participante.id  # Vencedor existe
        )
        
        session.add(leilao_sem_lance)
        session.commit()
        session.close()
        
        # Tentar notificar (vai executar linha 300: continue)
        resultado = email_service.notificar_vencedores_pendentes(leilao_service)
        
        # Deve pular por não ter lance
        assert resultado['emails_enviados'] == 0
        assert resultado['emails_falharam'] == 0
    
    def test_notificar_vencedores_falha_envio_linhas_315_316(self, clean_database):
        """Testa linhas 315-316: incrementa emails_falharam quando envio falha"""
        # Setup completo
        participante_service = ParticipanteService()
        participante_service.db_config = clean_database
        
        leilao_service = LeilaoService()
        leilao_service.db_config = clean_database
        
        lance_service = LanceService()
        lance_service.db_config = clean_database
        
        # Criar EmailService que vai falhar no envio
        email_service = EmailService(
            smtp_server="fake.smtp.server",
            smtp_port=999,
            email_usuario="fake@fake.com",
            email_senha="senha_fake_longa_teste",
            modo_producao=True  # Modo produção para tentar envio real
        )
        
        # Criar cenário completo
        participante = participante_service.criar_participante(
            "12345678901", "João", "joao@teste.com", datetime(1990, 1, 1)
        )
        
        leilao = leilao_service.criar_leilao(
            "Produto Teste", 100.0,
            datetime.now() - timedelta(hours=1),
            datetime.now() + timedelta(minutes=5),
            permitir_passado=True
        )
        
        # Abrir leilão e fazer lance
        leilao_service.atualizar_status_leiloes(enviar_emails=False)
        lance_service.criar_lance(participante.id, leilao.id, 150.0)
        
        # Finalizar leilão
        session = clean_database.get_session()
        from src.models import Leilao
        leilao_db = session.query(Leilao).filter(Leilao.id == leilao.id).first()
        leilao_db.data_termino = datetime.now() - timedelta(minutes=1)
        session.commit()
        session.close()
        
        leilao_service.atualizar_status_leiloes(enviar_emails=False)
        
        # Tentar notificar (vai falhar e executar linhas 315-316)
        resultado = email_service.notificar_vencedores_pendentes(leilao_service)
        
        # Deve ter falhado
        assert resultado['emails_enviados'] == 0
        assert resultado['emails_falharam'] == 1  # ← Linha 315
        assert len(resultado['detalhes']) == 1     # ← Linha 316
        assert resultado['detalhes'][0]['status'] == 'falhou'
    
    def test_notificar_vencedores_erro_geral_linhas_325_327(self, clean_database):
        """Testa linhas 325-327: tratamento de erro geral"""
        # Criar EmailService normal
        email_service = EmailService.criar_para_testes()
        
        # Criar um LeilaoService "quebrado" que vai dar erro
        class LeilaoServiceQuebrado:
            def leiloes_que_precisa_notificar(self):
                # Forçar um erro para executar as linhas 325-327
                raise Exception("Erro simulado para teste")
        
        leilao_service_quebrado = LeilaoServiceQuebrado()
        
        # Tentar notificar (vai dar erro e executar linhas 325-327)
        resultado = email_service.notificar_vencedores_pendentes(leilao_service_quebrado)
        
        # Deve retornar resultado padrão devido ao erro
        assert resultado['emails_enviados'] == 0
        assert resultado['emails_falharam'] == 0
        assert len(resultado['detalhes']) == 0

class TestEmailServiceMetodosConveniencia:
    """Testes para métodos de conveniência (se não estiverem cobertos)"""
    
    def test_criar_para_testes(self, clean_database):
        """Testa método criar_para_testes"""
        email_service = EmailService.criar_para_testes()
        
        assert email_service.modo_teste is True
        assert email_service.modo_producao is False
    
    def test_criar_para_producao(self, clean_database):
        """Testa método criar_para_producao"""
        email_service = EmailService.criar_para_producao()
        
        assert email_service.modo_producao is True
        assert email_service.modo_teste is False
    
    def test_criar_do_env(self, clean_database):
        """Testa método criar_do_env"""
        email_service = EmailService.criar_do_env()
        
        # Deve criar sem erro
        assert email_service is not None
        assert hasattr(email_service, 'modo_producao')
        assert hasattr(email_service, 'modo_teste')

class TestEmailServiceLinhasEspecificas:
    """Testes para cobrir linhas específicas que ainda faltam"""
    
    def test_erro_envio_email_vencedor_linhas_105_107(self, clean_database):
        """
        Força erro no envio_email_vencedor para executar linhas 105-107
        except Exception as e: print(f"❌ Erro...") return False
        """
        # Criar EmailService que vai dar erro 
        email_service = EmailService.criar_para_producao()
        
        # Sobrescrever método interno para forçar erro ANTES do print
        def _criar_mensagem_vencedor_com_erro(self, leilao, participante, valor_lance):
            raise Exception("Erro controlado na criação da mensagem")
        
        import types
        email_service._criar_mensagem_vencedor = types.MethodType(
            _criar_mensagem_vencedor_com_erro, email_service
        )
        
        # Criar objetos NORMAIS (sem propriedades problemáticas)
        class ParticipanteNormal:
            def __init__(self):
                self.nome = "João Silva"
                self.email = "joao@teste.com"  # Normal, não levanta erro
                self.cpf = "12345678901"
        
        class LeilaoNormal:
            def __init__(self):
                self.id = 1
                self.nome = "PlayStation 5"  # Normal, não levanta erro
                self.lance_minimo = 1000.0
                self.data_inicio = datetime.now()
                self.data_termino = datetime.now()
        
        participante = ParticipanteNormal()
        leilao = LeilaoNormal()
        
        # Tentar enviar email - vai dar erro no método _criar_mensagem_vencedor
        # Isso executa as linhas 105-107 SEM dar erro no print
        sucesso = email_service.enviar_email_vencedor(leilao, participante, 1500.0)
        
        # Deve retornar False devido ao erro
        assert sucesso is False
    
    def test_erro_envio_email_personalizado_linhas_141_143(self, clean_database):
        """
        Força erro no criar_email_personalizado para executar linhas 141-143
        except Exception as e: print(f"❌ Erro...") return False
        """
        # Criar EmailService em modo produção
        email_service = EmailService.criar_para_producao()
        
        # Sobrescrever método para forçar erro
        def _enviar_email_real_com_erro(self, mensagem, email_destino):
            raise Exception("Erro controlado no envio real")
        
        import types
        email_service._enviar_email_real = types.MethodType(_enviar_email_real_com_erro, email_service)
        
        # Tentar enviar email personalizado
        # Vai dar erro e executar linhas 141-143
        sucesso = email_service.criar_email_personalizado(
            nome_participante="João",
            email_destino="joao@teste.com",
            assunto="Teste",
            mensagem="Mensagem teste"
        )
        
        # Deve retornar False por causa do erro
        assert sucesso is False
    
    def test_smtp_real_sucesso_linhas_250_258(self, clean_database):
        """
        Simula envio SMTP real bem-sucedido para executar linhas 250-258
        """
        import smtplib
        from unittest.mock import patch, MagicMock
        
        # Criar EmailService em modo produção
        email_service = EmailService(
            smtp_server="smtp.gmail.com",
            smtp_port=587,
            email_usuario="teste@gmail.com",
            email_senha="senha_teste_app",
            modo_producao=True
        )
        
        # Mock do servidor SMTP para simular sucesso
        mock_server = MagicMock()
        
        # Configurar o mock para simular comportamento normal
        mock_server.__enter__.return_value = mock_server
        mock_server.__exit__.return_value = None
        mock_server.starttls.return_value = None
        mock_server.login.return_value = None
        mock_server.sendmail.return_value = {}  # Sucesso
        
        # Criar mensagem de teste
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        
        msg = MIMEMultipart()
        msg['From'] = "teste@gmail.com"
        msg['To'] = "destino@teste.com"
        msg['Subject'] = "Teste de Envio Real"
        msg.attach(MIMEText("Corpo do email de teste", 'plain'))
        
        # Usar patch para substituir smtplib.SMTP pelo mock
        with patch('smtplib.SMTP', return_value=mock_server):
            # Chamar método que vai executar linhas 250-258
            sucesso = email_service._enviar_email_real(msg, "destino@teste.com")
            
            # Deve retornar True (sucesso)
            assert sucesso is True
            
            # Verificar que métodos foram chamados (execução das linhas)
            mock_server.starttls.assert_called_once()  # Linha 250
            mock_server.login.assert_called_once_with("teste@gmail.com", "senha_teste_app")  # Linha 251
            mock_server.sendmail.assert_called_once()  # Linha 255
    
    def test_smtp_real_diferentes_tipos_erro(self, clean_database):
        """
        Testa diferentes tipos de erro SMTP para cobertura completa - versão simples
        """
        from unittest.mock import patch, MagicMock
    
        email_service = EmailService(
            smtp_server="smtp.gmail.com",
            smtp_port=587,
            email_usuario="teste@gmail.com",
            email_senha="senha_teste",
            modo_producao=True
        )
    
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
    
        msg = MIMEMultipart()
        msg['From'] = "teste@gmail.com"
        msg['To'] = "destino@teste.com"
        msg['Subject'] = "Teste"
        msg.attach(MIMEText("Teste", 'plain'))
    
        # Teste 1: Erro na criação da conexão SMTP
        with patch('smtplib.SMTP', side_effect=Exception("Erro de conexão")):
            sucesso = email_service._enviar_email_real(msg, "destino@teste.com")
            assert sucesso is False
    
        # Teste 2: Erro no starttls
        mock_server = MagicMock()
        mock_server.__enter__.return_value = mock_server
        mock_server.__exit__.return_value = None
        mock_server.starttls.side_effect = Exception("Erro no STARTTLS")
    
        with patch('smtplib.SMTP', return_value=mock_server):
            sucesso = email_service._enviar_email_real(msg, "destino@teste.com")
            assert sucesso is False
            mock_server.starttls.assert_called_once()
    
        # Teste 3: Erro no login
        mock_server2 = MagicMock()
        mock_server2.__enter__.return_value = mock_server2
        mock_server2.__exit__.return_value = None
        mock_server2.starttls.return_value = None
        mock_server2.login.side_effect = Exception("Erro de autenticação")
    
        with patch('smtplib.SMTP', return_value=mock_server2):
            sucesso = email_service._enviar_email_real(msg, "destino@teste.com")
            assert sucesso is False
            mock_server2.login.assert_called_once()
    
        # Teste 4: Erro no sendmail
        mock_server3 = MagicMock()
        mock_server3.__enter__.return_value = mock_server3
        mock_server3.__exit__.return_value = None
        mock_server3.starttls.return_value = None
        mock_server3.login.return_value = None
        mock_server3.sendmail.side_effect = Exception("Erro no envio")
    
        with patch('smtplib.SMTP', return_value=mock_server3):
            sucesso = email_service._enviar_email_real(msg, "destino@teste.com")
            assert sucesso is False
            mock_server3.sendmail.assert_called_once()

    def test_cobertura_completa_envio_vencedor_modo_producao(self, clean_database):
        """
        Teste integrado para cobrir fluxo completo em modo produção
        """
        import smtplib
        from unittest.mock import patch, MagicMock
        
        # Criar objetos reais do sistema
        participante_service = ParticipanteService()
        participante_service.db_config = clean_database
        
        leilao_service = LeilaoService()
        leilao_service.db_config = clean_database
        
        # Criar participante e leilão reais
        participante = participante_service.criar_participante(
            "12345678901", "João Silva", "joao@teste.com", datetime(1990, 1, 1)
        )
        
        leilao = leilao_service.criar_leilao(
            "PlayStation 5 Teste", 1000.0,
            datetime.now() - timedelta(hours=1),
            datetime.now() - timedelta(minutes=30),
            permitir_passado=True
        )
        
        # Criar EmailService em modo produção com mock SMTP
        email_service = EmailService(
            smtp_server="smtp.gmail.com",
            smtp_port=587,
            email_usuario="teste@gmail.com",
            email_senha="senha_app_teste",
            modo_producao=True
        )
        
        # Mock do SMTP que simula sucesso
        mock_server = MagicMock()
        mock_server.__enter__.return_value = mock_server
        mock_server.__exit__.return_value = None
        mock_server.starttls.return_value = None
        mock_server.login.return_value = None
        mock_server.sendmail.return_value = {}
        
        # Testar envio de vencedor com sucesso
        with patch('smtplib.SMTP', return_value=mock_server):
            sucesso = email_service.enviar_email_vencedor(leilao, participante, 1500.0)
            
            # Deve ter sucesso
            assert sucesso is True
            
            # Verificar que SMTP foi usado corretamente
            mock_server.starttls.assert_called_once()
            mock_server.login.assert_called_once()
            mock_server.sendmail.assert_called_once()
    
    def test_cobertura_completa_email_personalizado_modo_producao(self, clean_database):
        """
        Teste integrado para email personalizado em modo produção
        """
        import smtplib
        from unittest.mock import patch, MagicMock
        
        # Criar EmailService em modo produção
        email_service = EmailService(
            smtp_server="smtp.gmail.com",
            smtp_port=587,
            email_usuario="teste@gmail.com",
            email_senha="senha_app_teste",
            modo_producao=True
        )
        
        # Mock do SMTP que simula sucesso
        mock_server = MagicMock()
        mock_server.__enter__.return_value = mock_server
        mock_server.__exit__.return_value = None
        mock_server.starttls.return_value = None
        mock_server.login.return_value = None
        mock_server.sendmail.return_value = {}
        
        # Testar email personalizado com sucesso
        with patch('smtplib.SMTP', return_value=mock_server):
            sucesso = email_service.criar_email_personalizado(
                nome_participante="Maria Santos",
                email_destino="maria@teste.com",
                assunto="🎉 Email de Teste",
                mensagem="Esta é uma mensagem de teste do sistema!"
            )
            
            # Deve ter sucesso
            assert sucesso is True
            
            # Verificar que SMTP foi usado corretamente  
            mock_server.starttls.assert_called_once()
            mock_server.login.assert_called_once()
            mock_server.sendmail.assert_called_once()

