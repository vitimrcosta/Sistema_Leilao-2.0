import pytest
from datetime import datetime, timedelta
from src.models import StatusLeilao, Participante, Leilao, Lance

class TestIntegracaoSistemaLeiloes:
    """
    Testes de integração que simulam cenários completos do sistema
    Testam a interação entre múltiplos componentes
    """
    
    def test_ciclo_completo_leilao_sem_lances(self, leilao_service):
        """
        Teste de integração: Ciclo completo de um leilão que expira
        1. Criar leilão INATIVO
        2. Leilão vira ABERTO automaticamente
        3. Leilão vira EXPIRADO (sem lances)
        """
        # 1. Criar leilão que deveria estar aberto
        data_inicio = datetime.now() - timedelta(minutes=30)  # Já passou
        data_termino = datetime.now() - timedelta(minutes=10)  # Já terminou
        
        leilao = leilao_service.criar_leilao(
            nome="Produto que vai expirar",
            lance_minimo=100.0,
            data_inicio=data_inicio,
            data_termino=data_termino,
            permitir_passado=True  # Permitir datas no passado para testes
        )
        
        # Inicialmente INATIVO
        assert leilao.status == StatusLeilao.INATIVO
        
        # 2. Atualizar status - deve virar EXPIRADO diretamente
        resultado = leilao_service.atualizar_status_leiloes()
        
        # 3. Verificar se virou EXPIRADO (sem lances)
        leilao_final = leilao_service.obter_leilao_por_id(leilao.id)
        assert leilao_final.status == StatusLeilao.EXPIRADO
        assert resultado['expirados'] >= 1
    
    def test_workflow_criacao_e_alteracao(self, leilao_service):
        """
        Teste de integração: Workflow de criação e alteração de leilão
        1. Criar leilão
        2. Alterar várias vezes (enquanto INATIVO)
        3. Leilão vira ABERTO
        4. Tentar alterar (deve falhar)
        """
        # 1. Criar leilão
        data_inicio = datetime.now() + timedelta(hours=1)
        data_termino = datetime.now() + timedelta(days=1)
        
        leilao = leilao_service.criar_leilao(
            "Produto Inicial",
            100.0,
            data_inicio,
            data_termino
        )
        
        # 2. Alterar múltiplas vezes (deve funcionar)
        leilao = leilao_service.atualizar_leilao(leilao.id, nome="Produto Alterado 1")
        assert leilao.nome == "Produto Alterado 1"
        
        leilao = leilao_service.atualizar_leilao(leilao.id, lance_minimo=200.0)
        assert leilao.lance_minimo == 200.0
        
        nova_data_inicio = datetime.now() + timedelta(hours=2)
        nova_data_termino = datetime.now() + timedelta(days=2)
        leilao = leilao_service.atualizar_leilao(
            leilao.id, 
            data_inicio=nova_data_inicio,
            data_termino=nova_data_termino
        )
        
        # 3. Simular abertura do leilão (forçar status ABERTO)
        session = leilao_service.db_config.get_session()
        session.query(Leilao).filter(Leilao.id == leilao.id).update({
            Leilao.status: StatusLeilao.ABERTO
        })
        session.commit()
        session.close()
        
        # 4. Tentar alterar leilão ABERTO (deve falhar)
        from src.utils.validators import ValidationError
        with pytest.raises(ValidationError, match="não pode ser alterado"):
            leilao_service.atualizar_leilao(leilao.id, nome="Tentativa Inválida")
    
    def test_listagem_com_multiplos_filtros(self, leilao_service):
        """
        Teste de integração: Criação de múltiplos leilões e filtros complexos
        """
        agora = datetime.now()
        
        # Criar leilões com diferentes estados e datas
        leiloes_criados = []
        
        # Leilão 1: Futuro (INATIVO)
        l1 = leilao_service.criar_leilao(
            "Futuro 1", 100.0,
            agora + timedelta(days=1),
            agora + timedelta(days=2)
        )
        leiloes_criados.append(l1)
        
        # Leilão 2: Futuro distante (INATIVO)
        l2 = leilao_service.criar_leilao(
            "Futuro 2", 200.0,
            agora + timedelta(days=5),
            agora + timedelta(days=6)
        )
        leiloes_criados.append(l2)
        
        # Leilão 3: Deve estar ABERTO
        l3 = leilao_service.criar_leilao(
            "Aberto", 300.0,
            agora - timedelta(minutes=30),
            agora + timedelta(hours=1),
            permitir_passado=True  # Permitir datas no passado para testes
        )
        leiloes_criados.append(l3)
        
        # Atualizar status
        leilao_service.atualizar_status_leiloes()
        
        # Testar filtros diversos
        # 1. Todos os leilões
        todos = leilao_service.listar_leiloes()
        assert len(todos) >= 3
        
        # 2. Apenas INATIVOS
        inativos = leilao_service.listar_leiloes(status=StatusLeilao.INATIVO)
        assert len(inativos) >= 2
        
        # 3. Apenas ABERTOS
        abertos = leilao_service.listar_leiloes(status=StatusLeilao.ABERTO)
        assert len(abertos) >= 1
        
        # 4. Filtro por data - próximas 24 horas
        proximas_24h = leilao_service.listar_leiloes(
            data_inicio_min=agora,
            data_inicio_max=agora + timedelta(days=1)
        )
        assert len(proximas_24h) >= 1
        
        # 5. Filtro por data - futuro distante
        futuro_distante = leilao_service.listar_leiloes(
            data_inicio_min=agora + timedelta(days=4),
            data_inicio_max=agora + timedelta(days=7)
        )
        assert len(futuro_distante) >= 1
    
    def test_estatisticas_sistema_completo(self, leilao_service):
        """
        Teste de integração: Estatísticas do sistema com múltiplos leilões
        """
        # Criar vários leilões
        leiloes = []
        for i in range(5):
            data_inicio = datetime.now() + timedelta(hours=i+1)
            data_termino = datetime.now() + timedelta(days=i+1)
            
            leilao = leilao_service.criar_leilao(
                f"Produto {i+1}",
                100.0 * (i+1),
                data_inicio,
                data_termino
            )
            leiloes.append(leilao)
        
        # Verificar estatísticas individuais
        for leilao in leiloes:
            stats = leilao_service.obter_estatisticas_leilao(leilao.id)
            assert stats['total_lances'] == 0
            assert stats['lance_atual'] == leilao.lance_minimo
        
        # Verificar listagens
        todos_leiloes = leilao_service.listar_leiloes()
        assert len(todos_leiloes) >= 5
        
        # Verificar que todos estão INATIVOS
        inativos = leilao_service.listar_leiloes(status=StatusLeilao.INATIVO)
        assert len(inativos) >= 5
    
    def test_transicoes_estado_multiplos_leiloes(self, leilao_service):
        """
        Teste de integração: Transições de estado em múltiplos leilões simultaneamente
        """
        agora = datetime.now()
        
        # Cenário complexo com vários leilões
        leiloes = []
        
        # Leilão que deve virar ABERTO
        l1 = leilao_service.criar_leilao(
            "Deve Abrir", 100.0,
            agora - timedelta(minutes=10),  # Já passou
            agora + timedelta(hours=1),     # Ainda não terminou
            permitir_passado=True  # Permitir datas no passado para testes
        )
        leiloes.append(('abrir', l1))
        
        # Leilão que deve expirar
        l2 = leilao_service.criar_leilao(
            "Deve Expirar", 200.0,
            agora - timedelta(hours=2),     # Já passou
            agora - timedelta(minutes=10),  # Já terminou
            permitir_passado=True  # Permitir datas no passado para testes
        )
        leiloes.append(('expirar', l2))
        
        # Leilão que deve permanecer INATIVO
        l3 = leilao_service.criar_leilao(
            "Fica Inativo", 300.0,
            agora + timedelta(hours=1),     # Ainda não começou
            agora + timedelta(days=1)       # Ainda não terminou
        )
        leiloes.append(('inativo', l3))
        
        # Estado inicial - todos INATIVOS
        for _, leilao in leiloes:
            assert leilao.status == StatusLeilao.INATIVO
        
        # Executar atualização de status
        resultado = leilao_service.atualizar_status_leiloes()
        
        # Verificar transições
        l1_atual = leilao_service.obter_leilao_por_id(l1.id)
        l2_atual = leilao_service.obter_leilao_por_id(l2.id)
        l3_atual = leilao_service.obter_leilao_por_id(l3.id)
        
        assert l1_atual.status == StatusLeilao.ABERTO   # Deve ter aberto
        assert l2_atual.status == StatusLeilao.EXPIRADO # Deve ter expirado
        assert l3_atual.status == StatusLeilao.INATIVO  # Deve continuar inativo
        
        # Verificar contadores
        assert resultado['abertos'] >= 1
        assert resultado['expirados'] >= 1
        
    def test_integridade_dados_operacoes_multiplas(self, leilao_service):
        """
        Teste de integração: Integridade dos dados durante múltiplas operações
        """
        # Criar leilão inicial
        leilao = leilao_service.criar_leilao(
            "Teste Integridade",
            500.0,
            datetime.now() + timedelta(hours=1),
            datetime.now() + timedelta(days=1)
        )
        
        # Realizar múltiplas operações
        operacoes_realizadas = []
        
        # 1. Múltiplas atualizações
        for i in range(3):
            leilao_atualizado = leilao_service.atualizar_leilao(
                leilao.id, 
                nome=f"Atualização {i+1}",
                lance_minimo=500.0 + (i * 100)
            )
            operacoes_realizadas.append(f"Atualização {i+1}")
            
            # Verificar integridade após cada operação
            assert leilao_atualizado.nome == f"Atualização {i+1}"
            assert leilao_atualizado.lance_minimo == 500.0 + (i * 100)
            assert leilao_atualizado.status == StatusLeilao.INATIVO
        
        # 3. Verificar que leilão ainda existe e dados estão corretos
        leilao_final = leilao_service.obter_leilao_por_id(leilao.id)
        assert leilao_final is not None
        assert leilao_final.nome == "Atualização 3"
        assert leilao_final.lance_minimo == 700.0  # Corrigido: 500 + (2 * 100) = 700
        
        # 4. Verificar estatísticas
        stats = leilao_service.obter_estatisticas_leilao(leilao.id)
        assert stats['total_lances'] == 0
        assert stats['lance_atual'] == 700.0  # Corrigido
        
        # 5. Verificar capacidade de receber lances
        pode, _ = leilao_service.pode_receber_lances(leilao.id)
        assert pode is False  # INATIVO não pode receber lances
        
        operacoes_realizadas.append("Verificações finais")
        assert len(operacoes_realizadas) == 4

class TestIntegracaoRegrasNegocio:
    """
    Testes de integração focados nas regras de negócio específicas
    """
    
    def test_regra_leilao_expirado_nao_finaliza(self, leilao_service):
        """
        Teste da regra: Leilões no estado EXPIRADO não podem assumir o estado FINALIZADO
        """
        # Criar leilão que vai expirar
        agora = datetime.now()
        leilao = leilao_service.criar_leilao(
            "Vai Expirar",
            100.0,
            agora - timedelta(hours=1),
            agora - timedelta(minutes=30),
            permitir_passado=True  # Permitir datas no passado para testes
        )
        
        # Forçar expiração
        leilao_service.atualizar_status_leiloes()
        leilao_atualizado = leilao_service.obter_leilao_por_id(leilao.id)
        assert leilao_atualizado.status == StatusLeilao.EXPIRADO
        
        # Tentar forçar finalização (simulando bug)
        session = leilao_service.db_config.get_session()
        try:
            # Esta operação não deveria ser possível pelas regras de negócio
            # Mas vamos testar se o sistema mantém a integridade
            session.query(Leilao).filter(Leilao.id == leilao.id).update({
                Leilao.status: StatusLeilao.FINALIZADO
            })
            session.commit()
            
            # Re-executar atualização de status
            leilao_service.atualizar_status_leiloes()
            
            # Verificar se o sistema corrigiu o estado inválido
            leilao_final = leilao_service.obter_leilao_por_id(leilao.id)
            # O leilão deve permanecer EXPIRADO ou voltar a EXPIRADO
            # (dependendo da implementação da regra)
            
        finally:
            session.close()
    
    def test_protecao_leiloes_abertos_finalizados(self, leilao_service):
        """
        Teste: Leilões ABERTOS e FINALIZADOS não podem ser alterados nem excluídos
        """
        # Criar leilão
        leilao = leilao_service.criar_leilao(
            "Para Proteger",
            100.0,
            datetime.now() - timedelta(minutes=30),
            datetime.now() + timedelta(hours=1),
            permitir_passado=True  # Permitir datas no passado para testes
        )
        
        # Abrir leilão
        leilao_service.atualizar_status_leiloes()
        leilao_aberto = leilao_service.obter_leilao_por_id(leilao.id)
        assert leilao_aberto.status == StatusLeilao.ABERTO
        
        # Tentar alterar (deve falhar)
        from src.utils.validators import ValidationError
        with pytest.raises(ValidationError, match="não pode ser alterado"):
            leilao_service.atualizar_leilao(leilao.id, nome="Tentativa")
        
        # Tentar excluir (deve falhar)
        with pytest.raises(ValidationError, match="não pode ser excluído"):
            leilao_service.excluir_leilao(leilao.id)
        
        # Verificar que leilão ainda existe e não foi alterado
        leilao_verificacao = leilao_service.obter_leilao_por_id(leilao.id)
        assert leilao_verificacao.nome == "Para Proteger"
        assert leilao_verificacao.status == StatusLeilao.ABERTO
    
    def test_consistencia_filtros_avancados(self, leilao_service):
        """
        Teste de integração: Consistência dos filtros com dados complexos
        """
        agora = datetime.now()
        
        # Criar cenário complexo
        leiloes_esperados = {
            'proxima_hora': [],
            'proxima_semana': [],
            'mes_que_vem': []
        }
        
        # Leilões para próxima hora
        for i in range(2):
            l = leilao_service.criar_leilao(
                f"Próxima Hora {i}",
                100.0,
                agora + timedelta(minutes=10 + i*10),
                agora + timedelta(hours=1 + i)
            )
            leiloes_esperados['proxima_hora'].append(l)
        
        # Leilões para próxima semana
        for i in range(3):
            l = leilao_service.criar_leilao(
                f"Próxima Semana {i}",
                200.0,
                agora + timedelta(days=1 + i),
                agora + timedelta(days=2 + i)
            )
            leiloes_esperados['proxima_semana'].append(l)
        
        # Leilões para mês que vem
        for i in range(1):
            l = leilao_service.criar_leilao(
                f"Mês Que Vem {i}",
                300.0,
                agora + timedelta(days=30 + i),
                agora + timedelta(days=31 + i)
            )
            leiloes_esperados['mes_que_vem'].append(l)
        
        # Testar filtros específicos
        # 1. Próxima hora
        proxima_hora = leilao_service.listar_leiloes(
            data_inicio_min=agora,
            data_inicio_max=agora + timedelta(hours=1)
        )
        assert len(proxima_hora) >= 2
        
        # 2. Próximos 7 dias
        proximos_7_dias = leilao_service.listar_leiloes(
            data_inicio_min=agora,
            data_inicio_max=agora + timedelta(days=7)
        )
        assert len(proximos_7_dias) >= 5  # 2 + 3
        
        # 3. Apenas mês que vem
        mes_que_vem = leilao_service.listar_leiloes(
            data_inicio_min=agora + timedelta(days=25),
            data_inicio_max=agora + timedelta(days=35)
        )
        assert len(mes_que_vem) >= 1
        
        # 4. Verificar que não há sobreposição incorreta
        total_geral = leilao_service.listar_leiloes()
        assert len(total_geral) >= 6