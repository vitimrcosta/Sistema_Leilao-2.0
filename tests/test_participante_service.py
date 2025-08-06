import pytest
from datetime import datetime, timedelta
from src.models import Participante, Lance, Leilao, StatusLeilao
from src.services.participante_service import ParticipanteService
from src.utils.validators import ValidationError

class TestParticipanteService:
    """Testes para o ParticipanteService"""
    
    def test_criar_participante_valido(self, clean_database, dados_participante_valido):
        """Teste: Criar participante com dados válidos"""
        service = ParticipanteService()
        service.db_config = clean_database
        
        participante = service.criar_participante(**dados_participante_valido)
        
        assert participante is not None
        assert participante.id is not None
        assert participante.cpf == dados_participante_valido['cpf']
        assert participante.nome == dados_participante_valido['nome']
        assert participante.email == dados_participante_valido['email']
        assert participante.data_nascimento == dados_participante_valido['data_nascimento']
        assert participante.data_cadastro is not None
    
    def test_criar_participante_cpf_invalido(self, clean_database):
        """Teste: Criar participante com CPF inválido"""
        service = ParticipanteService()
        service.db_config = clean_database
        
        # CPF vazio
        with pytest.raises(ValidationError, match="CPF é obrigatório"):
            service.criar_participante("", "João Silva", "joao@teste.com", datetime(1990, 1, 1))
        
        # CPF com tamanho errado
        with pytest.raises(ValidationError, match="CPF deve ter 11 dígitos"):
            service.criar_participante("123456789", "João Silva", "joao@teste.com", datetime(1990, 1, 1))
        
        # CPF com todos os dígitos iguais
        with pytest.raises(ValidationError, match="CPF inválido"):
            service.criar_participante("11111111111", "João Silva", "joao@teste.com", datetime(1990, 1, 1))
    
    def test_criar_participante_nome_invalido(self, clean_database):
        """Teste: Criar participante com nome inválido"""
        service = ParticipanteService()
        service.db_config = clean_database
        
        # Nome vazio
        with pytest.raises(ValidationError, match="Nome é obrigatório"):
            service.criar_participante("12345678901", "", "joao@teste.com", datetime(1990, 1, 1))
        
        # Nome muito curto
        with pytest.raises(ValidationError, match="Nome deve ter pelo menos 2 caracteres"):
            service.criar_participante("12345678901", "A", "joao@teste.com", datetime(1990, 1, 1))
    
    def test_criar_participante_email_invalido(self, clean_database):
        """Teste: Criar participante com email inválido"""
        service = ParticipanteService()
        service.db_config = clean_database
        
        # Email vazio
        with pytest.raises(ValidationError, match="Email é obrigatório"):
            service.criar_participante("12345678901", "João Silva", "", datetime(1990, 1, 1))
        
        # Email com formato inválido
        with pytest.raises(ValidationError, match="Email inválido"):
            service.criar_participante("12345678901", "João Silva", "email_invalido", datetime(1990, 1, 1))
    
    def test_criar_participante_idade_invalida(self, clean_database):
        """Teste: Criar participante menor de 18 anos"""
        service = ParticipanteService()
        service.db_config = clean_database
        
        # Data de nascimento que resulta em menor de 18 anos
        data_nascimento_menor = datetime.now() - timedelta(days=365*17)  # 17 anos
        
        with pytest.raises(ValidationError, match="Participante deve ter pelo menos 18 anos"):
            service.criar_participante("12345678901", "João Silva", "joao@teste.com", data_nascimento_menor)
    
    def test_criar_participante_cpf_duplicado(self, clean_database, dados_participante_valido):
        """Teste: Criar participante com CPF já cadastrado"""
        service = ParticipanteService()
        service.db_config = clean_database
        
        # Criar primeiro participante
        service.criar_participante(**dados_participante_valido)
        
        # Tentar criar segundo com mesmo CPF
        with pytest.raises(ValidationError, match="CPF .* já está cadastrado"):
            service.criar_participante(
                cpf=dados_participante_valido['cpf'],  # Mesmo CPF
                nome="Maria Santos",
                email="maria@teste.com",
                data_nascimento=datetime(1985, 5, 15)
            )
    
    def test_criar_participante_email_duplicado(self, clean_database, dados_participante_valido):
        """Teste: Criar participante com email já cadastrado"""
        service = ParticipanteService()
        service.db_config = clean_database
        
        # Criar primeiro participante
        service.criar_participante(**dados_participante_valido)
        
        # Tentar criar segundo com mesmo email
        with pytest.raises(ValidationError, match="Email .* já está cadastrado"):
            service.criar_participante(
                cpf="10987654321",
                nome="Maria Santos",
                email=dados_participante_valido['email'],  # Mesmo email
                data_nascimento=datetime(1985, 5, 15)
            )
    
    def test_atualizar_participante_sem_lances(self, clean_database, dados_participante_valido):
        """Teste: Atualizar participante que não tem lances (deve funcionar)"""
        service = ParticipanteService()
        service.db_config = clean_database
        
        # Criar participante
        participante = service.criar_participante(**dados_participante_valido)
        
        # Atualizar
        participante_atualizado = service.atualizar_participante(
            participante.id,
            nome="Nome Atualizado",
            email="email_atualizado@teste.com"
        )
        
        assert participante_atualizado.nome == "Nome Atualizado"
        assert participante_atualizado.email == "email_atualizado@teste.com"
        assert participante_atualizado.cpf == dados_participante_valido['cpf']  # Não alterado
    
    def test_atualizar_participante_com_lances_deve_falhar(self, clean_database):
        """Teste: Tentar atualizar participante que já tem lances (deve falhar)"""
        service = ParticipanteService()
        service.db_config = clean_database
        
        # Criar participante
        participante = service.criar_participante(
            "12345678901", "João Silva", "joao@teste.com", datetime(1990, 1, 1)
        )
        
        # Simular que o participante fez um lance
        session = clean_database.get_session()
        
        # Primeiro criar um leilão
        leilao = Leilao(
            nome="Leilão Teste",
            lance_minimo=100.0,
            data_inicio=datetime.now() + timedelta(hours=1),
            data_termino=datetime.now() + timedelta(days=1),
            status=StatusLeilao.INATIVO
        )
        session.add(leilao)
        session.commit()
        session.refresh(leilao)
        
        # Criar lance
        lance = Lance(
            valor=150.0,
            leilao_id=leilao.id,
            participante_id=participante.id
        )
        session.add(lance)
        session.commit()
        session.close()
        
        # Tentar atualizar participante (deve falhar)
        with pytest.raises(ValidationError, match="Participante que já efetuou lances não pode ser alterado"):
            service.atualizar_participante(participante.id, nome="Tentativa de Alteração")
    
    def test_excluir_participante_sem_lances(self, clean_database, dados_participante_valido):
        """Teste: Excluir participante sem lances (deve funcionar)"""
        service = ParticipanteService()
        service.db_config = clean_database
        
        # Criar participante
        participante = service.criar_participante(**dados_participante_valido)
        
        # Excluir
        resultado = service.excluir_participante(participante.id)
        assert resultado is True
        
        # Verificar se foi excluído
        participante_excluido = service.obter_participante_por_id(participante.id)
        assert participante_excluido is None
    
    def test_excluir_participante_com_lances_deve_falhar(self, clean_database):
        """Teste: Tentar excluir participante que já tem lances (deve falhar)"""
        service = ParticipanteService()
        service.db_config = clean_database
        
        # Criar participante
        participante = service.criar_participante(
            "12345678901", "João Silva", "joao@teste.com", datetime(1990, 1, 1)
        )
        
        # Simular que o participante fez um lance (similar ao teste anterior)
        session = clean_database.get_session()
        leilao = Leilao(
            nome="Leilão Teste",
            lance_minimo=100.0,
            data_inicio=datetime.now() + timedelta(hours=1),
            data_termino=datetime.now() + timedelta(days=1),
            status=StatusLeilao.INATIVO
        )
        session.add(leilao)
        session.commit()
        session.refresh(leilao)
        
        lance = Lance(
            valor=150.0,
            leilao_id=leilao.id,
            participante_id=participante.id
        )
        session.add(lance)
        session.commit()
        session.close()
        
        # Tentar excluir participante (deve falhar)
        with pytest.raises(ValidationError, match="Participante que já efetuou lances não pode ser excluído"):
            service.excluir_participante(participante.id)
    
    def test_obter_participante_por_cpf(self, clean_database, dados_participante_valido):
        """Teste: Buscar participante por CPF"""
        service = ParticipanteService()
        service.db_config = clean_database
        
        # Criar participante
        participante_criado = service.criar_participante(**dados_participante_valido)
        
        # Buscar por CPF
        participante_encontrado = service.obter_participante_por_cpf(dados_participante_valido['cpf'])
        
        assert participante_encontrado is not None
        assert participante_encontrado.id == participante_criado.id
        assert participante_encontrado.cpf == dados_participante_valido['cpf']
    
    def test_obter_participante_por_email(self, clean_database, dados_participante_valido):
        """Teste: Buscar participante por email"""
        service = ParticipanteService()
        service.db_config = clean_database
        
        # Criar participante
        participante_criado = service.criar_participante(**dados_participante_valido)
        
        # Buscar por email
        participante_encontrado = service.obter_participante_por_email(dados_participante_valido['email'])
        
        assert participante_encontrado is not None
        assert participante_encontrado.id == participante_criado.id
        assert participante_encontrado.email == dados_participante_valido['email']
    
    def test_listar_participantes_filtro_nome(self, clean_database):
        """Teste: Listar participantes com filtro por nome"""
        service = ParticipanteService()
        service.db_config = clean_database
        
        # Criar vários participantes
        service.criar_participante("12345678901", "João Silva", "joao@teste.com", datetime(1990, 1, 1))
        service.criar_participante("10987654321", "Maria Silva", "maria@teste.com", datetime(1985, 5, 15))
        service.criar_participante("11122233344", "Pedro Santos", "pedro@teste.com", datetime(1992, 10, 20))
        
        # Buscar por "Silva"
        participantes_silva = service.listar_participantes(nome_parcial="Silva")
        assert len(participantes_silva) == 2
        assert all("Silva" in p.nome for p in participantes_silva)
        
        # Buscar por "Santos"
        participantes_santos = service.listar_participantes(nome_parcial="Santos")
        assert len(participantes_santos) == 1
        assert "Santos" in participantes_santos[0].nome
    
    def test_verificar_pode_alterar_excluir(self, clean_database, dados_participante_valido):
        """Teste: Verificar se participante pode ser alterado/excluído"""
        service = ParticipanteService()
        service.db_config = clean_database
        
        # Criar participante
        participante = service.criar_participante(**dados_participante_valido)
        
        # Verificar sem lances (deve poder)
        pode, motivo = service.verificar_pode_alterar_excluir(participante.id)
        assert pode is True
        assert "pode ser alterado/excluído" in motivo
    
    def test_obter_estatisticas_participante_sem_lances(self, clean_database, dados_participante_valido):
        """Teste: Estatísticas de participante sem lances"""
        service = ParticipanteService()
        service.db_config = clean_database
        
        # Criar participante
        participante = service.criar_participante(**dados_participante_valido)
        
        # Obter estatísticas
        stats = service.obter_estatisticas_participante(participante.id)
        
        assert stats['total_lances'] == 0
        assert stats['total_gasto'] == 0.0
        assert stats['leiloes_participados'] == 0
        assert stats['leiloes_vencidos'] == 0
        assert stats['maior_lance'] is None
        assert stats['menor_lance'] is None
    
    def test_validar_cpf_disponivel(self, clean_database, dados_participante_valido):
        """Teste: Validar disponibilidade de CPF"""
        service = ParticipanteService()
        service.db_config = clean_database
        
        # CPF não usado ainda (deve estar disponível)
        assert service.validar_cpf_disponivel("12345678901") is True
        
        # Criar participante
        participante = service.criar_participante(**dados_participante_valido)
        
        # CPF agora usado (não deve estar disponível)
        assert service.validar_cpf_disponivel(dados_participante_valido['cpf']) is False
        
        # Mas deve estar disponível excluindo o próprio participante
        assert service.validar_cpf_disponivel(dados_participante_valido['cpf'], participante.id) is True
    
    def test_validar_email_disponivel(self, clean_database, dados_participante_valido):
        """Teste: Validar disponibilidade de email"""
        service = ParticipanteService()
        service.db_config = clean_database
        
        # Email não usado ainda (deve estar disponível)
        assert service.validar_email_disponivel("teste@exemplo.com") is True
        
        # Criar participante
        participante = service.criar_participante(**dados_participante_valido)
        
        # Email agora usado (não deve estar disponível)
        assert service.validar_email_disponivel(dados_participante_valido['email']) is False
        
        # Mas deve estar disponível excluindo o próprio participante
        assert service.validar_email_disponivel(dados_participante_valido['email'], participante.id) is True
    
    def test_buscar_participantes_por_idade(self, clean_database):
        """Teste: Buscar participantes por faixa etária"""
        service = ParticipanteService()
        service.db_config = clean_database
        
        hoje = datetime.now()
        
        # Criar participantes com idades exatas
        # 25 anos
        service.criar_participante("12345678901", "João 25", "joao25@teste.com", 
                                  datetime(hoje.year - 25, hoje.month, hoje.day))
        # 30 anos  
        service.criar_participante("10987654321", "Maria 30", "maria30@teste.com", 
                                  datetime(hoje.year - 30, hoje.month, hoje.day))
        # 35 anos
        service.criar_participante("11122233344", "Pedro 35", "pedro35@teste.com", 
                                  datetime(hoje.year - 35, hoje.month, hoje.day))
        
        # Buscar participantes entre 28 e 32 anos
        participantes_28_32 = service.buscar_participantes_por_idade(28, 32)
        assert len(participantes_28_32) == 1
        assert "Maria 30" in participantes_28_32[0].nome
        
        # Buscar participantes com mais de 30 anos (30+)
        participantes_mais_30 = service.buscar_participantes_por_idade(idade_minima=30)
        assert len(participantes_mais_30) == 2  # Maria (30) e Pedro (35)
        
        # Buscar participantes com menos de 30 anos
        participantes_menos_30 = service.buscar_participantes_por_idade(idade_maxima=29)
        assert len(participantes_menos_30) == 1
        assert "João 25" in participantes_menos_30[0].nome

class TestParticipanteServiceValidacoes:
    """Testes específicos para validações do ParticipanteService"""
    
    def test_normalizacao_cpf(self, clean_database):
        """Teste: CPF deve ser normalizado removendo caracteres especiais"""
        service = ParticipanteService()
        service.db_config = clean_database
        
        # Criar participante com CPF formatado
        participante = service.criar_participante(
            cpf="123.456.789-01",  # Com formatação
            nome="João Silva",
            email="joao@teste.com",
            data_nascimento=datetime(1990, 1, 1)
        )
        
        # CPF deve estar salvo sem formatação
        assert participante.cpf == "12345678901"
        
        # Buscar deve funcionar com qualquer formato
        encontrado = service.obter_participante_por_cpf("123.456.789-01")
        assert encontrado is not None
        assert encontrado.id == participante.id
    
    def test_normalizacao_email(self, clean_database):
        """Teste: Email deve ser normalizado"""
        service = ParticipanteService()
        service.db_config = clean_database
        
        # Criar participante com email que pode ser normalizado
        participante = service.criar_participante(
            cpf="12345678901",
            nome="João Silva",
            email="JOAO@TESTE.COM",  # Maiúsculo
            data_nascimento=datetime(1990, 1, 1)
        )
        
        # Email deve estar normalizado
        assert participante.email.lower() == "joao@teste.com"
    
    def test_normalizacao_nome(self, clean_database):
        """Teste: Nome deve ser normalizado removendo espaços extras"""
        service = ParticipanteService()
        service.db_config = clean_database
        
        # Criar participante com nome com espaços extras
        participante = service.criar_participante(
            cpf="12345678901",
            nome="  João   Silva  ",  # Espaços extras
            email="joao@teste.com",
            data_nascimento=datetime(1990, 1, 1)
        )
        
        # Nome deve estar limpo
        assert participante.nome == "João   Silva"  # Espaços internos mantidos, externos removidos
    
    def test_atualizacao_parcial_campos(self, clean_database):
        """Teste: Atualização parcial deve manter campos não alterados"""
        service = ParticipanteService()
        service.db_config = clean_database
        
        # Criar participante
        participante = service.criar_participante(
            cpf="12345678901",
            nome="João Silva",
            email="joao@teste.com",
            data_nascimento=datetime(1990, 1, 1)
        )
        
        # Atualizar apenas nome
        participante_atualizado = service.atualizar_participante(
            participante.id,
            nome="João Santos"
        )
        
        # Nome deve ter mudado, outros campos mantidos
        assert participante_atualizado.nome == "João Santos"
        assert participante_atualizado.cpf == "12345678901"
        assert participante_atualizado.email == "joao@teste.com"
        assert participante_atualizado.data_nascimento == datetime(1990, 1, 1)
    
    def test_erro_participante_inexistente(self, clean_database):
        """Teste: Operações com participante inexistente devem dar erro apropriado"""
        service = ParticipanteService()
        service.db_config = clean_database
        
        # Tentar atualizar participante inexistente
        with pytest.raises(ValidationError, match="Participante com ID 99999 não encontrado"):
            service.atualizar_participante(99999, nome="Teste")
        
        # Tentar excluir participante inexistente
        with pytest.raises(ValidationError, match="Participante com ID 99999 não encontrado"):
            service.excluir_participante(99999)
        
        # Tentar obter estatísticas de participante inexistente
        with pytest.raises(ValidationError, match="Participante com ID 99999 não encontrado"):
            service.obter_estatisticas_participante(99999)
    
    def test_listar_participantes_filtro_com_sem_lances(self, clean_database):
        """Teste: Filtrar participantes que têm ou não têm lances"""
        service = ParticipanteService()
        service.db_config = clean_database
        
        # Criar participantes
        p1 = service.criar_participante("12345678901", "João", "joao@teste.com", datetime(1990, 1, 1))
        p2 = service.criar_participante("10987654321", "Maria", "maria@teste.com", datetime(1985, 5, 15))
        p3 = service.criar_participante("11122233344", "Pedro", "pedro@teste.com", datetime(1992, 10, 20))
        
        # Simular que João e Maria fizeram lances
        session = clean_database.get_session()
        
        # Criar leilão
        leilao = Leilao(
            nome="Leilão Teste",
            lance_minimo=100.0,
            data_inicio=datetime.now() + timedelta(hours=1),
            data_termino=datetime.now() + timedelta(days=1),
            status=StatusLeilao.INATIVO
        )
        session.add(leilao)
        session.commit()
        session.refresh(leilao)
        
        # João faz lance
        lance1 = Lance(valor=150.0, leilao_id=leilao.id, participante_id=p1.id)
        session.add(lance1)
        
        # Maria faz lance
        lance2 = Lance(valor=200.0, leilao_id=leilao.id, participante_id=p2.id)
        session.add(lance2)
        
        session.commit()
        session.close()
        
        # Testar filtros
        # Participantes COM lances
        com_lances = service.listar_participantes(tem_lances=True)
        assert len(com_lances) == 2
        nomes_com_lances = [p.nome for p in com_lances]
        assert "João" in nomes_com_lances
        assert "Maria" in nomes_com_lances
        
        # Participantes SEM lances
        sem_lances = service.listar_participantes(tem_lances=False)
        assert len(sem_lances) == 1
        assert sem_lances[0].nome == "Pedro"
        
        # Todos os participantes
        todos = service.listar_participantes(tem_lances=None)
        assert len(todos) == 3

class TestParticipanteServiceCoberturaEspecifica:
    """Testes específicos para cobrir as linhas exatas sem cobertura"""
    
    def test_atualizar_cpf_duplicado_outro_participante(self, clean_database):
        """
        Teste para cobrir as linhas 76-83 - caso de CPF duplicado
        Especificamente a linha que faz raise ValidationError para CPF duplicado
        """
        service = ParticipanteService()
        service.db_config = clean_database
        
        # Criar dois participantes
        participante1 = service.criar_participante(
            cpf="12345678901",
            nome="João Silva",
            email="joao@teste.com",
            data_nascimento=datetime(1990, 1, 1)
        )
        
        participante2 = service.criar_participante(
            cpf="10987654321",
            nome="Maria Santos",
            email="maria@teste.com",
            data_nascimento=datetime(1985, 5, 15)
        )
        
        # Tentar atualizar CPF do participante1 para o CPF do participante2
        # Isso deve executar as linhas 76-83 e dar erro na verificação de duplicação
        with pytest.raises(ValidationError, match="CPF 10987654321 já está cadastrado para outro participante"):
            service.atualizar_participante(
                participante_id=participante1.id,
                cpf="10987654321"  # CPF que já pertence ao participante2
            )
    
    def test_atualizar_email_duplicado_outro_participante(self, clean_database):
        """
        Teste para cobrir a linha 95 - caso de email duplicado
        Especificamente o raise ValidationError para email duplicado
        """
        service = ParticipanteService()
        service.db_config = clean_database
        
        # Criar dois participantes
        participante1 = service.criar_participante(
            cpf="12345678901",
            nome="João Silva", 
            email="joao@teste.com",
            data_nascimento=datetime(1990, 1, 1)
        )
        
        participante2 = service.criar_participante(
            cpf="10987654321",
            nome="Maria Santos",
            email="maria@teste.com", 
            data_nascimento=datetime(1985, 5, 15)
        )
        
        # Tentar atualizar email do participante1 para o email do participante2
        # Isso deve executar a linha 95 com o raise ValidationError
        with pytest.raises(ValidationError, match="Email maria@teste.com já está cadastrado para outro participante"):
            service.atualizar_participante(
                participante_id=participante1.id,
                email="maria@teste.com"  # Email que já pertence ao participante2
            )
    
    def test_atualizar_data_nascimento(self, clean_database):
        """
        Teste para cobrir a linha 99 - atualização de data_nascimento
        Especificamente a linha: participante.data_nascimento = ValidadorParticipante.validar_data_nascimento(data_nascimento)
        """
        service = ParticipanteService()
        service.db_config = clean_database
        
        # Criar participante inicial
        participante = service.criar_participante(
            cpf="12345678901",
            nome="João Silva",
            email="joao@teste.com", 
            data_nascimento=datetime(1990, 1, 1)
        )
        
        # Atualizar apenas a data de nascimento
        # Isso deve executar a linha 99 que valida e atribui a nova data
        nova_data = datetime(1985, 12, 25)
        participante_atualizado = service.atualizar_participante(
            participante_id=participante.id,
            data_nascimento=nova_data
        )
        
        # Verificar se a data foi atualizada corretamente
        assert participante_atualizado.data_nascimento == nova_data
        # Outros campos devem permanecer iguais
        assert participante_atualizado.cpf == "12345678901"
        assert participante_atualizado.nome == "João Silva"
        assert participante_atualizado.email == "joao@teste.com"
    
    def test_verificar_pode_alterar_excluir_participante_inexistente(self, clean_database):
        """
        Teste para cobrir a linha 224 - participante não encontrado
        Especificamente: return False, "Participante não encontrado"
        """
        service = ParticipanteService()
        service.db_config = clean_database
        
        # Tentar verificar participante que não existe
        # Isso deve executar a linha 224 que retorna o erro de participante não encontrado
        pode_alterar, motivo = service.verificar_pode_alterar_excluir(99999)
        
        assert pode_alterar is False
        assert motivo == "Participante não encontrado"

class TestParticipanteServiceCoberturaComplementar:
    """Testes complementares para garantir cobertura completa das funcionalidades testadas"""
    
    def test_atualizar_cpf_valido_sucesso(self, clean_database):
        """
        Teste complementar para cobrir o caminho de sucesso da atualização de CPF
        Garante que as linhas 76-83 também são executadas no caso de sucesso
        """
        service = ParticipanteService()
        service.db_config = clean_database
        
        # Criar participante
        participante = service.criar_participante(
            cpf="12345678901",
            nome="João Silva",
            email="joao@teste.com",
            data_nascimento=datetime(1990, 1, 1)
        )
        
        # Atualizar CPF para um válido e disponível
        # Isso executa as linhas 76-83 no caminho de sucesso
        participante_atualizado = service.atualizar_participante(
            participante_id=participante.id,
            cpf="10987654321"  # CPF válido e disponível
        )
        
        # Verificar se o CPF foi atualizado
        assert participante_atualizado.cpf == "10987654321"
    
    def test_atualizar_email_valido_sucesso(self, clean_database):
        """
        Teste complementar para cobrir o caminho de sucesso da atualização de email
        """
        service = ParticipanteService()
        service.db_config = clean_database
        
        # Criar participante
        participante = service.criar_participante(
            cpf="12345678901",
            nome="João Silva",
            email="joao@teste.com",
            data_nascimento=datetime(1990, 1, 1)
        )
        
        # Atualizar email para um válido e disponível
        participante_atualizado = service.atualizar_participante(
            participante_id=participante.id,
            email="novo.email@teste.com"  # Email válido e disponível
        )
        
        # Verificar se o email foi atualizado
        assert participante_atualizado.email == "novo.email@teste.com"
    
    def test_atualizar_data_nascimento_invalida(self, clean_database):
        """
        Teste para garantir que a validação de data de nascimento funciona corretamente
        """
        service = ParticipanteService()
        service.db_config = clean_database
        
        # Criar participante
        participante = service.criar_participante(
            cpf="12345678901",
            nome="João Silva",
            email="joao@teste.com",
            data_nascimento=datetime(1990, 1, 1)
        )
        
        # Tentar atualizar com data de nascimento inválida (menor de 18 anos)
        data_menor_idade = datetime.now() - timedelta(days=365*17)  # 17 anos
        
        with pytest.raises(ValidationError, match="Participante deve ter pelo menos 18 anos"):
            service.atualizar_participante(
                participante_id=participante.id,
                data_nascimento=data_menor_idade
            )
    
    def test_verificar_pode_alterar_excluir_participante_existente_sem_lances(self, clean_database):
        """
        Teste complementar para verificar participante que existe e pode ser alterado
        """
        service = ParticipanteService()
        service.db_config = clean_database
        
        # Criar participante
        participante = service.criar_participante(
            cpf="12345678901",
            nome="João Silva",
            email="joao@teste.com",
            data_nascimento=datetime(1990, 1, 1)
        )
        
        # Verificar participante que existe e não tem lances
        pode_alterar, motivo = service.verificar_pode_alterar_excluir(participante.id)
        
        assert pode_alterar is True
        assert motivo == "Participante pode ser alterado/excluído"
    
    def test_verificar_pode_alterar_excluir_participante_com_lances(self, clean_database):
        """
        Teste para verificar participante que tem lances e não pode ser alterado
        """
        service = ParticipanteService()
        service.db_config = clean_database
        
        # Criar participante
        participante = service.criar_participante(
            cpf="12345678901",
            nome="João Silva",
            email="joao@teste.com",
            data_nascimento=datetime(1990, 1, 1)
        )
        
        # Criar leilão e lance
        session = clean_database.get_session()
        
        leilao = Leilao(
            nome="Leilão Teste",
            lance_minimo=100.0,
            data_inicio=datetime.now() + timedelta(hours=1),
            data_termino=datetime.now() + timedelta(days=1),
            status=StatusLeilao.INATIVO
        )
        session.add(leilao)
        session.commit()
        session.refresh(leilao)
        
        lance = Lance(
            valor=150.0,
            leilao_id=leilao.id,
            participante_id=participante.id
        )
        session.add(lance)
        session.commit()
        session.close()
        
        # Verificar participante que tem lances
        pode_alterar, motivo = service.verificar_pode_alterar_excluir(participante.id)
        
        assert pode_alterar is False
        assert "possui 1 lance(s)" in motivo
        assert "não pode ser alterado/excluído" in motivo