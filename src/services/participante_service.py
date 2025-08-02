from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from src.models import Participante, Lance
from src.repositories import db_config
from src.utils import ValidadorParticipante, ValidationError

class ParticipanteService:
    def __init__(self):
        self.db_config = db_config
    
    def criar_participante(self, cpf: str, nome: str, email: str, data_nascimento: datetime) -> Participante:
        """
        Cria um novo participante com validações completas
        """
        session = self.db_config.get_session()
        try:
            # Validações
            cpf_limpo = ValidadorParticipante.validar_cpf(cpf)
            nome_limpo = ValidadorParticipante.validar_nome(nome)
            email_limpo = ValidadorParticipante.validar_email(email)
            data_nascimento_validada = ValidadorParticipante.validar_data_nascimento(data_nascimento)
            
            # Verificar se CPF já existe
            cpf_existente = session.query(Participante).filter(Participante.cpf == cpf_limpo).first()
            if cpf_existente:
                raise ValidationError(f"CPF {cpf_limpo} já está cadastrado")
            
            # Verificar se email já existe
            email_existente = session.query(Participante).filter(Participante.email == email_limpo).first()
            if email_existente:
                raise ValidationError(f"Email {email_limpo} já está cadastrado")
            
            # Criar participante
            participante = Participante(
                cpf=cpf_limpo,
                nome=nome_limpo,
                email=email_limpo,
                data_nascimento=data_nascimento_validada
            )
            
            session.add(participante)
            session.commit()
            session.refresh(participante)
            
            return participante
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def atualizar_participante(self, participante_id: int, cpf: str = None, nome: str = None, 
                              email: str = None, data_nascimento: datetime = None) -> Participante:
        """
        Atualiza dados de um participante
        REGRA: Caso o participante tenha efetuado algum Lance, o participante não pode ser alterado
        """
        session = self.db_config.get_session()
        try:
            participante = session.query(Participante).filter(Participante.id == participante_id).first()
            
            if not participante:
                raise ValidationError(f"Participante com ID {participante_id} não encontrado")
            
            # Verificar se participante tem lances
            tem_lances = session.query(Lance).filter(Lance.participante_id == participante_id).count() > 0
            if tem_lances:
                raise ValidationError("Participante que já efetuou lances não pode ser alterado")
            
            # Atualizar campos se fornecidos
            if cpf is not None:
                cpf_limpo = ValidadorParticipante.validar_cpf(cpf)
                # Verificar se novo CPF já existe (exceto o próprio participante)
                cpf_existente = session.query(Participante).filter(
                    and_(Participante.cpf == cpf_limpo, Participante.id != participante_id)
                ).first()
                if cpf_existente:
                    raise ValidationError(f"CPF {cpf_limpo} já está cadastrado para outro participante")
                participante.cpf = cpf_limpo
            
            if nome is not None:
                participante.nome = ValidadorParticipante.validar_nome(nome)
            
            if email is not None:
                email_limpo = ValidadorParticipante.validar_email(email)
                # Verificar se novo email já existe (exceto o próprio participante)
                email_existente = session.query(Participante).filter(
                    and_(Participante.email == email_limpo, Participante.id != participante_id)
                ).first()
                if email_existente:
                    raise ValidationError(f"Email {email_limpo} já está cadastrado para outro participante")
                participante.email = email_limpo
            
            if data_nascimento is not None:
                participante.data_nascimento = ValidadorParticipante.validar_data_nascimento(data_nascimento)
            
            session.commit()
            session.refresh(participante)
            
            return participante
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def excluir_participante(self, participante_id: int) -> bool:
        """
        Exclui um participante
        REGRA: Caso o participante tenha efetuado algum Lance, o participante não pode ser excluído
        """
        session = self.db_config.get_session()
        try:
            participante = session.query(Participante).filter(Participante.id == participante_id).first()
            
            if not participante:
                raise ValidationError(f"Participante com ID {participante_id} não encontrado")
            
            # Verificar se participante tem lances
            tem_lances = session.query(Lance).filter(Lance.participante_id == participante_id).count() > 0
            if tem_lances:
                raise ValidationError("Participante que já efetuou lances não pode ser excluído")
            
            session.delete(participante)
            session.commit()
            
            return True
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def obter_participante_por_id(self, participante_id: int) -> Optional[Participante]:
        """
        Obtém um participante específico por ID
        """
        session = self.db_config.get_session()
        try:
            participante = session.query(Participante).filter(Participante.id == participante_id).first()
            return participante
        finally:
            session.close()
    
    def obter_participante_por_cpf(self, cpf: str) -> Optional[Participante]:
        """
        Obtém um participante específico por CPF
        """
        session = self.db_config.get_session()
        try:
            cpf_limpo = ValidadorParticipante.validar_cpf(cpf)
            participante = session.query(Participante).filter(Participante.cpf == cpf_limpo).first()
            return participante
        finally:
            session.close()
    
    def obter_participante_por_email(self, email: str) -> Optional[Participante]:
        """
        Obtém um participante específico por email
        """
        session = self.db_config.get_session()
        try:
            email_limpo = ValidadorParticipante.validar_email(email)
            participante = session.query(Participante).filter(Participante.email == email_limpo).first()
            return participante
        finally:
            session.close()
    
    def listar_participantes(self, nome_parcial: str = None, tem_lances: bool = None) -> List[Participante]:
        """
        Lista participantes com filtros opcionais
        - nome_parcial: busca por nome que contenha o texto
        - tem_lances: True para apenas participantes com lances, False para sem lances, None para todos
        """
        session = self.db_config.get_session()
        try:
            query = session.query(Participante)
            
            # Filtro por nome parcial
            if nome_parcial:
                query = query.filter(Participante.nome.ilike(f"%{nome_parcial}%"))
            
            # Filtro por ter lances ou não
            if tem_lances is not None:
                if tem_lances:
                    # Apenas participantes que têm lances
                    query = query.filter(
                        Participante.id.in_(
                            session.query(Lance.participante_id).distinct()
                        )
                    )
                else:
                    # Apenas participantes que NÃO têm lances
                    query = query.filter(
                        ~Participante.id.in_(
                            session.query(Lance.participante_id).distinct()
                        )
                    )
            
            # Ordenar por nome
            participantes = query.order_by(Participante.nome).all()
            
            return participantes
            
        finally:
            session.close()
    
    def verificar_pode_alterar_excluir(self, participante_id: int) -> tuple[bool, str]:
        """
        Verifica se um participante pode ser alterado ou excluído
        Retorna (pode_alterar_excluir, motivo)
        """
        session = self.db_config.get_session()
        try:
            participante = session.query(Participante).filter(Participante.id == participante_id).first()
            
            if not participante:
                return False, "Participante não encontrado"
            
            # Verificar se tem lances
            quantidade_lances = session.query(Lance).filter(Lance.participante_id == participante_id).count()
            
            if quantidade_lances > 0:
                return False, f"Participante possui {quantidade_lances} lance(s) e não pode ser alterado/excluído"
            
            return True, "Participante pode ser alterado/excluído"
            
        finally:
            session.close()
    
    def obter_estatisticas_participante(self, participante_id: int) -> dict:
        """
        Obtém estatísticas de um participante específico
        - Total de lances
        - Total gasto em lances
        - Leilões participados
        - Leilões vencidos
        """
        session = self.db_config.get_session()
        try:
            participante = session.query(Participante).filter(Participante.id == participante_id).first()
            
            if not participante:
                raise ValidationError(f"Participante com ID {participante_id} não encontrado")
            
            # Buscar todos os lances do participante
            lances = session.query(Lance).filter(Lance.participante_id == participante_id).all()
            
            if not lances:
                return {
                    'total_lances': 0,
                    'total_gasto': 0.0,
                    'leiloes_participados': 0,
                    'leiloes_vencidos': 0,
                    'maior_lance': None,
                    'menor_lance': None
                }
            
            # Calcular estatísticas
            valores_lances = [lance.valor for lance in lances]
            leiloes_participados = len(set(lance.leilao_id for lance in lances))
            
            # Contar leilões vencidos
            from src.models import Leilao
            leiloes_vencidos = session.query(Leilao).filter(
                Leilao.participante_vencedor_id == participante_id
            ).count()
            
            return {
                'total_lances': len(lances),
                'total_gasto': sum(valores_lances),
                'leiloes_participados': leiloes_participados,
                'leiloes_vencidos': leiloes_vencidos,
                'maior_lance': max(valores_lances),
                'menor_lance': min(valores_lances)
            }
            
        finally:
            session.close()
    
    def validar_cpf_disponivel(self, cpf: str, excluir_participante_id: int = None) -> bool:
        """
        Verifica se um CPF está disponível para uso
        excluir_participante_id: ID do participante a ser excluído da verificação (para atualizações)
        """
        session = self.db_config.get_session()
        try:
            cpf_limpo = ValidadorParticipante.validar_cpf(cpf)
            
            query = session.query(Participante).filter(Participante.cpf == cpf_limpo)
            
            if excluir_participante_id:
                query = query.filter(Participante.id != excluir_participante_id)
            
            return query.first() is None
            
        finally:
            session.close()
    
    def validar_email_disponivel(self, email: str, excluir_participante_id: int = None) -> bool:
        """
        Verifica se um email está disponível para uso
        excluir_participante_id: ID do participante a ser excluído da verificação (para atualizações)
        """
        session = self.db_config.get_session()
        try:
            email_limpo = ValidadorParticipante.validar_email(email)
            
            query = session.query(Participante).filter(Participante.email == email_limpo)
            
            if excluir_participante_id:
                query = query.filter(Participante.id != excluir_participante_id)
            
            return query.first() is None
            
        finally:
            session.close()
    
    def buscar_participantes_por_idade(self, idade_minima: int = None, idade_maxima: int = None) -> List[Participante]:
        """
        Busca participantes por faixa etária
        """
        session = self.db_config.get_session()
        try:
            hoje = datetime.now()
            query = session.query(Participante)
            
            if idade_minima is not None:
                # Data de nascimento deve ser no máximo (hoje - idade_minima) anos
                # Para idade_minima=30, queremos pessoas nascidas em (hoje.year - 30) ou antes
                data_maxima_nascimento = datetime(hoje.year - idade_minima, hoje.month, hoje.day)
                query = query.filter(Participante.data_nascimento <= data_maxima_nascimento)
            
            if idade_maxima is not None:
                # Data de nascimento deve ser no mínimo (hoje - idade_maxima - 1) anos
                # Para idade_maxima=32, queremos pessoas nascidas após (hoje.year - 33)
                data_minima_nascimento = datetime(hoje.year - idade_maxima - 1, hoje.month, hoje.day)
                query = query.filter(Participante.data_nascimento > data_minima_nascimento)
            
            return query.order_by(Participante.data_nascimento.desc()).all()
            
        finally:
            session.close()