import pytest
from datetime import datetime, timedelta
from src.models import StatusLeilao, Lance
from src.services.lance_service import LanceService
from src.services.participante_service import ParticipanteService
from src.services.leilao_service import LeilaoService
from src.utils.validators import ValidationError

class TestIntegracaoLanceCompleta:
    """
    Testes de integração que simulam cenários completos do sistema de lances
    """
    
    def test_leilao_completo_com_multiplos_lances(self, clean_database):
        """
        Teste de integração: Leilão completo desde criação até finalização
        """
        # Setup dos serviços
        participante_service = ParticipanteService()
        participante_service.db_config = clean_database
        
        leilao_service = LeilaoService()
        leilao_service.db_config = clean_database
        
        lance_service = LanceService()
        lance_service.db_config = clean_database
        
        # 1. Criar participantes
        participantes = []
        for i in range(4):
            p = participante_service.criar_participante(
                f"1234567890{i}",
                f"Participante {i+1}",
                f"p{i+1}@teste.com",
                datetime(1990 + i, 1, 1)
            )
            participantes.append(p)
        
        # 2. Criar leilão
        leilao = leilao_service.criar_leilao(
            nome="Xbox Series X",
            lance_minimo=800.0,
            data_inicio=datetime.now() - timedelta(minutes=30),
            data_termino=datetime.now() + timedelta(minutes=30),
            permitir_passado=True
        )
        
        # 3. Abrir leilão
        leilao_service.atualizar_status_leiloes()
        leilao = leilao_service.obter_leilao_por_id(leilao.id)
        assert leilao.status == StatusLeilao.ABERTO
        
        # 4. Sequência de lances respeitando todas as regras
        lances_dados = []
        
        # Participante 1: 850 (acima do mínimo 800)
        lance1 = lance_service.criar_lance(participantes[0].id, leilao.id, 850.0)
        lances_dados.append(lance1)
        
        # Participante 2: 900 (acima do anterior 850)
        lance2 = lance_service.criar_lance(participantes[1].id, leilao.id, 900.0)
        lances_dados.append(lance2)
        
        # Participante 3: 950
        lance3 = lance_service.criar_lance(participantes[2].id, leilao.id, 950.0)
        lances_dados.append(lance3)
        
        # Participante 1 volta: 1000 (não pode ser consecutivo com ele mesmo)
        lance4 = lance_service.criar_lance(participantes[0].id, leilao.id, 1000.0)
        lances_dados.append(lance4)
        
        # Participante 4 entra: 1100
        lance5 = lance_service.criar_lance(participantes[3].id, leilao.id, 1100.0)
        lances_dados.append(lance5)
        
        # Participante 2 final: 1200 (vencedor)
        lance6 = lance_service.criar_lance(participantes[1].id, leilao.id, 1200.0)
        lances_dados.append(lance6)
        
        # 5. Verificar estatísticas durante o leilão
        stats = lance_service.obter_estatisticas_lances_leilao(leilao.id)
        assert stats['total_lances'] == 6
        assert stats['participantes_unicos'] == 4
        assert stats['maior_lance'] == 1200.0
        assert stats['menor_lance'] == 850.0
        assert stats['lance_atual'] == 1200.0
        
        # 6. Verificar ranking
        ranking = lance_service.obter_ranking_participantes_leilao(leilao.id)
        assert len(ranking) == 4
        assert ranking[0]['participante_nome'] == "Participante 2"  # Vencedor
        assert ranking[0]['maior_lance'] == 1200.0
        
        # 7. Finalizar leilão (simular passagem do tempo)
        session = clean_database.get_session()
        leilao_db = session.query(type(leilao)).filter(type(leilao).id == leilao.id).first()
        leilao_db.data_termino = datetime.now() - timedelta(minutes=1)  # Já terminou
        session.commit()
        session.close()
        
        # 8. Atualizar status (deve finalizar)
        leilao_service.atualizar_status_leiloes()
        leilao_final = leilao_service.obter_leilao_por_id(leilao.id)
        
        assert leilao_final.status == StatusLeilao.FINALIZADO
        assert leilao_final.participante_vencedor_id == participantes[1].id  # Participante 2
    
    def test_regras_validacao_lances_sequenciais(self, clean_database):
        """
        Teste de integração: Validação de todas as regras de lances sequenciais
        """
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
        
        # Criar leilão aberto
        leilao = leilao_service.criar_leilao(
            "Produto Teste", 500.0,
            datetime.now() - timedelta(minutes=10),
            datetime.now() + timedelta(hours=1),
            permitir_passado=True
        )
        
        leilao_service.atualizar_status_leiloes()
        
        # REGRA: Lance deve ser >= lance mínimo
        # REGRA: Lance deve ser >= lance mínimo
        with pytest.raises(ValidationError, match="Lance deve ser pelo menos R\\$ 500.00"):
            lance_service.criar_lance(p1.id, leilao.id, 400.0)
        
        # João dá lance válido
        lance1 = lance_service.criar_lance(p1.id, leilao.id, 600.0)
        
        # REGRA: Mesmo participante não pode dar lance consecutivo
        with pytest.raises(ValidationError, match="O mesmo participante não pode efetuar dois lances consecutivos"):
            lance_service.criar_lance(p1.id, leilao.id, 700.0)
        
        # REGRA: Lance deve ser maior que o último
        with pytest.raises(ValidationError, match="Lance deve ser maior que R\\$ 600.00"):
            lance_service.criar_lance(p2.id, leilao.id, 600.0)  # Igual
        
        with pytest.raises(ValidationError, match="Lance deve ser maior que R\\$ 600.00"):
            lance_service.criar_lance(p2.id, leilao.id, 550.0)  # Menor
        
        # Maria dá lance válido
        lance2 = lance_service.criar_lance(p2.id, leilao.id, 700.0)
        
        # Agora João pode dar lance novamente (não é mais consecutivo)
        lance3 = lance_service.criar_lance(p1.id, leilao.id, 800.0)
        
        # Verificar sequência correta
        lances = lance_service.obter_lances_leilao(leilao.id, ordem_crescente=False)
        assert len(lances) == 3
        assert lances[0].valor == 800.0  # Último (maior)
        assert lances[1].valor == 700.0
        assert lances[2].valor == 600.0  # Primeiro (menor)
    
    def test_simulacao_lances_antes_criacao(self, clean_database):
        """
        Teste de integração: Usar simulação para testar lances antes de criar
        """
        # Setup
        participante_service = ParticipanteService()
        participante_service.db_config = clean_database
        
        leilao_service = LeilaoService()
        leilao_service.db_config = clean_database
        
        lance_service = LanceService()
        lance_service.db_config = clean_database
        
        # Criar cenário
        p1 = participante_service.criar_participante(
            "12345678901", "João", "joao@teste.com", datetime(1990, 1, 1)
        )
        
        p2 = participante_service.criar_participante(
            "10987654321", "Maria", "maria@teste.com", datetime(1985, 5, 15)
        )
        
        leilao = leilao_service.criar_leilao(
            "Produto Simulação", 300.0,
            datetime.now() - timedelta(minutes=10),
            datetime.now() + timedelta(hours=1),
            permitir_passado=True
        )
        
        leilao_service.atualizar_status_leiloes()
        
        # Simular primeiro lance
        sim1 = lance_service.simular_lance(p1.id, leilao.id, 350.0)
        assert sim1['valido'] is True
        assert sim1['valor_minimo_aceito'] == 300.0
        
        # Criar o lance simulado
        lance_service.criar_lance(p1.id, leilao.id, 350.0)
        
        # Simular lance consecutivo (deve falhar)
        sim2 = lance_service.simular_lance(p1.id, leilao.id, 400.0)
        assert sim2['valido'] is False
        assert "último a dar lance" in sim2['motivo']
        
        # Simular lance de Maria (deve ser válido)
        sim3 = lance_service.simular_lance(p2.id, leilao.id, 400.0)
        assert sim3['valido'] is True
        assert sim3['valor_minimo_aceito'] == 350.01
        assert sim3['ultimo_lance']['valor'] == 350.0
        
        # Simular lance insuficiente de Maria
        sim4 = lance_service.simular_lance(p2.id, leilao.id, 350.0)
        assert sim4['valido'] is False
        assert "Lance deve ser pelo menos" in sim4['motivo']
    
    def test_historico_completo_leilao(self, clean_database):
        """
        Teste de integração: Histórico completo de um leilão com múltiplos participantes
        """
        # Setup
        participante_service = ParticipanteService()
        participante_service.db_config = clean_database
        
        leilao_service = LeilaoService()
        leilao_service.db_config = clean_database
        
        lance_service = LanceService()
        lance_service.db_config = clean_database
        
        # Criar participantes com nomes distintivos
        p1 = participante_service.criar_participante(
            "12345678901", "Ana Silva", "ana@teste.com", datetime(1990, 1, 1)
        )
        
        p2 = participante_service.criar_participante(
            "10987654321", "Bruno Santos", "bruno@teste.com", datetime(1985, 5, 15)
        )
        
        p3 = participante_service.criar_participante(
            "11122233344", "Carlos Oliveira", "carlos@teste.com", datetime(1992, 10, 20)
        )
        
        # Criar leilão
        leilao = leilao_service.criar_leilao(
            "Smartphone Premium", 1200.0,
            datetime.now() - timedelta(minutes=15),
            datetime.now() + timedelta(hours=2),
            permitir_passado=True
        )
        
        leilao_service.atualizar_status_leiloes()
        
        # Criar sequência de lances com intervalos
        import time
        
        lance_service.criar_lance(p1.id, leilao.id, 1300.0)  # Ana
        time.sleep(0.1)  # Pequeno intervalo para datas diferentes
        
        lance_service.criar_lance(p2.id, leilao.id, 1400.0)  # Bruno
        time.sleep(0.1)
        
        lance_service.criar_lance(p3.id, leilao.id, 1500.0)  # Carlos
        time.sleep(0.1)
        
        lance_service.criar_lance(p1.id, leilao.id, 1600.0)  # Ana volta
        time.sleep(0.1)
        
        lance_service.criar_lance(p2.id, leilao.id, 1800.0)  # Bruno final
        
        # Verificar histórico cronológico
        historico = lance_service.obter_historico_lances_leilao(leilao.id)
        
        assert len(historico) == 5
        
        # Verificar ordem cronológica (primeiro lance primeiro)
        assert historico[0]['participante_nome'] == "Ana Silva"
        assert historico[0]['valor'] == 1300.0
        
        assert historico[1]['participante_nome'] == "Bruno Santos"
        assert historico[1]['valor'] == 1400.0
        
        assert historico[2]['participante_nome'] == "Carlos Oliveira"
        assert historico[2]['valor'] == 1500.0
        
        assert historico[3]['participante_nome'] == "Ana Silva"
        assert historico[3]['valor'] == 1600.0
        
        assert historico[4]['participante_nome'] == "Bruno Santos"
        assert historico[4]['valor'] == 1800.0
        
        # Verificar que as datas estão em ordem crescente
        for i in range(1, len(historico)):
            assert historico[i]['data_lance'] > historico[i-1]['data_lance']
        
        # Verificar estatísticas finais
        stats = lance_service.obter_estatisticas_lances_leilao(leilao.id)
        assert stats['total_lances'] == 5
        assert stats['participantes_unicos'] == 3
        assert stats['maior_lance'] == 1800.0
        assert stats['menor_lance'] == 1300.0
        assert stats['incremento_total'] == 600.0  # 1800 - 1200
        
        # Verificar ranking final
        ranking = lance_service.obter_ranking_participantes_leilao(leilao.id)
        
        # Bruno deve estar em 1º (lance de 1800)
        assert ranking[0]['participante_nome'] == "Bruno Santos"
        assert ranking[0]['maior_lance'] == 1800.0
        assert ranking[0]['total_lances'] == 2
        assert ranking[0]['vencedor'] is True
        
        # Ana deve estar em 2º (lance de 1600)
        assert ranking[1]['participante_nome'] == "Ana Silva"
        assert ranking[1]['maior_lance'] == 1600.0
        assert ranking[1]['total_lances'] == 2
        assert ranking[1]['vencedor'] is False
        
        # Carlos deve estar em 3º (lance de 1500)
        assert ranking[2]['participante_nome'] == "Carlos Oliveira"
        assert ranking[2]['maior_lance'] == 1500.0
        assert ranking[2]['total_lances'] == 1
        assert ranking[2]['vencedor'] is False
    
    def test_leilao_sem_lances_expira(self, clean_database):
        """
        Teste de integração: Leilão sem lances deve expirar
        """
        # Setup
        leilao_service = LeilaoService()
        leilao_service.db_config = clean_database
        
        lance_service = LanceService()
        lance_service.db_config = clean_database
        
        # Criar leilão que vai expirar
        leilao = leilao_service.criar_leilao(
            "Produto Sem Interesse", 2000.0,
            datetime.now() - timedelta(hours=1),
            datetime.now() - timedelta(minutes=10),  # Já terminou
            permitir_passado=True
        )
        
        # Atualizar status (deve ir direto para EXPIRADO)
        leilao_service.atualizar_status_leiloes()
        leilao_final = leilao_service.obter_leilao_por_id(leilao.id)
        
        assert leilao_final.status == StatusLeilao.EXPIRADO
        assert leilao_final.participante_vencedor_id is None
        
        # Verificar estatísticas de leilão expirado
        stats = lance_service.obter_estatisticas_lances_leilao(leilao.id)
        assert stats['total_lances'] == 0
        assert stats['maior_lance'] is None
        assert stats['lance_atual'] == 2000.0  # Lance mínimo
        
        # Ranking deve estar vazio
        ranking = lance_service.obter_ranking_participantes_leilao(leilao.id)
        assert len(ranking) == 0
    
    def test_integracao_completa_multiplos_leiloes(self, clean_database):
        """
        Teste de integração: Múltiplos leilões simultâneos com mesmos participantes
        """
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
        
        # Criar múltiplos leilões abertos
        leilao1 = leilao_service.criar_leilao(
            "Leilão A", 100.0,
            datetime.now() - timedelta(minutes=30),
            datetime.now() + timedelta(hours=1),
            permitir_passado=True
        )
        
        leilao2 = leilao_service.criar_leilao(
            "Leilão B", 200.0,
            datetime.now() - timedelta(minutes=20),
            datetime.now() + timedelta(hours=2),
            permitir_passado=True
        )
        
        # Abrir leilões
        leilao_service.atualizar_status_leiloes()
        
        # João participa dos dois leilões
        lance_service.criar_lance(p1.id, leilao1.id, 150.0)  # Leilão A
        lance_service.criar_lance(p1.id, leilao2.id, 250.0)  # Leilão B
        
        # Maria participa dos dois leilões
        lance_service.criar_lance(p2.id, leilao1.id, 200.0)  # Leilão A
        lance_service.criar_lance(p2.id, leilao2.id, 300.0)  # Leilão B
        
        # João dá lances finais
        lance_service.criar_lance(p1.id, leilao1.id, 250.0)  # Vence A
        lance_service.criar_lance(p1.id, leilao2.id, 350.0)  # Vence B
        
        # Verificar estatísticas individuais
        stats1 = lance_service.obter_estatisticas_lances_leilao(leilao1.id)
        stats2 = lance_service.obter_estatisticas_lances_leilao(leilao2.id)
        
        assert stats1['maior_lance'] == 250.0
        assert stats2['maior_lance'] == 350.0
        
        # Verificar rankings
        ranking1 = lance_service.obter_ranking_participantes_leilao(leilao1.id)
        ranking2 = lance_service.obter_ranking_participantes_leilao(leilao2.id)
        
        # João deve vencer ambos
        assert ranking1[0]['participante_nome'] == "João"
        assert ranking2[0]['participante_nome'] == "João"
        
        # Verificar lances de cada participante
        lances_joao_A = lance_service.obter_lances_participante(p1.id, leilao1.id)
        lances_joao_B = lance_service.obter_lances_participante(p1.id, leilao2.id)
        
        assert len(lances_joao_A) == 2  # 150, 250
        assert len(lances_joao_B) == 2  # 250, 350
        
        # Verificar todos os lances de João
        todos_lances_joao = lance_service.obter_lances_participante(p1.id)
        assert len(todos_lances_joao) == 4  # 2 de cada leilão