import pytest
from datetime import datetime, timedelta
from src.models import Lance, Leilao, Participante, StatusLeilao
from src.services.lance_service import LanceService
from src.services.participante_service import ParticipanteService
from src.services.leilao_service import LeilaoService
from src.utils.validators import ValidationError

class TestLanceService:
    """Testes para o LanceService"""
    
    def test_criar_lance_valido(self, clean_database):
        """Teste: Criar lance válido em leilão aberto"""
        # Setup
        participante_service = ParticipanteService()
        participante_service.db_config = clean_database
        
        leilao_service = LeilaoService()
        leilao_service.db_config = clean_database
        
        lance_service = LanceService()
        lance_service.db_config = clean_database
        
        # Criar participante
        participante = participante_service.criar_participante(
            "12345678901", "João Silva", "joao@teste.com", datetime(1990, 1, 1)
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
        assert leilao.status == StatusLeilao.ABERTO
        
        # Criar lance
        lance = lance_service.criar_lance(participante.id, leilao.id, 1100.0)
        
        assert lance is not None
        assert lance.id is not None
        assert lance.valor == 1100.0
        assert lance.participante_id == participante.id
        assert lance.leilao_id == leilao.id
        assert lance.data_lance is not None
    
    def test_criar_lance_participante_inexistente(self, clean_database):
        """Teste: Tentar criar lance com participante inexistente"""
        lance_service = LanceService()
        lance_service.db_config = clean_database
        
        with pytest.raises(ValidationError, match="Participante com ID 99999 não encontrado"):
            lance_service.criar_lance(99999, 1, 100.0)
    
    def test_criar_lance_leilao_inexistente(self, clean_database):
        """Teste: Tentar criar lance com leilão inexistente"""
        participante_service = ParticipanteService()
        participante_service.db_config = clean_database
        
        lance_service = LanceService()
        lance_service.db_config = clean_database
        
        # Criar participante
        participante = participante_service.criar_participante(
            "12345678901", "João Silva", "joao@teste.com", datetime(1990, 1, 1)
        )
        
        with pytest.raises(ValidationError, match="Leilão com ID 99999 não encontrado"):
            lance_service.criar_lance(participante.id, 99999, 100.0)
    
    def test_criar_lance_leilao_nao_aberto(self, clean_database):
        """Teste: Tentar criar lance em leilão não aberto"""
        participante_service = ParticipanteService()
        participante_service.db_config = clean_database
        
        leilao_service = LeilaoService()
        leilao_service.db_config = clean_database
        
        lance_service = LanceService()
        lance_service.db_config = clean_database
        
        # Criar participante
        participante = participante_service.criar_participante(
            "12345678901", "João Silva", "joao@teste.com", datetime(1990, 1, 1)
        )
        
        # Criar leilão INATIVO
        leilao = leilao_service.criar_leilao(
            "PlayStation 5", 1000.0,
            datetime.now() + timedelta(hours=1),
            datetime.now() + timedelta(days=1)
        )
        
        with pytest.raises(ValidationError, match="Lances só podem ser realizados em leilões ABERTOS"):
            lance_service.criar_lance(participante.id, leilao.id, 1100.0)
    
    def test_criar_lance_menor_que_minimo(self, clean_database):
        """Teste: Tentar criar lance menor que o mínimo"""
        participante_service = ParticipanteService()
        participante_service.db_config = clean_database
        
        leilao_service = LeilaoService()
        leilao_service.db_config = clean_database
        
        lance_service = LanceService()
        lance_service.db_config = clean_database
        
        # Setup
        participante = participante_service.criar_participante(
            "12345678901", "João Silva", "joao@teste.com", datetime(1990, 1, 1)
        )
        
        leilao = leilao_service.criar_leilao(
            "PlayStation 5", 1000.0,
            datetime.now() - timedelta(minutes=30),
            datetime.now() + timedelta(hours=1),
            permitir_passado=True
        )
        
        leilao_service.atualizar_status_leiloes()
        
        # Tentar lance menor que o mínimo
        with pytest.raises(ValidationError, match="Lance deve ser pelo menos R\\$ 1000.00"):
            lance_service.criar_lance(participante.id, leilao.id, 900.0)
    
    def test_criar_lance_menor_que_ultimo(self, clean_database):
        """Teste: Tentar criar lance menor ou igual ao último lance"""
        participante_service = ParticipanteService()
        participante_service.db_config = clean_database
        
        leilao_service = LeilaoService()
        leilao_service.db_config = clean_database
        
        lance_service = LanceService()
        lance_service.db_config = clean_database
        
        # Setup
        p1 = participante_service.criar_participante(
            "12345678901", "João", "joao@teste.com", datetime(1990, 1, 1)
        )
        
        p2 = participante_service.criar_participante(
            "10987654321", "Maria", "maria@teste.com", datetime(1985, 5, 15)
        )
        
        leilao = leilao_service.criar_leilao(
            "PlayStation 5", 1000.0,
            datetime.now() - timedelta(minutes=30),
            datetime.now() + timedelta(hours=1),
            permitir_passado=True
        )
        
        leilao_service.atualizar_status_leiloes()
        
        # João dá primeiro lance
        lance_service.criar_lance(p1.id, leilao.id, 1100.0)
        
        # Maria tenta lance igual (deve falhar)
        with pytest.raises(ValidationError, match="Lance deve ser maior que R\\$ 1100.00"):
            lance_service.criar_lance(p2.id, leilao.id, 1100.0)
        
        # Maria tenta lance menor (deve falhar)
        with pytest.raises(ValidationError, match="Lance deve ser maior que R\\$ 1100.00"):
            lance_service.criar_lance(p2.id, leilao.id, 1050.0)
    
    def test_mesmo_participante_lances_consecutivos(self, clean_database):
        """Teste: Mesmo participante não pode dar dois lances consecutivos"""
        participante_service = ParticipanteService()
        participante_service.db_config = clean_database
        
        leilao_service = LeilaoService()
        leilao_service.db_config = clean_database
        
        lance_service = LanceService()
        lance_service.db_config = clean_database
        
        # Setup
        participante = participante_service.criar_participante(
            "12345678901", "João", "joao@teste.com", datetime(1990, 1, 1)
        )
        
        leilao = leilao_service.criar_leilao(
            "PlayStation 5", 1000.0,
            datetime.now() - timedelta(minutes=30),
            datetime.now() + timedelta(hours=1),
            permitir_passado=True
        )
        
        leilao_service.atualizar_status_leiloes()
        
        # João dá primeiro lance
        lance_service.criar_lance(participante.id, leilao.id, 1100.0)
        
        # João tenta dar segundo lance consecutivo (deve falhar)
        with pytest.raises(ValidationError, match="O mesmo participante não pode efetuar dois lances consecutivos"):
            lance_service.criar_lance(participante.id, leilao.id, 1200.0)
    
    def test_lances_alternados_entre_participantes(self, clean_database):
        """Teste: Lances alternados entre participantes devem funcionar"""
        participante_service = ParticipanteService()
        participante_service.db_config = clean_database
        
        leilao_service = LeilaoService()
        leilao_service.db_config = clean_database
        
        lance_service = LanceService()
        lance_service.db_config = clean_database
        
        # Setup
        p1 = participante_service.criar_participante(
            "12345678901", "João", "joao@teste.com", datetime(1990, 1, 1)
        )
        
        p2 = participante_service.criar_participante(
            "10987654321", "Maria", "maria@teste.com", datetime(1985, 5, 15)
        )
        
        p3 = participante_service.criar_participante(
            "11122233344", "Pedro", "pedro@teste.com", datetime(1992, 10, 20)
        )
        
        leilao = leilao_service.criar_leilao(
            "PlayStation 5", 1000.0,
            datetime.now() - timedelta(minutes=30),
            datetime.now() + timedelta(hours=1),
            permitir_passado=True
        )
        
        leilao_service.atualizar_status_leiloes()
        
        # Sequência de lances alternados
        lance1 = lance_service.criar_lance(p1.id, leilao.id, 1100.0)  # João
        lance2 = lance_service.criar_lance(p2.id, leilao.id, 1200.0)  # Maria
        lance3 = lance_service.criar_lance(p3.id, leilao.id, 1300.0)  # Pedro
        lance4 = lance_service.criar_lance(p1.id, leilao.id, 1400.0)  # João novamente (OK)
        
        assert lance1.valor == 1100.0
        assert lance2.valor == 1200.0
        assert lance3.valor == 1300.0
        assert lance4.valor == 1400.0
    
    def test_obter_lances_leilao_ordem_crescente(self, clean_database):
        """Teste: Obter lances em ordem crescente de valor"""
        participante_service = ParticipanteService()
        participante_service.db_config = clean_database
        
        leilao_service = LeilaoService()
        leilao_service.db_config = clean_database
        
        lance_service = LanceService()
        lance_service.db_config = clean_database
        
        # Setup com múltiplos lances
        p1 = participante_service.criar_participante(
            "12345678901", "João", "joao@teste.com", datetime(1990, 1, 1)
        )
        
        p2 = participante_service.criar_participante(
            "10987654321", "Maria", "maria@teste.com", datetime(1985, 5, 15)
        )
        
        leilao = leilao_service.criar_leilao(
            "PlayStation 5", 1000.0,
            datetime.now() - timedelta(minutes=30),
            datetime.now() + timedelta(hours=1),
            permitir_passado=True
        )
        
        leilao_service.atualizar_status_leiloes()
        
        # Criar lances em ordem não crescente
        lance_service.criar_lance(p1.id, leilao.id, 1300.0)  # João - 1300
        lance_service.criar_lance(p2.id, leilao.id, 1400.0)  # Maria - 1400
        lance_service.criar_lance(p1.id, leilao.id, 1500.0)  # João - 1500
        
        # Obter lances em ordem crescente
        lances_crescente = lance_service.obter_lances_leilao(leilao.id, ordem_crescente=True)
        
        assert len(lances_crescente) == 3
        assert lances_crescente[0].valor == 1300.0
        assert lances_crescente[1].valor == 1400.0
        assert lances_crescente[2].valor == 1500.0
        
        # Obter lances em ordem decrescente
        lances_decrescente = lance_service.obter_lances_leilao(leilao.id, ordem_crescente=False)
        
        assert len(lances_decrescente) == 3
        assert lances_decrescente[0].valor == 1500.0
        assert lances_decrescente[1].valor == 1400.0
        assert lances_decrescente[2].valor == 1300.0
    
    def test_obter_lances_leilao_inexistente(self, clean_database):
        """Teste: Obter lances de leilão inexistente - COBRE LINHA 121"""
        lance_service = LanceService()
        lance_service.db_config = clean_database
        
        # ESTE TESTE DEVE COBRIR A LINHA 121:
        # leilao = session.query(Leilao).filter(Leilao.id == leilao_id).first()
        # if not leilao:                                                    <- linha antes do raise
        #     raise ValidationError(f"Leilão com ID {leilao_id} não encontrado")  <- LINHA 121
        
        with pytest.raises(ValidationError, match="Leilão com ID 99999 não encontrado"):
            lance_service.obter_lances_leilao(99999)
    
    def test_obter_maior_menor_lance(self, clean_database):
        """Teste: Obter maior e menor lance de um leilão"""
        participante_service = ParticipanteService()
        participante_service.db_config = clean_database
        
        leilao_service = LeilaoService()
        leilao_service.db_config = clean_database
        
        lance_service = LanceService()
        lance_service.db_config = clean_database
        
        # Setup
        p1 = participante_service.criar_participante(
            "12345678901", "João", "joao@teste.com", datetime(1990, 1, 1)
        )
        
        p2 = participante_service.criar_participante(
            "10987654321", "Maria", "maria@teste.com", datetime(1985, 5, 15)
        )
        
        leilao = leilao_service.criar_leilao(
            "PlayStation 5", 1000.0,
            datetime.now() - timedelta(minutes=30),
            datetime.now() + timedelta(hours=1),
            permitir_passado=True
        )
        
        leilao_service.atualizar_status_leiloes()
        
        # Teste sem lances
        stats_sem_lances = lance_service.obter_maior_menor_lance(leilao.id)
        assert stats_sem_lances['maior_lance'] is None
        assert stats_sem_lances['menor_lance'] is None
        assert stats_sem_lances['lance_atual'] == 1000.0  # Lance mínimo
        assert stats_sem_lances['total_lances'] == 0
        
        # Criar lances
        lance_service.criar_lance(p1.id, leilao.id, 1100.0)
        lance_service.criar_lance(p2.id, leilao.id, 1300.0)
        lance_service.criar_lance(p1.id, leilao.id, 1500.0)
        
        # Teste com lances
        stats_com_lances = lance_service.obter_maior_menor_lance(leilao.id)
        assert stats_com_lances['maior_lance'] == 1500.0
        assert stats_com_lances['menor_lance'] == 1100.0
        assert stats_com_lances['lance_atual'] == 1500.0
        assert stats_com_lances['total_lances'] == 3
    
    def test_verificar_pode_dar_lance(self, clean_database):
        """Teste: Verificar se participante pode dar lance"""
        participante_service = ParticipanteService()
        participante_service.db_config = clean_database
        
        leilao_service = LeilaoService()
        leilao_service.db_config = clean_database
        
        lance_service = LanceService()
        lance_service.db_config = clean_database
        
        # Setup
        p1 = participante_service.criar_participante(
            "12345678901", "João", "joao@teste.com", datetime(1990, 1, 1)
        )
        
        p2 = participante_service.criar_participante(
            "10987654321", "Maria", "maria@teste.com", datetime(1985, 5, 15)
        )
        
        leilao = leilao_service.criar_leilao(
            "PlayStation 5", 1000.0,
            datetime.now() - timedelta(minutes=30),
            datetime.now() + timedelta(hours=1),
            permitir_passado=True
        )
        
        leilao_service.atualizar_status_leiloes()
        
        # João pode dar lance (primeiro lance)
        pode, motivo = lance_service.verificar_pode_dar_lance(p1.id, leilao.id)
        assert pode is True
        assert "Pode dar lance" in motivo
        
        # João dá lance
        lance_service.criar_lance(p1.id, leilao.id, 1100.0)
        
        # João NÃO pode dar lance novamente (foi o último)
        pode, motivo = lance_service.verificar_pode_dar_lance(p1.id, leilao.id)
        assert pode is False
        assert "último a dar lance" in motivo
        
        # Maria pode dar lance
        pode, motivo = lance_service.verificar_pode_dar_lance(p2.id, leilao.id)
        assert pode is True
        assert "Pode dar lance" in motivo
    
    def test_obter_valor_minimo_proximo_lance(self, clean_database):
        """Teste: Obter valor mínimo para próximo lance"""
        participante_service = ParticipanteService()
        participante_service.db_config = clean_database
        
        leilao_service = LeilaoService()
        leilao_service.db_config = clean_database
        
        lance_service = LanceService()
        lance_service.db_config = clean_database
        
        # Setup
        participante = participante_service.criar_participante(
            "12345678901", "João", "joao@teste.com", datetime(1990, 1, 1)
        )
        
        leilao = leilao_service.criar_leilao(
            "PlayStation 5", 1000.0,
            datetime.now() - timedelta(minutes=30),
            datetime.now() + timedelta(hours=1),
            permitir_passado=True
        )
        
        leilao_service.atualizar_status_leiloes()
        
        # Sem lances - deve retornar lance mínimo
        valor_min = lance_service.obter_valor_minimo_proximo_lance(leilao.id)
        assert valor_min == 1000.0
        
        # Com lance - deve retornar último lance + 0.01
        lance_service.criar_lance(participante.id, leilao.id, 1200.0)
        valor_min = lance_service.obter_valor_minimo_proximo_lance(leilao.id)
        assert valor_min == 1200.01
    
    def test_obter_historico_lances_leilao(self, clean_database):
        """Teste: Obter histórico completo de lances com dados do participante"""
        participante_service = ParticipanteService()
        participante_service.db_config = clean_database
        
        leilao_service = LeilaoService()
        leilao_service.db_config = clean_database
        
        lance_service = LanceService()
        lance_service.db_config = clean_database
        
        # Setup
        p1 = participante_service.criar_participante(
            "12345678901", "João Silva", "joao@teste.com", datetime(1990, 1, 1)
        )
        
        p2 = participante_service.criar_participante(
            "10987654321", "Maria Santos", "maria@teste.com", datetime(1985, 5, 15)
        )
        
        leilao = leilao_service.criar_leilao(
            "PlayStation 5", 1000.0,
            datetime.now() - timedelta(minutes=30),
            datetime.now() + timedelta(hours=1),
            permitir_passado=True
        )
        
        leilao_service.atualizar_status_leiloes()
        
        # Criar lances
        lance_service.criar_lance(p1.id, leilao.id, 1100.0)
        lance_service.criar_lance(p2.id, leilao.id, 1200.0)
        
        # Obter histórico
        historico = lance_service.obter_historico_lances_leilao(leilao.id)
        
        assert len(historico) == 2
        
        # Primeiro lance (João)
        assert historico[0]['valor'] == 1100.0
        assert historico[0]['participante_nome'] == "João Silva"
        assert historico[0]['participante_cpf'] == "12345678901"
        
        # Segundo lance (Maria)
        assert historico[1]['valor'] == 1200.0
        assert historico[1]['participante_nome'] == "Maria Santos"
        assert historico[1]['participante_cpf'] == "10987654321"
    
    def test_obter_estatisticas_lances_leilao(self, clean_database):
        """Teste: Obter estatísticas detalhadas dos lances"""
        participante_service = ParticipanteService()
        participante_service.db_config = clean_database
        
        leilao_service = LeilaoService()
        leilao_service.db_config = clean_database
        
        lance_service = LanceService()
        lance_service.db_config = clean_database
        
        # Setup
        p1 = participante_service.criar_participante(
            "12345678901", "João", "joao@teste.com", datetime(1990, 1, 1)
        )
        
        p2 = participante_service.criar_participante(
            "10987654321", "Maria", "maria@teste.com", datetime(1985, 5, 15)
        )
        
        leilao = leilao_service.criar_leilao(
            "PlayStation 5", 1000.0,
            datetime.now() - timedelta(minutes=30),
            datetime.now() + timedelta(hours=1),
            permitir_passado=True
        )
        
        leilao_service.atualizar_status_leiloes()
        
        # Criar lances: 1100, 1200, 1500
        lance_service.criar_lance(p1.id, leilao.id, 1100.0)
        lance_service.criar_lance(p2.id, leilao.id, 1200.0)
        lance_service.criar_lance(p1.id, leilao.id, 1500.0)
        
        # Obter estatísticas
        stats = lance_service.obter_estatisticas_lances_leilao(leilao.id)
        
        assert stats['total_lances'] == 3
        assert stats['participantes_unicos'] == 2
        assert stats['maior_lance'] == 1500.0
        assert stats['menor_lance'] == 1100.0
        assert stats['lance_medio'] == (1100 + 1200 + 1500) / 3
        assert stats['lance_atual'] == 1500.0
        assert stats['incremento_total'] == 500.0  # 1500 - 1000
    
    def test_obter_ranking_participantes_leilao(self, clean_database):
        """Teste: Obter ranking dos participantes por maior lance"""
        participante_service = ParticipanteService()
        participante_service.db_config = clean_database
        
        leilao_service = LeilaoService()
        leilao_service.db_config = clean_database
        
        lance_service = LanceService()
        lance_service.db_config = clean_database
        
        # Setup
        p1 = participante_service.criar_participante(
            "12345678901", "João", "joao@teste.com", datetime(1990, 1, 1)
        )
        
        p2 = participante_service.criar_participante(
            "10987654321", "Maria", "maria@teste.com", datetime(1985, 5, 15)
        )
        
        p3 = participante_service.criar_participante(
            "11122233344", "Pedro", "pedro@teste.com", datetime(1992, 10, 20)
        )
        
        leilao = leilao_service.criar_leilao(
            "PlayStation 5", 1000.0,
            datetime.now() - timedelta(minutes=30),
            datetime.now() + timedelta(hours=1),
            permitir_passado=True
        )
        
        leilao_service.atualizar_status_leiloes()
        
        # Criar lances com diferentes valores máximos
        lance_service.criar_lance(p1.id, leilao.id, 1100.0)  # João: maior = 1300
        lance_service.criar_lance(p2.id, leilao.id, 1200.0)  # Maria: maior = 1500  
        lance_service.criar_lance(p3.id, leilao.id, 1250.0)  # Pedro: maior = 1250
        lance_service.criar_lance(p1.id, leilao.id, 1300.0)  # João: maior = 1300
        lance_service.criar_lance(p2.id, leilao.id, 1500.0)  # Maria: maior = 1500
        
        # Obter ranking
        ranking = lance_service.obter_ranking_participantes_leilao(leilao.id)
        
        assert len(ranking) == 3
        
        # 1º lugar: Maria (1500)
        assert ranking[0]['posicao'] == 1
        assert ranking[0]['participante_nome'] == "Maria"
        assert ranking[0]['maior_lance'] == 1500.0
        assert ranking[0]['total_lances'] == 2
        assert ranking[0]['vencedor'] is True
        
        # 2º lugar: João (1300)
        assert ranking[1]['posicao'] == 2
        assert ranking[1]['participante_nome'] == "João"
        assert ranking[1]['maior_lance'] == 1300.0
        assert ranking[1]['total_lances'] == 2
        assert ranking[1]['vencedor'] is False
        
        # 3º lugar: Pedro (1250)
        assert ranking[2]['posicao'] == 3
        assert ranking[2]['participante_nome'] == "Pedro"
        assert ranking[2]['maior_lance'] == 1250.0
        assert ranking[2]['total_lances'] == 1
        assert ranking[2]['vencedor'] is False
    
    def test_simular_lance(self, clean_database):
        """Teste: Simular lance sem criar no banco"""
        participante_service = ParticipanteService()
        participante_service.db_config = clean_database
        
        leilao_service = LeilaoService()
        leilao_service.db_config = clean_database
        
        lance_service = LanceService()
        lance_service.db_config = clean_database
        
        # Setup
        p1 = participante_service.criar_participante(
            "12345678901", "João", "joao@teste.com", datetime(1990, 1, 1)
        )
        
        p2 = participante_service.criar_participante(
            "10987654321", "Maria", "maria@teste.com", datetime(1985, 5, 15)
        )
        
        leilao = leilao_service.criar_leilao(
            "PlayStation 5", 1000.0,
            datetime.now() - timedelta(minutes=30),
            datetime.now() + timedelta(hours=1),
            permitir_passado=True
        )
        
        leilao_service.atualizar_status_leiloes()
        
        # Simular primeiro lance válido
        sim1 = lance_service.simular_lance(p1.id, leilao.id, 1100.0)
        assert sim1['valido'] is True
        assert sim1['valor_minimo_aceito'] == 1000.0
        assert sim1['ultimo_lance'] is None
        
        # João dá lance real
        lance_service.criar_lance(p1.id, leilao.id, 1100.0)
        
        # Simular lance de João novamente (deve falhar - consecutivo)
        sim2 = lance_service.simular_lance(p1.id, leilao.id, 1200.0)
        assert sim2['valido'] is False
        assert "último a dar lance" in sim2['motivo']
        
        # Simular lance de Maria válido
        sim3 = lance_service.simular_lance(p2.id, leilao.id, 1200.0)
        assert sim3['valido'] is True
        assert sim3['valor_minimo_aceito'] == 1100.01
        assert sim3['ultimo_lance']['valor'] == 1100.0
        
        # Simular lance de Maria insuficiente
        sim4 = lance_service.simular_lance(p2.id, leilao.id, 1050.0)
        assert sim4['valido'] is False
        assert "Lance deve ser pelo menos" in sim4['motivo']

class TestLanceServiceValidacoes:
    """Testes específicos para validações do LanceService"""
    
    def test_valor_lance_invalido(self, clean_database):
        """Teste: Validação de valor de lance inválido"""
        lance_service = LanceService()
        lance_service.db_config = clean_database
        
        # Valor negativo
        with pytest.raises(ValidationError, match="Valor do lance deve ser maior que zero"):
            lance_service.criar_lance(1, 1, -100.0)
        
        # Valor zero
        with pytest.raises(ValidationError, match="Valor do lance deve ser maior que zero"):
            lance_service.criar_lance(1, 1, 0.0)
        
        # Valor None
        with pytest.raises(ValidationError, match="Valor do lance é obrigatório"):
            lance_service.criar_lance(1, 1, None)

class TestLanceServiceCobertura:
    """Testes específicos para cobrir linhas não testadas do LanceService"""
    
    def test_obter_lance_por_id_existente_e_inexistente(self, clean_database):
        """
        Testa método obter_lance_por_id com lance existente e inexistente
        """
        # Setup
        participante_service = ParticipanteService()
        participante_service.db_config = clean_database
        
        leilao_service = LeilaoService()
        leilao_service.db_config = clean_database
        
        lance_service = LanceService()
        lance_service.db_config = clean_database
        
        # Criar participante e leilão
        participante = participante_service.criar_participante(
            "12345678901", "João", "joao@teste.com", datetime(1990, 1, 1)
        )
        
        leilao = leilao_service.criar_leilao(
            "Produto Teste", 100.0,
            datetime.now() - timedelta(minutes=30),
            datetime.now() + timedelta(hours=1),
            permitir_passado=True
        )
        
        # Abrir leilão e criar lance
        leilao_service.atualizar_status_leiloes()
        lance = lance_service.criar_lance(participante.id, leilao.id, 150.0)
        
        # Teste: obter lance por ID existente
        lance_encontrado = lance_service.obter_lance_por_id(lance.id)
        assert lance_encontrado is not None
        assert lance_encontrado.id == lance.id
        assert lance_encontrado.valor == 150.0
        
        # Teste: obter lance por ID inexistente
        lance_inexistente = lance_service.obter_lance_por_id(99999)
        assert lance_inexistente is None
    
    def test_verificar_pode_dar_lance_participante_inexistente(self, clean_database):
        """
        Testa verificar_pode_dar_lance com participante inexistente
        """
        lance_service = LanceService()
        lance_service.db_config = clean_database
        
        # Tentar verificar com participante inexistente
        pode, motivo = lance_service.verificar_pode_dar_lance(99999, 1)
        
        assert pode is False
        assert motivo == "Participante não encontrado"
    
    def test_verificar_pode_dar_lance_leilao_inexistente(self, clean_database):
        """
        Testa verificar_pode_dar_lance com leilão inexistente
        """
        # Setup
        participante_service = ParticipanteService()
        participante_service.db_config = clean_database
        
        lance_service = LanceService()
        lance_service.db_config = clean_database
        
        # Criar participante
        participante = participante_service.criar_participante(
            "12345678901", "João", "joao@teste.com", datetime(1990, 1, 1)
        )
        
        # Tentar verificar com leilão inexistente
        pode, motivo = lance_service.verificar_pode_dar_lance(participante.id, 99999)
        
        assert pode is False
        assert motivo == "Leilão não encontrado"
    
    def test_verificar_pode_dar_lance_leilao_nao_aberto(self, clean_database):
        """
        Testa verificar_pode_dar_lance com leilão não aberto
        """
        # Setup
        participante_service = ParticipanteService()
        participante_service.db_config = clean_database
        
        leilao_service = LeilaoService()
        leilao_service.db_config = clean_database
        
        lance_service = LanceService()
        lance_service.db_config = clean_database
        
        # Criar participante e leilão INATIVO
        participante = participante_service.criar_participante(
            "12345678901", "João", "joao@teste.com", datetime(1990, 1, 1)
        )
        
        leilao = leilao_service.criar_leilao(
            "Produto Teste", 100.0,
            datetime.now() + timedelta(hours=1),  # Futuro - fica INATIVO
            datetime.now() + timedelta(days=1)
        )
        
        # Verificar lance em leilão INATIVO
        pode, motivo = lance_service.verificar_pode_dar_lance(participante.id, leilao.id)
        
        assert pode is False
        assert "não está aberto" in motivo
        assert "INATIVO" in motivo
    
    def test_obter_valor_minimo_proximo_lance_leilao_inexistente(self, clean_database):
        """
        Testa obter_valor_minimo_proximo_lance com leilão inexistente
        """
        lance_service = LanceService()
        lance_service.db_config = clean_database
        
        # Tentar obter valor mínimo de leilão inexistente
        with pytest.raises(ValidationError, match="Leilão com ID 99999 não encontrado"):
            lance_service.obter_valor_minimo_proximo_lance(99999)
    
    def test_obter_historico_lances_leilao_inexistente(self, clean_database):
        """
        Testa obter_historico_lances_leilao com leilão inexistente
        """
        lance_service = LanceService()
        lance_service.db_config = clean_database
        
        # Tentar obter histórico de leilão inexistente
        with pytest.raises(ValidationError, match="Leilão com ID 99999 não encontrado"):
            lance_service.obter_historico_lances_leilao(99999)
    
    def test_obter_estatisticas_lances_leilao_inexistente(self, clean_database):
        """
        Testa obter_estatisticas_lances_leilao com leilão inexistente
        """
        lance_service = LanceService()
        lance_service.db_config = clean_database
        
        # Tentar obter estatísticas de leilão inexistente
        with pytest.raises(ValidationError, match="Leilão com ID 99999 não encontrado"):
            lance_service.obter_estatisticas_lances_leilao(99999)
    
    def test_obter_ranking_participantes_leilao_inexistente(self, clean_database):
        """
        Testa obter_ranking_participantes_leilao com leilão inexistente
        """
        lance_service = LanceService()
        lance_service.db_config = clean_database
        
        # Tentar obter ranking de leilão inexistente
        with pytest.raises(ValidationError, match="Leilão com ID 99999 não encontrado"):
            lance_service.obter_ranking_participantes_leilao(99999)
    
    def test_simular_lance_valor_invalido(self, clean_database):
        """
        Testa simular_lance com valor inválido
        """
        lance_service = LanceService()
        lance_service.db_config = clean_database
        
        # Tentar simular lance com valor inválido (negativo)
        resultado = lance_service.simular_lance(1, 1, -100.0)
        
        assert resultado['valido'] is False
        assert "Valor do lance deve ser maior que zero" in resultado['motivo']
    
    def test_simular_lance_participante_inexistente(self, clean_database):
        """
        Testa simular_lance com participante inexistente
        """
        lance_service = LanceService()
        lance_service.db_config = clean_database
        
        # Tentar simular lance com participante inexistente
        resultado = lance_service.simular_lance(99999, 1, 100.0)
        
        assert resultado['valido'] is False
        assert resultado['motivo'] == "Participante não encontrado"
    
    def test_simular_lance_leilao_inexistente(self, clean_database):
        """
        Testa simular_lance com leilão inexistente
        """
        # Setup
        participante_service = ParticipanteService()
        participante_service.db_config = clean_database
        
        lance_service = LanceService()
        lance_service.db_config = clean_database
        
        # Criar participante
        participante = participante_service.criar_participante(
            "12345678901", "João", "joao@teste.com", datetime(1990, 1, 1)
        )
        
        # Simular lance com leilão inexistente
        resultado = lance_service.simular_lance(participante.id, 99999, 100.0)
        
        assert resultado['valido'] is False
        assert resultado['motivo'] == "Leilão não encontrado"
    
    def test_simular_lance_leilao_nao_aberto(self, clean_database):
        """
        Testa simular_lance com leilão não aberto
        """
        # Setup
        participante_service = ParticipanteService()
        participante_service.db_config = clean_database
        
        leilao_service = LeilaoService()
        leilao_service.db_config = clean_database
        
        lance_service = LanceService()
        lance_service.db_config = clean_database
        
        # Criar participante e leilão INATIVO
        participante = participante_service.criar_participante(
            "12345678901", "João", "joao@teste.com", datetime(1990, 1, 1)
        )
        
        leilao = leilao_service.criar_leilao(
            "Produto Teste", 100.0,
            datetime.now() + timedelta(hours=1),  # Futuro - fica INATIVO
            datetime.now() + timedelta(days=1)
        )
        
        # Simular lance em leilão não aberto
        resultado = lance_service.simular_lance(participante.id, leilao.id, 150.0)
        
        assert resultado['valido'] is False
        assert "não está aberto" in resultado['motivo']
        assert "INATIVO" in resultado['motivo']
    
    def test_simular_lance_com_historico_participante(self, clean_database):
        """
        Testa simular_lance quando participante já fez lance
        """
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
        
        # Criar leilão aberto
        leilao = leilao_service.criar_leilao(
            "Produto Teste", 100.0,
            datetime.now() - timedelta(minutes=30),
            datetime.now() + timedelta(hours=1),
            permitir_passado=True
        )
        
        leilao_service.atualizar_status_leiloes()
        
        # João faz primeiro lance
        lance_service.criar_lance(p1.id, leilao.id, 150.0)
        
        # Maria faz segundo lance
        lance_service.criar_lance(p2.id, leilao.id, 200.0)
        
        # Simular novo lance do João (deve incluir seu último lance)
        resultado = lance_service.simular_lance(p1.id, leilao.id, 250.0)
        
        assert resultado['valido'] is True
        assert resultado['seu_ultimo_lance'] is not None
        assert resultado['seu_ultimo_lance']['valor'] == 150.0
        assert 'data' in resultado['seu_ultimo_lance']
    
    def test_simular_lance_participante_sem_lance_anterior(self, clean_database):
        """
        Testa simular_lance quando participante nunca fez lance
        """
        # Setup
        participante_service = ParticipanteService()
        participante_service.db_config = clean_database
        
        leilao_service = LeilaoService()
        leilao_service.db_config = clean_database
        
        lance_service = LanceService()
        lance_service.db_config = clean_database
        
        # Criar participante e leilão aberto
        participante = participante_service.criar_participante(
            "12345678901", "João", "joao@teste.com", datetime(1990, 1, 1)
        )
        
        leilao = leilao_service.criar_leilao(
            "Produto Teste", 100.0,
            datetime.now() - timedelta(minutes=30),
            datetime.now() + timedelta(hours=1),
            permitir_passado=True
        )
        
        leilao_service.atualizar_status_leiloes()
        
        # Simular lance de participante que nunca fez lance
        resultado = lance_service.simular_lance(participante.id, leilao.id, 150.0)
        
        assert resultado['valido'] is True
        assert resultado['seu_ultimo_lance'] is None

class TestLanceServiceCasosEspeciais:
    """Testes para casos especiais que podem não estar cobertos"""
    
    def test_obter_lances_participante_inexistente(self, clean_database):
        """
        Testa obter_lances_participante com participante inexistente
        """
        lance_service = LanceService()
        lance_service.db_config = clean_database
        
        # Deve dar ValidationError
        with pytest.raises(ValidationError, match="Participante com ID 99999 não encontrado"):
            lance_service.obter_lances_participante(99999)
    
    def test_obter_lances_participante_com_leilao_especifico(self, clean_database):
        """
        Testa obter_lances_participante filtrado por leilão específico
        """
        # Setup completo
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
        
        # Criar dois leilões
        leilao1 = leilao_service.criar_leilao(
            "Leilão 1", 100.0,
            datetime.now() - timedelta(minutes=30),
            datetime.now() + timedelta(hours=1),
            permitir_passado=True
        )
        
        leilao2 = leilao_service.criar_leilao(
            "Leilão 2", 200.0,
            datetime.now() - timedelta(minutes=30),
            datetime.now() + timedelta(hours=1),
            permitir_passado=True
        )
        
        leilao_service.atualizar_status_leiloes()
        
        # Fazer lances em ambos leilões
        lance_service.criar_lance(participante.id, leilao1.id, 150.0)
        lance_service.criar_lance(participante.id, leilao2.id, 250.0)
        
        # Obter lances apenas do leilão 1
        lances_leilao1 = lance_service.obter_lances_participante(participante.id, leilao1.id)
        assert len(lances_leilao1) == 1
        assert lances_leilao1[0].valor == 150.0
        
        # Obter todos os lances do participante
        todos_lances = lance_service.obter_lances_participante(participante.id)
        assert len(todos_lances) == 2
    
    def test_cobertura_completa_obter_maior_menor_lance(self, clean_database):
        """
        Testa obter_maior_menor_lance em cenários diferentes
        """
        # Setup
        participante_service = ParticipanteService()
        participante_service.db_config = clean_database
        
        leilao_service = LeilaoService()
        leilao_service.db_config = clean_database
        
        lance_service = LanceService()
        lance_service.db_config = clean_database
        
        # Criar leilão
        leilao = leilao_service.criar_leilao(
            "Produto Teste", 500.0,
            datetime.now() - timedelta(minutes=30),
            datetime.now() + timedelta(hours=1),
            permitir_passado=True
        )
        
        # Teste 1: Leilão sem lances
        stats_vazio = lance_service.obter_maior_menor_lance(leilao.id)
        assert stats_vazio['maior_lance'] is None
        assert stats_vazio['menor_lance'] is None
        assert stats_vazio['lance_atual'] == 500.0  # Lance mínimo
        assert stats_vazio['total_lances'] == 0
        
        # Teste 2: Leilão com lances
        leilao_service.atualizar_status_leiloes()
        
        # Criar participantes e lances
        p1 = participante_service.criar_participante(
            "12345678901", "João", "joao@teste.com", datetime(1990, 1, 1)
        )
        
        p2 = participante_service.criar_participante(
            "10987654321", "Maria", "maria@teste.com", datetime(1985, 5, 15)
        )
        
        # CORRIGIDO: Sequência crescente de lances
        lance_service.criar_lance(p1.id, leilao.id, 600.0)  # João: 600
        lance_service.criar_lance(p2.id, leilao.id, 700.0)  # Maria: 700 (maior que 600)
        lance_service.criar_lance(p1.id, leilao.id, 800.0)  # João: 800 (maior que 700)
        
        stats_com_lances = lance_service.obter_maior_menor_lance(leilao.id)
        assert stats_com_lances['maior_lance'] == 800.0
        assert stats_com_lances['menor_lance'] == 600.0
        assert stats_com_lances['lance_atual'] == 800.0
        assert stats_com_lances['total_lances'] == 3

class TestLanceServiceLinha121:

    def test_linha_121_exata(self, clean_database):
        """Teste ultra-específico para cobrir exatamente a linha 121"""
        service = LanceService()
        service.db_config = clean_database
        
        # ID que não existe
        non_existent_id = 99999
        
        # Verificar se a mensagem de erro é exatamente a mesma
        with pytest.raises(ValidationError) as excinfo:
            service.obter_lances_leilao(non_existent_id)
        
        # Verificação exata da mensagem
        assert str(excinfo.value) == f"Leilão com ID {non_existent_id} não encontrado"


    """Teste específico para cobrir a linha 121 do lance_service.py"""
    
    def test_obter_lances_leilao_inexistente_linha121(self, clean_database):
        """
        Teste específico para cobrir EXATAMENTE a linha 121:
        raise ValidationError(f"Leilão com ID {leilao_id} não encontrado")
        
        Esta linha está no método obter_lances_leilao quando leilao é None
        """
        lance_service = LanceService()
        lance_service.db_config = clean_database
        
        # Tentar obter lances de um leilão que não existe
        # Isso deve executar EXATAMENTE a linha 121 do lance_service.py
        with pytest.raises(ValidationError, match="Leilão com ID 99999 não encontrado"):
            lance_service.obter_lances_leilao(99999)
    
    def test_obter_lances_leilao_diferentes_ordens(self, clean_database):
        """
        Teste adicional para garantir cobertura completa do método obter_lances_leilao
        Testa tanto ordem crescente quanto decrescente para cobrir todas as linhas
        """
        from src.services.participante_service import ParticipanteService
        from src.services.leilao_service import LeilaoService
        
        # Setup
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
        
        # Criar leilão
        leilao = leilao_service.criar_leilao(
            "Teste Linha 121", 100.0,
            datetime.now() - timedelta(minutes=30),
            datetime.now() + timedelta(hours=1),
            permitir_passado=True
        )
        
        leilao_service.atualizar_status_leiloes()
        
        # CORRIGIDO: Criar lances em sequência VÁLIDA e crescente
        lance_service.criar_lance(p1.id, leilao.id, 150.0)  # João: 150
        lance_service.criar_lance(p2.id, leilao.id, 200.0)  # Maria: 200 (maior que 150)
        lance_service.criar_lance(p1.id, leilao.id, 250.0)  # João: 250 (maior que 200)
        
        # Testar ordem crescente (True) - padrão
        lances_crescente = lance_service.obter_lances_leilao(leilao.id, ordem_crescente=True)
        assert len(lances_crescente) == 3
        
        # Testar ordem decrescente (False)
        lances_decrescente = lance_service.obter_lances_leilao(leilao.id, ordem_crescente=False)
        assert len(lances_decrescente) == 3
        
        # Verificar que as ordens são realmente diferentes
        assert lances_crescente[0].valor <= lances_crescente[1].valor <= lances_crescente[2].valor  # Crescente
        assert lances_decrescente[0].valor >= lances_decrescente[1].valor >= lances_decrescente[2].valor  # Decrescente
        
class TestLanceServiceCoberturaAdicional:
    """Testes adicionais para garantir cobertura completa"""
    
    def test_criar_lance_sequencia_valida_completa(self, clean_database):
        """
        Teste para garantir cobertura completa do método criar_lance
        com uma sequência válida e completa de lances
        """
        from src.services.participante_service import ParticipanteService
        from src.services.leilao_service import LeilaoService
        
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
        
        # Criar leilão
        leilao = leilao_service.criar_leilao(
            "Cobertura Completa", 100.0,
            datetime.now() - timedelta(minutes=30),
            datetime.now() + timedelta(hours=1),
            permitir_passado=True
        )
        
        leilao_service.atualizar_status_leiloes()
        
        # Sequência completa de lances válidos
        # 1. Primeiro lance (sem último lance anterior)
        lance1 = lance_service.criar_lance(p1.id, leilao.id, 150.0)
        assert lance1.valor == 150.0
        assert lance1.participante_id == p1.id
        
        # 2. Segundo lance (participante diferente, valor maior)
        lance2 = lance_service.criar_lance(p2.id, leilao.id, 200.0)
        assert lance2.valor == 200.0
        assert lance2.participante_id == p2.id
        
        # 3. Terceiro lance (primeiro participante novamente, valor maior)
        lance3 = lance_service.criar_lance(p1.id, leilao.id, 250.0)
        assert lance3.valor == 250.0
        assert lance3.participante_id == p1.id
        
        # Verificar que todos os lances foram salvos
        todos_lances = lance_service.obter_lances_leilao(leilao.id)
        assert len(todos_lances) == 3
    
    def test_todas_validacoes_criar_lance(self, clean_database):
        """
        Teste para cobrir todas as validações do método criar_lance
        """
        from src.services.participante_service import ParticipanteService
        from src.services.leilao_service import LeilaoService
        
        # Setup
        participante_service = ParticipanteService()
        participante_service.db_config = clean_database
        
        leilao_service = LeilaoService()
        leilao_service.db_config = clean_database
        
        lance_service = LanceService()
        lance_service.db_config = clean_database
        
        # 1. Teste: Valor inválido (já testado, mas para completude)
        with pytest.raises(ValidationError, match="Valor do lance deve ser maior que zero"):
            lance_service.criar_lance(1, 1, -50.0)
        
        # 2. Teste: Participante inexistente (já testado)
        with pytest.raises(ValidationError, match="Participante com ID 99999 não encontrado"):
            lance_service.criar_lance(99999, 1, 100.0)
        
        # Criar participante para próximos testes
        participante = participante_service.criar_participante(
            "12345678901", "João", "joao@teste.com", datetime(1990, 1, 1)
        )
        
        # 3. Teste: Leilão inexistente
        with pytest.raises(ValidationError, match="Leilão com ID 99999 não encontrado"):
            lance_service.criar_lance(participante.id, 99999, 100.0)
        
        # Criar leilão INATIVO para próximos testes
        leilao_inativo = leilao_service.criar_leilao(
            "Leilão Inativo", 100.0,
            datetime.now() + timedelta(hours=1),  # Futuro - fica INATIVO
            datetime.now() + timedelta(days=1)
        )
        
        # 4. Teste: Leilão não aberto
        with pytest.raises(ValidationError, match="Lances só podem ser realizados em leilões ABERTOS"):
            lance_service.criar_lance(participante.id, leilao_inativo.id, 150.0)
        
        # Criar leilão aberto para próximos testes
        leilao_aberto = leilao_service.criar_leilao(
            "Leilão Aberto", 200.0,
            datetime.now() - timedelta(minutes=30),
            datetime.now() + timedelta(hours=1),
            permitir_passado=True
        )
        
        leilao_service.atualizar_status_leiloes()
        
        # 5. Teste: Lance menor que mínimo
        with pytest.raises(ValidationError, match="Lance deve ser pelo menos R\\$ 200.00"):
            lance_service.criar_lance(participante.id, leilao_aberto.id, 150.0)
        
        # Fazer um lance válido
        lance_service.criar_lance(participante.id, leilao_aberto.id, 250.0)
        
        # 6. Teste: Lance menor ou igual ao último
        with pytest.raises(ValidationError, match="Lance deve ser maior que R\\$ 250.00"):
            lance_service.criar_lance(participante.id, leilao_aberto.id, 250.0)  # Igual
        
        with pytest.raises(ValidationError, match="Lance deve ser maior que R\\$ 250.00"):
            lance_service.criar_lance(participante.id, leilao_aberto.id, 200.0)  # Menor
        
        # 7. Teste: Mesmo participante consecutivo
        with pytest.raises(ValidationError, match="O mesmo participante não pode efetuar dois lances consecutivos"):
            lance_service.criar_lance(participante.id, leilao_aberto.id, 300.0)
        
        print("✅ Todas as validações do criar_lance foram testadas!")

# Teste adicional para verificar especificamente a linha 121
class TestEspecificoLinha121:
    """Classe focada APENAS na linha 121"""
    
    def test_linha_121_obter_lances_leilao_inexistente(self, clean_database):
        """
        Teste ultra-específico para a linha 121 do lance_service.py
        
        Linha 121: raise ValidationError(f"Leilão com ID {leilao_id} não encontrado")
        
        Esta linha está no método obter_lances_leilao, dentro do bloco:
        if not leilao:
            raise ValidationError(f"Leilão com ID {leilao_id} não encontrado")  # <- LINHA 121
        """
        lance_service = LanceService()
        lance_service.db_config = clean_database
        
        # Este comando deve executar EXATAMENTE a linha 121
        with pytest.raises(ValidationError) as exc_info:
            lance_service.obter_lances_leilao(12345)  # Leilão inexistente
        
        # Verificar a mensagem exata
        assert "Leilão com ID 12345 não encontrado" in str(exc_info.value)
        
        # Tentar com outro ID para garantir que a linha é sempre executada
        with pytest.raises(ValidationError) as exc_info2:
            lance_service.obter_lances_leilao(99999)
        
        assert "Leilão com ID 99999 não encontrado" in str(exc_info2.value)        