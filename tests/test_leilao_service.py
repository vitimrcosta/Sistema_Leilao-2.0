import pytest
from datetime import datetime, timedelta
from src.models import StatusLeilao, Leilao
from src.utils.validators import ValidationError

class TestLeilaoService:
    """Testes para o LeilaoService"""
    
    def test_criar_leilao_valido(self, leilao_service, dados_leilao_valido):
        """Teste: Criar leilão com dados válidos"""
        leilao = leilao_service.criar_leilao(**dados_leilao_valido)
        
        assert leilao is not None
        assert leilao.id is not None
        assert leilao.nome == dados_leilao_valido['nome']
        assert leilao.lance_minimo == dados_leilao_valido['lance_minimo']
        assert leilao.status == StatusLeilao.INATIVO
        assert leilao.data_cadastro is not None
    
    def test_criar_leilao_nome_invalido(self, leilao_service):
        """Teste: Criar leilão com nome inválido"""
        data_inicio = datetime.now() + timedelta(hours=1)
        data_termino = datetime.now() + timedelta(days=1)
        
        # Nome vazio
        with pytest.raises(ValidationError, match="Nome do leilão é obrigatório"):
            leilao_service.criar_leilao("", 100.0, data_inicio, data_termino)
        
        # Nome muito curto
        with pytest.raises(ValidationError, match="Nome do leilão deve ter pelo menos 3 caracteres"):
            leilao_service.criar_leilao("AB", 100.0, data_inicio, data_termino)
    
    def test_criar_leilao_lance_minimo_invalido(self, leilao_service):
        """Teste: Criar leilão com lance mínimo inválido"""
        data_inicio = datetime.now() + timedelta(hours=1)
        data_termino = datetime.now() + timedelta(days=1)
        
        # Lance mínimo negativo
        with pytest.raises(ValidationError, match="Lance mínimo deve ser maior que zero"):
            leilao_service.criar_leilao("Produto Teste", -50.0, data_inicio, data_termino)
        
        # Lance mínimo zero
        with pytest.raises(ValidationError, match="Lance mínimo deve ser maior que zero"):
            leilao_service.criar_leilao("Produto Teste", 0, data_inicio, data_termino)
    
    def test_criar_leilao_datas_invalidas(self, leilao_service):
        """Teste: Criar leilão com datas inválidas"""
        # Data de término anterior à data de início
        data_inicio = datetime.now() + timedelta(days=1)
        data_termino = datetime.now() + timedelta(hours=1)
        
        with pytest.raises(ValidationError, match="Data de término deve ser posterior à data de início"):
            leilao_service.criar_leilao("Produto Teste", 100.0, data_inicio, data_termino)
    
    def test_atualizar_leilao_inativo(self, leilao_service, leilao_valido):
        """Teste: Atualizar leilão no estado INATIVO (deve funcionar)"""
        novo_nome = "PlayStation 5 Pro"
        novo_lance = 1500.00
        
        leilao_atualizado = leilao_service.atualizar_leilao(
            leilao_valido.id,
            nome=novo_nome,
            lance_minimo=novo_lance
        )
        
        assert leilao_atualizado.nome == novo_nome
        assert leilao_atualizado.lance_minimo == novo_lance
        assert leilao_atualizado.status == StatusLeilao.INATIVO
    
    def test_atualizar_leilao_aberto_deve_falhar(self, leilao_service, leilao_aberto):
        """Teste: Tentar atualizar leilão ABERTO (deve falhar)"""
        with pytest.raises(ValidationError, match="Leilão no estado ABERTO não pode ser alterado"):
            leilao_service.atualizar_leilao(leilao_aberto.id, nome="Tentativa de alteração")
    
    def test_excluir_leilao_inativo(self, leilao_service, leilao_valido):
        """Teste: Excluir leilão INATIVO (deve funcionar)"""
        resultado = leilao_service.excluir_leilao(leilao_valido.id)
        
        assert resultado is True
        
        # Verificar se foi realmente excluído
        leilao_excluido = leilao_service.obter_leilao_por_id(leilao_valido.id)
        assert leilao_excluido is None
    
    def test_excluir_leilao_aberto_deve_falhar(self, leilao_service, leilao_aberto):
        """Teste: Tentar excluir leilão ABERTO (deve falhar)"""
        with pytest.raises(ValidationError, match="Leilão no estado ABERTO não pode ser excluído"):
            leilao_service.excluir_leilao(leilao_aberto.id)
    
    def test_atualizar_status_inativo_para_aberto(self, leilao_service):
        """Teste: Leilão INATIVO deve virar ABERTO quando atingir data de início"""
        # Criar leilão com data de início no passado (para testes)
        data_inicio = datetime.now() - timedelta(minutes=30)
        data_termino = datetime.now() + timedelta(hours=1)
        
        leilao = leilao_service.criar_leilao(
            "Produto para abrir",
            100.0,
            data_inicio,
            data_termino,
            permitir_passado=True  # Permitir data no passado para testes
        )
        
        assert leilao.status == StatusLeilao.INATIVO
        
        # Atualizar status
        resultado = leilao_service.atualizar_status_leiloes()
        
        # Verificar se abriu
        leilao_atualizado = leilao_service.obter_leilao_por_id(leilao.id)
        assert leilao_atualizado.status == StatusLeilao.ABERTO
        assert resultado['abertos'] >= 1
    
    def test_listar_leiloes_sem_filtro(self, leilao_service, varios_leiloes):
        """Teste: Listar todos os leilões sem filtro"""
        leiloes = leilao_service.listar_leiloes()
        
        assert len(leiloes) >= 3  # Pelo menos os 3 da fixture
        assert all(isinstance(leilao, Leilao) for leilao in leiloes)
    
    def test_listar_leiloes_filtro_status(self, leilao_service, varios_leiloes):
        """Teste: Listar leilões filtrados por status"""
        # Filtrar apenas INATIVOS
        inativos = leilao_service.listar_leiloes(status=StatusLeilao.INATIVO)
        assert all(leilao.status == StatusLeilao.INATIVO for leilao in inativos)
        
        # Filtrar apenas ABERTOS
        abertos = leilao_service.listar_leiloes(status=StatusLeilao.ABERTO)
        assert all(leilao.status == StatusLeilao.ABERTO for leilao in abertos)
    
    def test_listar_leiloes_filtro_data(self, leilao_service, varios_leiloes):
        """Teste: Listar leilões filtrados por data"""
        agora = datetime.now()
        
        # Filtrar leilões que começam nas próximas 2 horas
        filtrados = leilao_service.listar_leiloes(
            data_inicio_min=agora,
            data_inicio_max=agora + timedelta(hours=2)
        )
        
        assert len(filtrados) >= 1
        for leilao in filtrados:
            assert agora <= leilao.data_inicio <= agora + timedelta(hours=2)
    
    def test_pode_receber_lances_leilao_aberto(self, leilao_service, leilao_aberto):
        """Teste: Leilão ABERTO deve poder receber lances"""
        pode, motivo = leilao_service.pode_receber_lances(leilao_aberto.id)
        
        assert pode is True
        assert "pode receber lances" in motivo
    
    def test_pode_receber_lances_leilao_inativo(self, leilao_service, leilao_valido):
        """Teste: Leilão INATIVO não deve poder receber lances"""
        pode, motivo = leilao_service.pode_receber_lances(leilao_valido.id)
        
        assert pode is False
        assert "INATIVO" in motivo
    
    def test_obter_estatisticas_leilao_sem_lances(self, leilao_service, leilao_valido):
        """Teste: Estatísticas de leilão sem lances"""
        stats = leilao_service.obter_estatisticas_leilao(leilao_valido.id)
        
        assert stats['total_lances'] == 0
        assert stats['maior_lance'] is None
        assert stats['menor_lance'] is None
        assert stats['participantes_unicos'] == 0
        assert stats['lance_atual'] == leilao_valido.lance_minimo
    
    def test_obter_leilao_por_id_existente(self, leilao_service, leilao_valido):
        """Teste: Obter leilão existente por ID"""
        leilao = leilao_service.obter_leilao_por_id(leilao_valido.id)
        
        assert leilao is not None
        assert leilao.id == leilao_valido.id
        assert leilao.nome == leilao_valido.nome
    
    def test_obter_leilao_por_id_inexistente(self, leilao_service):
        """Teste: Tentar obter leilão inexistente por ID"""
        leilao = leilao_service.obter_leilao_por_id(99999)
        
        assert leilao is None
    
    def test_leiloes_que_precisa_notificar_vazio(self, leilao_service, varios_leiloes):
        """Teste: Lista de leilões para notificar deve estar vazia (sem finalizados)"""
        leiloes_notificar = leilao_service.leiloes_que_precisa_notificar()
        
        assert isinstance(leiloes_notificar, list)
        # Como não temos leilões finalizados com vencedor, deve estar vazio
        assert len(leiloes_notificar) == 0

class TestLeilaoServiceValidacoes:
    """Testes específicos para validações do LeilaoService"""
    
    def test_validacao_nome_apenas_espacos(self, leilao_service):
        """Teste: Nome com apenas espaços deve falhar"""
        data_inicio = datetime.now() + timedelta(hours=1)
        data_termino = datetime.now() + timedelta(days=1)
        
        with pytest.raises(ValidationError):
            leilao_service.criar_leilao("   ", 100.0, data_inicio, data_termino)
    
    def test_validacao_lance_minimo_string(self, leilao_service):
        """Teste: Lance mínimo como string inválida deve falhar"""
        data_inicio = datetime.now() + timedelta(hours=1)
        data_termino = datetime.now() + timedelta(days=1)
        
        with pytest.raises(ValidationError):
            leilao_service.criar_leilao("Produto", "abc", data_inicio, data_termino)
    
    def test_atualizacao_parcial_leilao(self, leilao_service, leilao_valido):
        """Teste: Atualização parcial deve manter outros campos inalterados"""
        nome_original = leilao_valido.nome
        lance_original = leilao_valido.lance_minimo
        
        # Atualizar apenas o nome
        leilao_service.atualizar_leilao(leilao_valido.id, nome="Novo Nome")
        
        leilao_atualizado = leilao_service.obter_leilao_por_id(leilao_valido.id)
        assert leilao_atualizado.nome == "Novo Nome"
        assert leilao_atualizado.lance_minimo == lance_original  # Deve permanecer igual