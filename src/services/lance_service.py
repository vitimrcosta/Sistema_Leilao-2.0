from datetime import datetime
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from src.models import Lance, Leilao, Participante, StatusLeilao
from src.repositories import db_config
from src.utils import ValidadorLance, ValidationError

class LanceService:
    def __init__(self):
        self.db_config = db_config
    
    def criar_lance(self, participante_id: int, leilao_id: int, valor: float) -> Lance:
        """
        Cria um novo lance com todas as validações das regras de negócio
        
        REGRAS:
        a. Os lances são possíveis somente para participantes previamente cadastrados
        b. Para que lances possam ser realizados em um leilão, este deve estar no estado ABERTO
        c. Cada participante pode efetuar quantos lances desejar, para um dado leilão
        d. Não é possível alterar um lance
        e. Um lance sempre deve ser maior que o último lance para um dado leilão
        f. Um mesmo participante não pode efetuar dois lances em sequência para um mesmo leilão
        g. Cada lance efetuado deve observar o lance mínimo de um dado leilão
        """
        session = self.db_config.get_session()
        try:
            # Validar valor do lance
            valor = ValidadorLance.validar_valor(valor)
            
            # Verificar se participante existe
            participante = session.query(Participante).filter(Participante.id == participante_id).first()
            if not participante:
                raise ValidationError(f"Participante com ID {participante_id} não encontrado")
            
            # Verificar se leilão existe
            leilao = session.query(Leilao).filter(Leilao.id == leilao_id).first()
            if not leilao:
                raise ValidationError(f"Leilão com ID {leilao_id} não encontrado")
            
            # REGRA b: Leilão deve estar ABERTO
            if leilao.status != StatusLeilao.ABERTO:
                raise ValidationError(f"Lances só podem ser realizados em leilões ABERTOS. Status atual: {leilao.status.value}")
            
            # REGRA g: Lance deve ser >= lance mínimo
            if valor < leilao.lance_minimo:
                raise ValidationError(f"Lance deve ser pelo menos R$ {leilao.lance_minimo:.2f}")
            
            # Buscar último lance do leilão
            ultimo_lance = session.query(Lance).filter(Lance.leilao_id == leilao_id).order_by(Lance.data_lance.desc()).first()
            
            if ultimo_lance:
                # REGRA e: Lance deve ser maior que o último lance
                if valor <= ultimo_lance.valor:
                    raise ValidationError(f"Lance deve ser maior que R$ {ultimo_lance.valor:.2f}")
                
                # REGRA f: Mesmo participante não pode dar dois lances seguidos
                if ultimo_lance.participante_id == participante_id:
                    raise ValidationError("O mesmo participante não pode efetuar dois lances consecutivos")
            
            # Criar lance
            lance = Lance(
                valor=valor,
                leilao_id=leilao_id,
                participante_id=participante_id,
                data_lance=datetime.now()
            )
            
            session.add(lance)
            session.commit()
            session.refresh(lance)
            
            return lance
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def obter_lances_leilao(self, leilao_id: int, ordem_crescente: bool = True) -> List[Lance]:
        """
        Obtém lista de lances de um leilão em ordem crescente de valor
        
        REGRA k: Feature importante - permitir acesso à lista de lances de um determinado leilão,
        em ordem crescente de valor
        """
        session = self.db_config.get_session()
        try:
            # Verificar se leilão existe
            leilao = session.query(Leilao).filter(Leilao.id == leilao_id).first()
            if not leilao:
                raise ValidationError(f"Leilão com ID {leilao_id} não encontrado")
            
            # Buscar lances
            query = session.query(Lance).filter(Lance.leilao_id == leilao_id)
            
            if ordem_crescente:
                query = query.order_by(Lance.valor.asc())
            else:
                query = query.order_by(Lance.valor.desc())
            
            lances = query.all()
            return lances
            
        finally:
            session.close()
    
    def obter_maior_menor_lance(self, leilao_id: int) -> dict:
        """
        Obtém o maior e menor lance de um leilão
        
        REGRA l: Os usuários precisam saber qual é o maior e o menor lance efetuado
        """
        session = self.db_config.get_session()
        try:
            # Verificar se leilão existe
            leilao = session.query(Leilao).filter(Leilao.id == leilao_id).first()
            if not leilao:
                raise ValidationError(f"Leilão com ID {leilao_id} não encontrado")  # pragma: no cover
            
            # Buscar lances
            lances = session.query(Lance).filter(Lance.leilao_id == leilao_id).all()
            
            if not lances:
                return {
                    'maior_lance': None,
                    'menor_lance': None,
                    'lance_atual': leilao.lance_minimo,
                    'total_lances': 0
                }
            
            valores = [lance.valor for lance in lances]
            
            return {
                'maior_lance': max(valores),
                'menor_lance': min(valores),
                'lance_atual': max(valores),
                'total_lances': len(lances)
            }
            
        finally:
            session.close()
    
    def obter_lance_por_id(self, lance_id: int) -> Optional[Lance]:
        """
        Obtém um lance específico por ID
        """
        session = self.db_config.get_session()
        try:
            lance = session.query(Lance).filter(Lance.id == lance_id).first()
            return lance
        finally:
            session.close()
    
    def obter_lances_participante(self, participante_id: int, leilao_id: int = None) -> List[Lance]:
        """
        Obtém todos os lances de um participante, opcionalmente filtrado por leilão
        """
        session = self.db_config.get_session()
        try:
            # Verificar se participante existe
            participante = session.query(Participante).filter(Participante.id == participante_id).first()
            if not participante:
                raise ValidationError(f"Participante com ID {participante_id} não encontrado")
            
            query = session.query(Lance).filter(Lance.participante_id == participante_id)
            
            if leilao_id:
                query = query.filter(Lance.leilao_id == leilao_id)
            
            lances = query.order_by(Lance.data_lance.desc()).all()
            return lances
            
        finally:
            session.close()
    
    def verificar_pode_dar_lance(self, participante_id: int, leilao_id: int) -> Tuple[bool, str]:
        """
        Verifica se um participante pode dar um lance em um leilão
        Retorna (pode_dar_lance, motivo)
        """
        session = self.db_config.get_session()
        try:
            # Verificar se participante existe
            participante = session.query(Participante).filter(Participante.id == participante_id).first()
            if not participante:
                return False, "Participante não encontrado"
            
            # Verificar se leilão existe
            leilao = session.query(Leilao).filter(Leilao.id == leilao_id).first()
            if not leilao:
                return False, "Leilão não encontrado"
            
            # Verificar se leilão está aberto
            if leilao.status != StatusLeilao.ABERTO:
                return False, f"Leilão não está aberto (status: {leilao.status.value})"
            
            # Verificar se não foi o último a dar lance
            ultimo_lance = session.query(Lance).filter(Lance.leilao_id == leilao_id).order_by(Lance.data_lance.desc()).first()
            
            if ultimo_lance and ultimo_lance.participante_id == participante_id:
                return False, "Você foi o último a dar lance neste leilão"
            
            return True, "Pode dar lance"
            
        finally:
            session.close()
    
    def obter_valor_minimo_proximo_lance(self, leilao_id: int) -> float:
        """
        Obtém o valor mínimo para o próximo lance
        """
        session = self.db_config.get_session()
        try:
            # Verificar se leilão existe
            leilao = session.query(Leilao).filter(Leilao.id == leilao_id).first()
            if not leilao:
                raise ValidationError(f"Leilão com ID {leilao_id} não encontrado")
            
            # Buscar último lance
            ultimo_lance = session.query(Lance).filter(Lance.leilao_id == leilao_id).order_by(Lance.data_lance.desc()).first()
            
            if ultimo_lance:
                # Próximo lance deve ser maior que o último
                return ultimo_lance.valor + 0.01
            else:
                # Primeiro lance deve ser >= lance mínimo
                return leilao.lance_minimo
            
        finally:
            session.close()
    
    def obter_historico_lances_leilao(self, leilao_id: int) -> List[dict]:
        """
        Obtém histórico completo de lances com informações do participante
        """
        session = self.db_config.get_session()
        try:
            # Verificar se leilão existe
            leilao = session.query(Leilao).filter(Leilao.id == leilao_id).first()
            if not leilao:
                raise ValidationError(f"Leilão com ID {leilao_id} não encontrado")
            
            # Buscar lances com join para pegar dados do participante
            lances_query = session.query(Lance, Participante).join(
                Participante, Lance.participante_id == Participante.id
            ).filter(Lance.leilao_id == leilao_id).order_by(Lance.data_lance.asc())
            
            historico = []
            for lance, participante in lances_query:
                historico.append({
                    'lance_id': lance.id,
                    'valor': lance.valor,
                    'data_lance': lance.data_lance,
                    'participante_id': participante.id,
                    'participante_nome': participante.nome,
                    'participante_cpf': participante.cpf
                })
            
            return historico
            
        finally:
            session.close()
    
    def obter_estatisticas_lances_leilao(self, leilao_id: int) -> dict:
        """
        Obtém estatísticas detalhadas dos lances de um leilão
        """
        session = self.db_config.get_session()
        try:
            # Verificar se leilão existe
            leilao = session.query(Leilao).filter(Leilao.id == leilao_id).first()
            if not leilao:
                raise ValidationError(f"Leilão com ID {leilao_id} não encontrado")
            
            # Buscar todos os lances
            lances = session.query(Lance).filter(Lance.leilao_id == leilao_id).all()
            
            if not lances:
                return {
                    'total_lances': 0,
                    'participantes_unicos': 0,
                    'maior_lance': None,
                    'menor_lance': None,
                    'lance_medio': None,
                    'lance_atual': leilao.lance_minimo,
                    'incremento_total': 0.0
                }
            
            valores = [lance.valor for lance in lances]
            participantes_ids = set(lance.participante_id for lance in lances)
            
            maior_lance = max(valores)
            menor_lance = min(valores)
            incremento_total = maior_lance - leilao.lance_minimo
            
            return {
                'total_lances': len(lances),
                'participantes_unicos': len(participantes_ids),
                'maior_lance': maior_lance,
                'menor_lance': menor_lance,
                'lance_medio': sum(valores) / len(valores),
                'lance_atual': maior_lance,
                'incremento_total': incremento_total
            }
            
        finally:
            session.close()
    
    def obter_ranking_participantes_leilao(self, leilao_id: int) -> List[dict]:
        """
        Obtém ranking dos participantes de um leilão ordenado pelo maior lance
        """
        session = self.db_config.get_session()
        try:
            # Verificar se leilão existe
            leilao = session.query(Leilao).filter(Leilao.id == leilao_id).first()
            if not leilao:
                raise ValidationError(f"Leilão com ID {leilao_id} não encontrado")
            
            # Query para obter o maior lance de cada participante
            from sqlalchemy import func
            
            ranking_query = session.query(
                Participante.id,
                Participante.nome,
                func.max(Lance.valor).label('maior_lance'),
                func.count(Lance.id).label('total_lances')
            ).join(
                Lance, Participante.id == Lance.participante_id
            ).filter(
                Lance.leilao_id == leilao_id
            ).group_by(
                Participante.id, Participante.nome
            ).order_by(
                func.max(Lance.valor).desc()
            )
            
            ranking = []
            posicao = 1
            
            for participante_id, nome, maior_lance, total_lances in ranking_query:
                ranking.append({
                    'posicao': posicao,
                    'participante_id': participante_id,
                    'participante_nome': nome,
                    'maior_lance': float(maior_lance),
                    'total_lances': total_lances,
                    'vencedor': posicao == 1
                })
                posicao += 1
            
            return ranking
            
        finally:
            session.close()
    
    def simular_lance(self, participante_id: int, leilao_id: int, valor: float) -> dict:
        """
        Simula um lance sem criar no banco, retornando validações e informações
        """
        session = self.db_config.get_session()
        try:
            resultado = {
                'valido': False,
                'motivo': '',
                'valor_minimo_aceito': None,
                'ultimo_lance': None,
                'seu_ultimo_lance': None
            }
            
            # Verificações básicas
            try:
                valor = ValidadorLance.validar_valor(valor)
            except ValidationError as e:
                resultado['motivo'] = str(e)
                return resultado
            
            # Verificar participante e leilão
            participante = session.query(Participante).filter(Participante.id == participante_id).first()
            if not participante:
                resultado['motivo'] = "Participante não encontrado"
                return resultado
            
            leilao = session.query(Leilao).filter(Leilao.id == leilao_id).first()
            if not leilao:
                resultado['motivo'] = "Leilão não encontrado"
                return resultado
            
            if leilao.status != StatusLeilao.ABERTO:
                resultado['motivo'] = f"Leilão não está aberto (status: {leilao.status.value})"
                return resultado
            
            # Obter informações dos lances
            ultimo_lance = session.query(Lance).filter(Lance.leilao_id == leilao_id).order_by(Lance.data_lance.desc()).first()
            
            if ultimo_lance:
                resultado['ultimo_lance'] = {
                    'valor': ultimo_lance.valor,
                    'participante_id': ultimo_lance.participante_id,
                    'data': ultimo_lance.data_lance
                }
                
                if ultimo_lance.participante_id == participante_id:
                    resultado['motivo'] = "Você foi o último a dar lance neste leilão"
                    return resultado
                
                valor_minimo = ultimo_lance.valor + 0.01
            else:
                valor_minimo = leilao.lance_minimo
            
            resultado['valor_minimo_aceito'] = valor_minimo
            
            # Verificar se valor é suficiente
            if valor < valor_minimo:
                resultado['motivo'] = f"Lance deve ser pelo menos R$ {valor_minimo:.2f}"
                return resultado
            
            # Obter último lance do participante neste leilão
            seu_ultimo_lance = session.query(Lance).filter(
                and_(Lance.leilao_id == leilao_id, Lance.participante_id == participante_id)
            ).order_by(Lance.data_lance.desc()).first()
            
            if seu_ultimo_lance:
                resultado['seu_ultimo_lance'] = {
                    'valor': seu_ultimo_lance.valor,
                    'data': seu_ultimo_lance.data_lance
                }
            
            resultado['valido'] = True
            resultado['motivo'] = "Lance válido"
            
            return resultado
            
        finally:
            session.close()