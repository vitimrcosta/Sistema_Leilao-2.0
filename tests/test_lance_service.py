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
    
    def test_obter_lances_leilao_inexistente(self, clean_database):
        """Teste: Obter lances de leilão inexistente"""
        lance_service = LanceService()
        lance_service.db_config = clean_database
        
        with pytest.raises(ValidationError, match="Leilão com ID 99999 não encontrado"):
            lance_service.obter_lances_leilao(99999)
    
    def test_obter_lances_participante_inexistente(self, clean_database):
        """Teste: Obter lances de participante inexistente"""
        lance_service = LanceService()
        lance_service.db_config = clean_database
        
        with pytest.raises(ValidationError, match="Participante com ID 99999 não encontrado"):
            lance_service.obter_lances_participante(99999)