import pytest
from datetime import datetime, timedelta
from src.utils.validators import (
    ValidadorParticipante, 
    ValidadorLeilao, 
    ValidadorLance,
    ValidationError
)

class TestValidadorParticipante:
    """Testes para ValidadorParticipante"""
    
    def test_validar_cpf_valido(self):
        """Teste: CPF válido deve ser aceito e normalizado"""
        # CPF sem formatação
        cpf_limpo = ValidadorParticipante.validar_cpf("12345678901")
        assert cpf_limpo == "12345678901"
        
        # CPF com formatação
        cpf_formatado = ValidadorParticipante.validar_cpf("123.456.789-01")
        assert cpf_formatado == "12345678901"
    
    def test_validar_cpf_vazio(self):
        """Teste: CPF vazio deve dar erro - linha não testada"""
        with pytest.raises(ValidationError, match="CPF é obrigatório"):
            ValidadorParticipante.validar_cpf("")
        
        with pytest.raises(ValidationError, match="CPF é obrigatório"):
            ValidadorParticipante.validar_cpf(None)
    
    def test_validar_cpf_tamanho_errado(self):
        """Teste: CPF com tamanho errado"""
        with pytest.raises(ValidationError, match="CPF deve ter 11 dígitos"):
            ValidadorParticipante.validar_cpf("123456789")  # 9 dígitos
        
        with pytest.raises(ValidationError, match="CPF deve ter 11 dígitos"):
            ValidadorParticipante.validar_cpf("123456789012")  # 12 dígitos
    
    def test_validar_cpf_todos_digitos_iguais(self):
        """Teste: CPF com todos os dígitos iguais"""
        with pytest.raises(ValidationError, match="CPF inválido"):
            ValidadorParticipante.validar_cpf("11111111111")
        
        with pytest.raises(ValidationError, match="CPF inválido"):
            ValidadorParticipante.validar_cpf("00000000000")
    
    def test_validar_email_valido(self):
        """Teste: Email válido deve ser normalizado"""
        email_normalizado = ValidadorParticipante.validar_email("teste@exemplo.com")
        assert email_normalizado.lower() == "teste@exemplo.com"
    
    def test_validar_email_vazio(self):
        """Teste: Email vazio deve dar erro"""
        with pytest.raises(ValidationError, match="Email é obrigatório"):
            ValidadorParticipante.validar_email("")
        
        with pytest.raises(ValidationError, match="Email é obrigatório"):
            ValidadorParticipante.validar_email(None)
    
    def test_validar_email_invalido(self):
        """Teste: Email com formato inválido"""
        with pytest.raises(ValidationError, match="Email inválido"):
            ValidadorParticipante.validar_email("email_sem_arroba")
        
        with pytest.raises(ValidationError, match="Email inválido"):
            ValidadorParticipante.validar_email("@dominio.com")
    
    def test_validar_nome_valido(self):
        """Teste: Nome válido deve ser normalizado"""
        nome_limpo = ValidadorParticipante.validar_nome("  João Silva  ")
        assert nome_limpo == "João Silva"
    
    def test_validar_nome_vazio(self):
        """Teste: Nome vazio deve dar erro"""
        with pytest.raises(ValidationError, match="Nome é obrigatório"):
            ValidadorParticipante.validar_nome("")
        
        with pytest.raises(ValidationError, match="Nome é obrigatório"):
            ValidadorParticipante.validar_nome("   ")
        
        with pytest.raises(ValidationError, match="Nome é obrigatório"):
            ValidadorParticipante.validar_nome(None)
    
    def test_validar_nome_muito_curto(self):
        """Teste: Nome muito curto deve dar erro"""
        with pytest.raises(ValidationError, match="Nome deve ter pelo menos 2 caracteres"):
            ValidadorParticipante.validar_nome("A")
        
        with pytest.raises(ValidationError, match="Nome deve ter pelo menos 2 caracteres"):
            ValidadorParticipante.validar_nome(" B ")
    
    def test_validar_data_nascimento_none(self):
        """Teste: Data de nascimento None - LINHA 56 SEM COBERTURA"""
        with pytest.raises(ValidationError, match="Data de nascimento é obrigatória"):
            ValidadorParticipante.validar_data_nascimento(None)
    
    def test_validar_data_nascimento_string_valida(self):
        """Teste: Data de nascimento como string válida - LINHAS 59-62 SEM COBERTURA"""
        # String válida
        data_valida = ValidadorParticipante.validar_data_nascimento("1990-05-15")
        assert data_valida == datetime(1990, 5, 15)
    
    def test_validar_data_nascimento_string_invalida(self):
        """Teste: Data de nascimento string inválida - LINHAS 59-62 SEM COBERTURA"""
        with pytest.raises(ValidationError, match="Data de nascimento deve estar no formato YYYY-MM-DD"):
            ValidadorParticipante.validar_data_nascimento("15/05/1990")  # Formato errado
        
        with pytest.raises(ValidationError, match="Data de nascimento deve estar no formato YYYY-MM-DD"):
            ValidadorParticipante.validar_data_nascimento("1990-13-01")  # Mês inválido
        
        with pytest.raises(ValidationError, match="Data de nascimento deve estar no formato YYYY-MM-DD"):
            ValidadorParticipante.validar_data_nascimento("data_invalida")
    
    def test_validar_data_nascimento_datetime_valida(self):
        """Teste: Data de nascimento como datetime válida"""
        data_nascimento = datetime(1990, 5, 15)
        data_validada = ValidadorParticipante.validar_data_nascimento(data_nascimento)
        assert data_validada == data_nascimento
    
    def test_validar_data_nascimento_menor_idade(self):
        """Teste: Data de nascimento que resulta em menor de 18 anos"""
        data_menor = datetime.now() - timedelta(days=365*17)  # 17 anos
        
        with pytest.raises(ValidationError, match="Participante deve ter pelo menos 18 anos"):
            ValidadorParticipante.validar_data_nascimento(data_menor)
    
    def test_validar_data_nascimento_idade_exata_18_anos(self):
        """Teste: Data de nascimento que resulta em exatos 18 anos"""
        hoje = datetime.now()
        data_18_anos = datetime(hoje.year - 18, hoje.month, hoje.day)
        
        # Deve aceitar exatos 18 anos
        data_validada = ValidadorParticipante.validar_data_nascimento(data_18_anos)
        assert data_validada == data_18_anos

class TestValidadorLeilao:
    """Testes para ValidadorLeilao"""
    
    def test_validar_nome_valido(self):
        """Teste: Nome válido do leilão"""
        nome_limpo = ValidadorLeilao.validar_nome("  Leilão PlayStation 5  ")
        assert nome_limpo == "Leilão PlayStation 5"
    
    def test_validar_nome_vazio(self):
        """Teste: Nome vazio deve dar erro"""
        with pytest.raises(ValidationError, match="Nome do leilão é obrigatório"):
            ValidadorLeilao.validar_nome("")
        
        with pytest.raises(ValidationError, match="Nome do leilão é obrigatório"):
            ValidadorLeilao.validar_nome(None)
    
    def test_validar_nome_muito_curto(self):
        """Teste: Nome muito curto deve dar erro"""
        with pytest.raises(ValidationError, match="Nome do leilão deve ter pelo menos 3 caracteres"):
            ValidadorLeilao.validar_nome("AB")
    
    def test_validar_lance_minimo_none(self):
        """Teste: Lance mínimo None - LINHA 91 SEM COBERTURA"""
        with pytest.raises(ValidationError, match="Lance mínimo é obrigatório"):
            ValidadorLeilao.validar_lance_minimo(None)
    
    def test_validar_lance_minimo_valido(self):
        """Teste: Lance mínimo válido"""
        lance_float = ValidadorLeilao.validar_lance_minimo(100.50)
        assert lance_float == 100.50
        
        lance_int = ValidadorLeilao.validar_lance_minimo(200)
        assert lance_int == 200.0
        
        lance_string = ValidadorLeilao.validar_lance_minimo("150.75")
        assert lance_string == 150.75
    
    def test_validar_lance_minimo_invalido(self):
        """Teste: Lance mínimo inválido"""
        with pytest.raises(ValidationError, match="Lance mínimo deve ser um número"):
            ValidadorLeilao.validar_lance_minimo("abc")
        
        with pytest.raises(ValidationError, match="Lance mínimo deve ser maior que zero"):
            ValidadorLeilao.validar_lance_minimo(0)
        
        with pytest.raises(ValidationError, match="Lance mínimo deve ser maior que zero"):
            ValidadorLeilao.validar_lance_minimo(-10)
    
    def test_validar_datas_data_inicio_none(self):
        """Teste: Data de início None - LINHA 110 SEM COBERTURA"""
        with pytest.raises(ValidationError, match="Data de início é obrigatória"):
            ValidadorLeilao.validar_datas(None, datetime.now() + timedelta(days=1))
    
    def test_validar_datas_data_termino_none(self):
        """Teste: Data de término None - LINHA 113 SEM COBERTURA"""
        with pytest.raises(ValidationError, match="Data de término é obrigatória"):
            ValidadorLeilao.validar_datas(datetime.now() + timedelta(hours=1), None)
    
    def test_validar_datas_string_valida(self):
        """Teste: Datas como string válida"""
        data_inicio_str = "2025-12-01 10:00:00"
        data_termino_str = "2025-12-02 10:00:00"
        
        data_inicio, data_termino = ValidadorLeilao.validar_datas(
            data_inicio_str, data_termino_str, permitir_passado=True
        )
        
        assert data_inicio == datetime(2025, 12, 1, 10, 0, 0)
        assert data_termino == datetime(2025, 12, 2, 10, 0, 0)
    
    def test_validar_datas_string_inicio_invalida(self):
        """Teste: Data início string inválida - LINHAS 117-120 SEM COBERTURA"""
        with pytest.raises(ValidationError, match="Data de início deve estar no formato YYYY-MM-DD HH:MM:SS"):
            ValidadorLeilao.validar_datas(
                "01/12/2025 10:00:00",  # Formato errado
                "2025-12-02 10:00:00",
                permitir_passado=True
            )
        
        with pytest.raises(ValidationError, match="Data de início deve estar no formato YYYY-MM-DD HH:MM:SS"):
            ValidadorLeilao.validar_datas(
                "2025-13-01 10:00:00",  # Mês inválido
                "2025-12-02 10:00:00",
                permitir_passado=True
            )
        
        with pytest.raises(ValidationError, match="Data de início deve estar no formato YYYY-MM-DD HH:MM:SS"):
            ValidadorLeilao.validar_datas(
                "data_invalida",
                "2025-12-02 10:00:00",
                permitir_passado=True
            )
    
    def test_validar_datas_string_termino_invalida(self):
        """Teste: Data término string inválida - LINHAS 123-126 SEM COBERTURA"""
        with pytest.raises(ValidationError, match="Data de término deve estar no formato YYYY-MM-DD HH:MM:SS"):
            ValidadorLeilao.validar_datas(
                "2025-12-01 10:00:00",
                "02/12/2025 10:00:00",  # Formato errado
                permitir_passado=True
            )
        
        with pytest.raises(ValidationError, match="Data de término deve estar no formato YYYY-MM-DD HH:MM:SS"):
            ValidadorLeilao.validar_datas(
                "2025-12-01 10:00:00",
                "2025-13-02 10:00:00",  # Mês inválido
                permitir_passado=True
            )
    
    def test_validar_datas_datetime_valida(self):
        """Teste: Datas como datetime válidas"""
        data_inicio = datetime(2025, 12, 1, 10, 0, 0)
        data_termino = datetime(2025, 12, 2, 10, 0, 0)
        
        inicio_validada, termino_validada = ValidadorLeilao.validar_datas(
            data_inicio, data_termino, permitir_passado=True
        )
        
        assert inicio_validada == data_inicio
        assert termino_validada == data_termino
    
    def test_validar_datas_termino_antes_inicio(self):
        """Teste: Data de término antes da data de início"""
        data_inicio = datetime(2025, 12, 2, 10, 0, 0)
        data_termino = datetime(2025, 12, 1, 10, 0, 0)  # Antes do início
        
        with pytest.raises(ValidationError, match="Data de término deve ser posterior à data de início"):
            ValidadorLeilao.validar_datas(data_inicio, data_termino, permitir_passado=True)
    
    def test_validar_datas_inicio_no_passado(self):
        """Teste: Data de início no passado sem permitir - LINHA 136 SEM COBERTURA"""
        data_passado = datetime.now() - timedelta(hours=1)
        data_futura = datetime.now() + timedelta(days=1)
        
        with pytest.raises(ValidationError, match="Data de início não pode ser no passado"):
            ValidadorLeilao.validar_datas(data_passado, data_futura, permitir_passado=False)
    
    def test_validar_datas_inicio_no_passado_permitido(self):
        """Teste: Data de início no passado com permitir_passado=True"""
        data_passado = datetime.now() - timedelta(hours=1)
        data_futura = datetime.now() + timedelta(days=1)
        
        # Deve funcionar quando permitir_passado=True
        inicio, termino = ValidadorLeilao.validar_datas(data_passado, data_futura, permitir_passado=True)
        assert inicio == data_passado
        assert termino == data_futura

class TestValidadorLance:
    """Testes para ValidadorLance"""
    
    def test_validar_valor_none(self):
        """Teste: Valor None deve dar erro"""
        with pytest.raises(ValidationError, match="Valor do lance é obrigatório"):
            ValidadorLance.validar_valor(None)
    
    def test_validar_valor_valido(self):
        """Teste: Valor válido"""
        valor_float = ValidadorLance.validar_valor(150.75)
        assert valor_float == 150.75
        
        valor_int = ValidadorLance.validar_valor(200)
        assert valor_int == 200.0
        
        valor_string = ValidadorLance.validar_valor("300.50")
        assert valor_string == 300.50
    
    def test_validar_valor_string_invalida(self):
        """Teste: Valor string inválida - LINHAS 149-150 SEM COBERTURA"""
        with pytest.raises(ValidationError, match="Valor do lance deve ser um número"):
            ValidadorLance.validar_valor("abc")
        
        with pytest.raises(ValidationError, match="Valor do lance deve ser um número"):
            ValidadorLance.validar_valor("100,50")  # Vírgula ao invés de ponto
        
        with pytest.raises(ValidationError, match="Valor do lance deve ser um número"):
            ValidadorLance.validar_valor("R$ 100")
    
    def test_validar_valor_tipo_invalido(self):
        """Teste: Valor tipo inválido - LINHAS 149-150 SEM COBERTURA (TypeError)"""
        with pytest.raises(ValidationError, match="Valor do lance deve ser um número"):
            ValidadorLance.validar_valor([100])  # Lista - TypeError
        
        with pytest.raises(ValidationError, match="Valor do lance deve ser um número"):
            ValidadorLance.validar_valor({"valor": 100})  # Dict - TypeError
    
    def test_validar_valor_zero_negativo(self):
        """Teste: Valor zero ou negativo"""
        with pytest.raises(ValidationError, match="Valor do lance deve ser maior que zero"):
            ValidadorLance.validar_valor(0)
        
        with pytest.raises(ValidationError, match="Valor do lance deve ser maior que zero"):
            ValidadorLance.validar_valor(-10.50)

class TestValidationError:
    """Testes para a classe ValidationError"""
    
    def test_validation_error_herda_exception(self):
        """Teste: ValidationError deve herdar de Exception"""
        erro = ValidationError("Teste de erro")
        assert isinstance(erro, Exception)
        assert str(erro) == "Teste de erro"
    
    def test_validation_error_pode_ser_lancada(self):
        """Teste: ValidationError pode ser lançada e capturada"""
        with pytest.raises(ValidationError) as exc_info:
            raise ValidationError("Erro customizado")
        
        assert str(exc_info.value) == "Erro customizado"