from datetime import datetime
from typing import List, Optional, Tuple
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from src.models import Leilao, StatusLeilao, Lance, Participante
from src.repositories import db_config
from src.utils import ValidadorLeilao, ValidationError

class LeilaoService:
    def __init__(self):
        self.db_config = db_config
    
    def criar_leilao(self, nome: str, lance_minimo: float, data_inicio: datetime, data_termino: datetime, permitir_passado: bool = False) -> Leilao:
        """
        Cria um novo leilão no estado INATIVO
        """
        session = self.db_config.get_session()
        try:
            # Validações
            nome = ValidadorLeilao.validar_nome(nome)
            lance_minimo = ValidadorLeilao.validar_lance_minimo(lance_minimo)
            data_inicio, data_termino = ValidadorLeilao.validar_datas(data_inicio, data_termino, permitir_passado)
            
            # Criar leilão
            leilao = Leilao(
                nome=nome,
                lance_minimo=lance_minimo,
                data_inicio=data_inicio,
                data_termino=data_termino,
                status=StatusLeilao.INATIVO
            )
            
            session.add(leilao)
            session.commit()
            session.refresh(leilao)
            
            return leilao
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def atualizar_leilao(self, leilao_id: int, nome: str = None, lance_minimo: float = None, 
                        data_inicio: datetime = None, data_termino: datetime = None) -> Leilao:
        """
        Atualiza um leilão - APENAS se estiver INATIVO
        Regra: Um Leilão ABERTO ou FINALIZADO não pode sofrer alterações
        """
        session = self.db_config.get_session()
        try:
            leilao = session.query(Leilao).filter(Leilao.id == leilao_id).first()
            
            if not leilao:
                raise ValidationError(f"Leilão com ID {leilao_id} não encontrado")
            
            # Verificar se pode ser alterado
            if leilao.status in [StatusLeilao.ABERTO, StatusLeilao.FINALIZADO]:
                raise ValidationError(f"Leilão no estado {leilao.status.value} não pode ser alterado")
            
            # Atualizar campos se fornecidos
            if nome is not None:
                leilao.nome = ValidadorLeilao.validar_nome(nome)
            
            if lance_minimo is not None:
                leilao.lance_minimo = ValidadorLeilao.validar_lance_minimo(lance_minimo)
            
            if data_inicio is not None or data_termino is not None:
                nova_data_inicio = data_inicio if data_inicio is not None else leilao.data_inicio
                nova_data_termino = data_termino if data_termino is not None else leilao.data_termino
                
                nova_data_inicio, nova_data_termino = ValidadorLeilao.validar_datas(nova_data_inicio, nova_data_termino)
                leilao.data_inicio = nova_data_inicio
                leilao.data_termino = nova_data_termino
            
            session.commit()
            session.refresh(leilao)
            
            return leilao
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def excluir_leilao(self, leilao_id: int) -> bool:
        """
        Exclui um leilão - APENAS se estiver INATIVO
        Regra: Um Leilão ABERTO ou FINALIZADO não pode ser excluído
        """
        session = self.db_config.get_session()
        try:
            leilao = session.query(Leilao).filter(Leilao.id == leilao_id).first()
            
            if not leilao:
                raise ValidationError(f"Leilão com ID {leilao_id} não encontrado")
            
            # Verificar se pode ser excluído
            if leilao.status in [StatusLeilao.ABERTO, StatusLeilao.FINALIZADO]:
                raise ValidationError(f"Leilão no estado {leilao.status.value} não pode ser excluído")
            
            session.delete(leilao)
            session.commit()
            
            return True
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def atualizar_status_leiloes(self, enviar_emails: bool = True) -> dict:
        """
        Atualiza o status de todos os leilões baseado na data/hora atual
        - INATIVO → ABERTO (quando atingir data de início E ainda não passou data de término)
        - INATIVO → EXPIRADO (quando já passou data de término E não tem lances)
        - ABERTO → FINALIZADO (quando atingir data de término E tiver lances)
        - ABERTO → EXPIRADO (quando atingir data de término E NÃO tiver lances)
        
        Se enviar_emails=True, envia email automático para vencedores
        """
        session = self.db_config.get_session()
        try:
            agora = datetime.now()
            resultado = {
                'abertos': 0,
                'finalizados': 0,
                'expirados': 0,
                'emails_enviados': 0
            }
            
            # Buscar leilões que podem mudar de status
            leiloes_para_processar = session.query(Leilao).filter(
                Leilao.status.in_([StatusLeilao.INATIVO, StatusLeilao.ABERTO])
            ).all()
            
            leiloes_finalizados = []  # Para enviar emails depois
            
            for leilao in leiloes_para_processar:
                if leilao.status == StatusLeilao.INATIVO:
                    # Leilão INATIVO - verificar se deve abrir ou expirar
                    if leilao.data_termino <= agora:
                        # Já passou da data de término - verificar se tem lances
                        tem_lances = session.query(Lance).filter(Lance.leilao_id == leilao.id).count() > 0
                        
                        if tem_lances:
                            # Tem lances → FINALIZADO (pula o estado ABERTO)
                            leilao.status = StatusLeilao.FINALIZADO
                            # Definir vencedor (maior lance)
                            lance_vencedor = session.query(Lance).filter(Lance.leilao_id == leilao.id).order_by(Lance.valor.desc()).first()
                            if lance_vencedor:
                                leilao.participante_vencedor_id = lance_vencedor.participante_id
                                leiloes_finalizados.append((leilao, lance_vencedor))
                            resultado['finalizados'] += 1
                        else:
                            # Não tem lances → EXPIRADO
                            leilao.status = StatusLeilao.EXPIRADO
                            resultado['expirados'] += 1
                    elif leilao.data_inicio <= agora:
                        # Chegou a data de início mas ainda não terminou - ABERTO
                        leilao.status = StatusLeilao.ABERTO
                        resultado['abertos'] += 1
                
                elif leilao.status == StatusLeilao.ABERTO:
                    # Leilão ABERTO - verificar se deve finalizar ou expirar
                    if leilao.data_termino <= agora:
                        # Chegou a data de término - verificar se tem lances
                        tem_lances = session.query(Lance).filter(Lance.leilao_id == leilao.id).count() > 0
                        
                        if tem_lances:
                            # Tem lances → FINALIZADO
                            leilao.status = StatusLeilao.FINALIZADO
                            # Definir vencedor (maior lance)
                            lance_vencedor = session.query(Lance).filter(Lance.leilao_id == leilao.id).order_by(Lance.valor.desc()).first()
                            if lance_vencedor:
                                leilao.participante_vencedor_id = lance_vencedor.participante_id
                                leiloes_finalizados.append((leilao, lance_vencedor))
                            resultado['finalizados'] += 1
                        else:
                            # Não tem lances → EXPIRADO
                            leilao.status = StatusLeilao.EXPIRADO
                            resultado['expirados'] += 1
            
            session.commit()
            
            # Enviar emails para vencedores (se solicitado)
            if enviar_emails and leiloes_finalizados:
                resultado['emails_enviados'] = self._enviar_emails_vencedores(leiloes_finalizados)
            
            return resultado
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def _enviar_emails_vencedores(self, leiloes_finalizados: list) -> int:
        """
        Envia emails para vencedores de leilões recém-finalizados
        """
        try:
            from .email_service import EmailService
            email_service = EmailService()  # Modo teste por padrão
            
            emails_enviados = 0
            session = self.db_config.get_session()
            
            for leilao, lance_vencedor in leiloes_finalizados:
                # Buscar dados do vencedor
                participante_vencedor = session.query(Participante).filter(
                    Participante.id == lance_vencedor.participante_id
                ).first()
                
                if participante_vencedor:
                    sucesso = email_service.enviar_email_vencedor(
                        leilao, participante_vencedor, lance_vencedor.valor
                    )
                    if sucesso:
                        emails_enviados += 1
            
            session.close()
            return emails_enviados
            
        except Exception as e:
            print(f"Erro ao enviar emails: {e}")
            return 0
    
    def listar_leiloes(self, status: StatusLeilao = None, data_inicio_min: datetime = None, 
                      data_inicio_max: datetime = None, data_termino_min: datetime = None, 
                      data_termino_max: datetime = None) -> List[Leilao]:
        """
        Lista leilões com filtros opcionais
        - Filtro por status
        - Filtro por intervalo de datas (início e término)
        """
        session = self.db_config.get_session()
        try:
            query = session.query(Leilao)
            
            # Filtro por status
            if status:
                query = query.filter(Leilao.status == status)
            
            # Filtros de data de início
            if data_inicio_min:
                query = query.filter(Leilao.data_inicio >= data_inicio_min)
            
            if data_inicio_max:
                query = query.filter(Leilao.data_inicio <= data_inicio_max)
            
            # Filtros de data de término
            if data_termino_min:
                query = query.filter(Leilao.data_termino >= data_termino_min)
            
            if data_termino_max:
                query = query.filter(Leilao.data_termino <= data_termino_max)
            
            # Ordenar por data de início
            leiloes = query.order_by(Leilao.data_inicio.desc()).all()
            
            return leiloes
            
        finally:
            session.close()
    
    def obter_leilao_por_id(self, leilao_id: int) -> Optional[Leilao]:
        """
        Obtém um leilão específico por ID
        """
        session = self.db_config.get_session()
        try:
            leilao = session.query(Leilao).filter(Leilao.id == leilao_id).first()
            return leilao
        finally:
            session.close()
    
    def pode_receber_lances(self, leilao_id: int) -> Tuple[bool, str]:
        """
        Verifica se um leilão pode receber lances
        Retorna (pode_receber, motivo)
        """
        # Primeiro atualizar status dos leilões
        self.atualizar_status_leiloes()
        
        session = self.db_config.get_session()
        try:
            leilao = session.query(Leilao).filter(Leilao.id == leilao_id).first()
            
            if not leilao:
                return False, "Leilão não encontrado"
            
            if leilao.status != StatusLeilao.ABERTO:
                return False, f"Leilão está no estado {leilao.status.value}, apenas leilões ABERTOS podem receber lances"
            
            return True, "Leilão pode receber lances"
            
        finally:
            session.close()
    
    def obter_estatisticas_leilao(self, leilao_id: int) -> dict:
        """
        Obtém estatísticas de um leilão específico
        - Total de lances
        - Maior lance
        - Menor lance
        - Participantes únicos
        """
        session = self.db_config.get_session()
        try:
            leilao = session.query(Leilao).filter(Leilao.id == leilao_id).first()
            
            if not leilao:
                raise ValidationError(f"Leilão com ID {leilao_id} não encontrado")
            
            lances = session.query(Lance).filter(Lance.leilao_id == leilao_id).all()
            
            if not lances:
                return {
                    'total_lances': 0,
                    'maior_lance': None,
                    'menor_lance': None,
                    'participantes_unicos': 0,
                    'lance_atual': leilao.lance_minimo
                }
            
            valores_lances = [lance.valor for lance in lances]
            participantes_unicos = len(set(lance.participante_id for lance in lances))
            
            return {
                'total_lances': len(lances),
                'maior_lance': max(valores_lances),
                'menor_lance': min(valores_lances),
                'participantes_unicos': participantes_unicos,
                'lance_atual': max(valores_lances)
            }
            
        finally:
            session.close()
    
    def leiloes_que_precisa_notificar(self) -> List[Leilao]:
        """
        Retorna leilões que acabaram de ser finalizados e precisam notificar o vencedor
        (Para implementar o envio de email)
        """
        session = self.db_config.get_session()
        try:
            # Buscar leilões finalizados que têm vencedor
            leiloes = session.query(Leilao).filter(
                and_(
                    Leilao.status == StatusLeilao.FINALIZADO,
                    Leilao.participante_vencedor_id.isnot(None)
                )
            ).all()
            
            return leiloes
            
        finally:
            session.close()