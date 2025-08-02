import re
from datetime import datetime
from email_validator import validate_email, EmailNotValidError

class ValidationError(Exception):
    """Exceção customizada para erros de validação"""
    pass

class ValidadorParticipante:
    @staticmethod
    def validar_cpf(cpf):
        """Valida formato do CPF (somente números, 11 dígitos)"""
        if not cpf:
            raise ValidationError("CPF é obrigatório")
        
        # Remove caracteres não numéricos
        cpf_limpo = re.sub(r'\D', '', cpf)
        
        if len(cpf_limpo) != 11:
            raise ValidationError("CPF deve ter 11 dígitos")
        
        # Verifica se não são todos os dígitos iguais
        if cpf_limpo == cpf_limpo[0] * 11:
            raise ValidationError("CPF inválido")
        
        return cpf_limpo
    
    @staticmethod
    def validar_email(email):
        """Valida formato do email"""
        if not email:
            raise ValidationError("Email é obrigatório")
        
        try:
            # Valida e normaliza o email
            validated_email = validate_email(email)
            return validated_email.normalized  # Usar .normalized ao invés de .email
        except EmailNotValidError:
            raise ValidationError("Email inválido")
    
    @staticmethod
    def validar_nome(nome):
        """Valida nome do participante"""
        if not nome or not nome.strip():
            raise ValidationError("Nome é obrigatório")
        
        if len(nome.strip()) < 2:
            raise ValidationError("Nome deve ter pelo menos 2 caracteres")
        
        return nome.strip()
    
    @staticmethod
    def validar_data_nascimento(data_nascimento):
        """Valida data de nascimento"""
        if not data_nascimento:
            raise ValidationError("Data de nascimento é obrigatória")
        
        if isinstance(data_nascimento, str):
            try:
                data_nascimento = datetime.strptime(data_nascimento, "%Y-%m-%d")
            except ValueError:
                raise ValidationError("Data de nascimento deve estar no formato YYYY-MM-DD")
        
        # Verifica se a pessoa tem pelo menos 18 anos
        hoje = datetime.now()
        idade = hoje.year - data_nascimento.year
        if hoje.month < data_nascimento.month or (hoje.month == data_nascimento.month and hoje.day < data_nascimento.day):
            idade -= 1
        
        if idade < 18:
            raise ValidationError("Participante deve ter pelo menos 18 anos")
        
        return data_nascimento

class ValidadorLeilao:
    @staticmethod
    def validar_nome(nome):
        """Valida nome do leilão"""
        if not nome or not nome.strip():
            raise ValidationError("Nome do leilão é obrigatório")
        
        if len(nome.strip()) < 3:
            raise ValidationError("Nome do leilão deve ter pelo menos 3 caracteres")
        
        return nome.strip()
    
    @staticmethod
    def validar_lance_minimo(lance_minimo):
        """Valida lance mínimo"""
        if lance_minimo is None:
            raise ValidationError("Lance mínimo é obrigatório")
        
        try:
            lance_minimo = float(lance_minimo)
        except (ValueError, TypeError):
            raise ValidationError("Lance mínimo deve ser um número")
        
        if lance_minimo <= 0:
            raise ValidationError("Lance mínimo deve ser maior que zero")
        
        return lance_minimo
    
    @staticmethod
    def validar_datas(data_inicio, data_termino, permitir_passado=False):
        """
        Valida datas de início e término do leilão
        permitir_passado: usado para testes, permite datas no passado
        """
        if not data_inicio:
            raise ValidationError("Data de início é obrigatória")
        
        if not data_termino:
            raise ValidationError("Data de término é obrigatória")
        
        # Converte strings para datetime se necessário
        if isinstance(data_inicio, str):
            try:
                data_inicio = datetime.strptime(data_inicio, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                raise ValidationError("Data de início deve estar no formato YYYY-MM-DD HH:MM:SS")
        
        if isinstance(data_termino, str):
            try:
                data_termino = datetime.strptime(data_termino, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                raise ValidationError("Data de término deve estar no formato YYYY-MM-DD HH:MM:SS")
        
        # Valida se data de término é posterior à data de início
        if data_termino <= data_inicio:
            raise ValidationError("Data de término deve ser posterior à data de início")
        
        # Valida se data de início não é no passado (APENAS em produção)
        if not permitir_passado:
            agora = datetime.now()
            if data_inicio < agora:
                raise ValidationError("Data de início não pode ser no passado")
        
        return data_inicio, data_termino

class ValidadorLance:
    @staticmethod
    def validar_valor(valor):
        """Valida valor do lance"""
        if valor is None:
            raise ValidationError("Valor do lance é obrigatório")
        
        try:
            valor = float(valor)
        except (ValueError, TypeError):
            raise ValidationError("Valor do lance deve ser um número")
        
        if valor <= 0:
            raise ValidationError("Valor do lance deve ser maior que zero")
        
        return valor