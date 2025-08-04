"""
EmailService Melhorado - Configurável por ambiente
"""
import smtplib
import ssl
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv

from src.models import Leilao, Participante
from src.utils import ValidationError

# Carregar variáveis de ambiente
load_dotenv()

class EmailService:
    def __init__(self, smtp_server: str = "smtp.gmail.com", smtp_port: int = 587, 
                 email_usuario: str = None, email_senha: str = None, 
                 modo_producao: bool = None):
        """
        Inicializa o serviço de email com configuração flexível
        
        Args:
            smtp_server: Servidor SMTP
            smtp_port: Porta SMTP
            email_usuario: Email do remetente
            email_senha: Senha/token do remetente
            modo_producao: Force produção (True) ou teste (False). Se None, detecta automaticamente
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        
        # Configurações do .env têm prioridade
        self.email_usuario = email_usuario or os.getenv('EMAIL_USUARIO', "sistema.leiloes@exemplo.com")
        self.email_senha = email_senha or os.getenv('EMAIL_SENHA', "senha_do_sistema")
        
        # Determinar modo de operação
        self.modo_producao = self._determinar_modo_operacao(modo_producao)
        self.modo_teste = not self.modo_producao
        
        # Log da configuração
        self._log_configuracao()
    
    def _determinar_modo_operacao(self, modo_producao_forcado: bool = None) -> bool:
        """
        Determina se deve operar em modo produção ou teste
        
        Prioridade:
        1. Parâmetro modo_producao (força manual)
        2. Variável de ambiente EMAIL_MODE
        3. Presença de credenciais reais
        """
        # 1. Modo forçado via parâmetro
        if modo_producao_forcado is not None:
            return modo_producao_forcado
        
        # 2. Variável de ambiente EMAIL_MODE
        email_mode = os.getenv('EMAIL_MODE', '').upper()
        if email_mode == 'PRODUCTION':
            return True
        elif email_mode == 'TEST':
            return False
        
        # 3. Auto-detecção: tem credenciais reais?
        tem_credenciais_reais = (
            self.email_usuario and 
            self.email_senha and 
            self.email_usuario != "sistema.leiloes@exemplo.com" and
            self.email_senha != "senha_do_sistema" and
            len(self.email_senha) > 10  # Senhas de app são longas
        )
        
        return tem_credenciais_reais
    
    def _log_configuracao(self):
        """Log da configuração atual (para debug)"""
        modo_str = "🔴 PRODUÇÃO" if self.modo_producao else "🟡 SIMULAÇÃO"
        print(f"📧 EmailService: {modo_str}")
        
        if self.modo_producao:
            print(f"   📨 Remetente: {self.email_usuario}")
            print(f"   🌐 SMTP: {self.smtp_server}:{self.smtp_port}")
        else:
            print(f"   🧪 Modo teste ativo - emails não serão enviados")
    
    def enviar_email_vencedor(self, leilao: Leilao, participante_vencedor: Participante, 
                             valor_lance_vencedor: float) -> bool:
        """
        Envia email de parabenização para o vencedor do leilão
        """
        try:
            # Criar mensagem
            mensagem = self._criar_mensagem_vencedor(leilao, participante_vencedor, valor_lance_vencedor)
            
            if self.modo_teste:
                # Modo teste - apenas simular
                return self._simular_envio_email(mensagem, participante_vencedor.email)
            else:
                # Modo produção - enviar email real
                return self._enviar_email_real(mensagem, participante_vencedor.email)
                
        except Exception as e:
            print(f"❌ Erro ao enviar email para {participante_vencedor.email}: {e}")
            return False
    
    def criar_email_personalizado(self, nome_participante: str, email_destino: str, 
                                 assunto: str, mensagem: str) -> bool:
        """
        Envia email personalizado (sempre em modo real se tem credenciais)
        """
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email_usuario
            msg['To'] = email_destino
            msg['Subject'] = assunto
            
            corpo = f"""
            <html>
            <body>
                <h3>Olá, {nome_participante}!</h3>
                <p>{mensagem}</p>
                <hr>
                <p style="color: #666; font-size: 12px;">
                    Sistema de Leilões - {datetime.now().strftime('%d/%m/%Y às %H:%M')}
                </p>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(corpo, 'html', 'utf-8'))
            
            # Para emails personalizados, usa modo produção se tem credenciais
            if self.modo_producao:
                return self._enviar_email_real(msg, email_destino)
            else:
                return self._simular_envio_email(msg, email_destino)
                
        except Exception as e:
            print(f"❌ Erro ao enviar email personalizado: {e}")
            return False
    
    def _criar_mensagem_vencedor(self, leilao: Leilao, participante: Participante, 
                                valor_lance: float) -> MIMEMultipart:
        """Cria a mensagem de email para o vencedor"""
        
        msg = MIMEMultipart()
        msg['From'] = self.email_usuario
        msg['To'] = participante.email
        msg['Subject'] = f"🎉 Parabéns! Você venceu o leilão: {leilao.nome}"
        
        # Template do email
        corpo_email = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; color: white;">
                <h1 style="margin: 0;">🎉 PARABÉNS!</h1>
                <h2 style="margin: 10px 0 0 0;">Você VENCEU o leilão!</h2>
            </div>
            
            <div style="padding: 30px; background-color: #f9f9f9;">
                <h3 style="color: #333;">Olá, {participante.nome}! 👋</h3>
                
                <p style="font-size: 16px; line-height: 1.6;">
                    É com grande prazer que informamos que você <strong>VENCEU</strong> o leilão!
                </p>
                
                <div style="background-color: white; padding: 25px; border-radius: 10px; margin: 20px 0; border-left: 5px solid #4CAF50;">
                    <h3 style="color: #4CAF50; margin-top: 0;">📋 Detalhes do Leilão Vencido</h3>
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold;">🎮 Produto:</td>
                            <td style="padding: 8px 0;">{leilao.nome}</td>
                        </tr>
                        <tr style="background-color: #f0f8ff;">
                            <td style="padding: 8px 0; font-weight: bold;">💰 Seu Lance Vencedor:</td>
                            <td style="padding: 8px 0; font-size: 18px; color: #4CAF50; font-weight: bold;">R$ {valor_lance:,.2f}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold;">📅 Início:</td>
                            <td style="padding: 8px 0;">{leilao.data_inicio.strftime('%d/%m/%Y às %H:%M')}</td>
                        </tr>
                        <tr style="background-color: #f0f8ff;">
                            <td style="padding: 8px 0; font-weight: bold;">⏰ Encerramento:</td>
                            <td style="padding: 8px 0;">{leilao.data_termino.strftime('%d/%m/%Y às %H:%M')}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold;">💵 Lance Mínimo:</td>
                            <td style="padding: 8px 0;">R$ {leilao.lance_minimo:,.2f}</td>
                        </tr>
                    </table>
                </div>
                
                <div style="background-color: #e8f5e8; padding: 20px; border-radius: 10px; margin: 20px 0;">
                    <h3 style="color: #2e7d32; margin-top: 0;">🏆 Você foi o melhor!</h3>
                    <p style="margin: 0; font-size: 16px;">
                        Seu lance de <strong>R$ {valor_lance:,.2f}</strong> foi o maior entre todos os participantes!
                    </p>
                </div>
                
                <div style="background-color: #fff3cd; padding: 20px; border-radius: 10px; margin: 20px 0; border: 1px solid #ffeaa7;">
                    <h3 style="color: #856404; margin-top: 0;">📞 Próximos Passos</h3>
                    <p style="margin: 0; line-height: 1.6;">
                        Nossa equipe entrará em contato em breve para finalizar o processo de arrematação.<br>
                        <strong>Por favor, mantenha este email como comprovante da sua vitória no leilão.</strong>
                    </p>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <p style="font-size: 18px; color: #4CAF50; font-weight: bold;">
                        🎊 Parabéns novamente! 🎊
                    </p>
                </div>
            </div>
            
            <div style="background-color: #333; color: white; padding: 20px; text-align: center; font-size: 12px;">
                <strong>Sistema de Leilões</strong><br>
                Email enviado automaticamente em {datetime.now().strftime('%d/%m/%Y às %H:%M')}<br>
                <small>Leilão ID: {leilao.id} | Participante: {participante.cpf}</small>
            </div>
        </body>
        </html>
        """
        
        # Anexar corpo HTML
        msg.attach(MIMEText(corpo_email, 'html', 'utf-8'))
        
        return msg
    
    def _simular_envio_email(self, mensagem: MIMEMultipart, email_destino: str) -> bool:
        """Simula envio de email (para desenvolvimento/testes)"""
        print(f"\n📧 === EMAIL SIMULADO ===")
        print(f"Para: {email_destino}")
        print(f"Assunto: {mensagem['Subject']}")
        print(f"Enviado em: {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}")
        print("✅ Email enviado com sucesso (modo simulação)")
        print("=" * 50)
        return True
    
    def _enviar_email_real(self, mensagem: MIMEMultipart, email_destino: str) -> bool:
        """Envia email real via SMTP"""
        try:
            # Criar conexão SSL
            context = ssl.create_default_context()
            
            # Conectar ao servidor SMTP
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.email_usuario, self.email_senha)
                
                # Enviar email
                texto_mensagem = mensagem.as_string()
                server.sendmail(self.email_usuario, email_destino, texto_mensagem)
                
            print(f"✅ Email REAL enviado com sucesso para {email_destino}")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao enviar email real: {e}")
            return False
    
    def notificar_vencedores_pendentes(self, leilao_service) -> dict:
        """
        Notifica todos os vencedores de leilões que precisam ser notificados
        Integração com LeilaoService
        """
        resultado = {
            'emails_enviados': 0,
            'emails_falharam': 0,
            'detalhes': []
        }
        
        try:
            # Buscar leilões que precisam notificar
            leiloes_para_notificar = leilao_service.leiloes_que_precisa_notificar()
            
            for leilao in leiloes_para_notificar:
                # Buscar dados do vencedor
                session = leilao_service.db_config.get_session()
                participante_vencedor = session.query(Participante).filter(
                    Participante.id == leilao.participante_vencedor_id
                ).first()
                
                if not participante_vencedor:
                    session.close()
                    continue
                
                # Buscar valor do lance vencedor
                from src.models import Lance
                lance_vencedor = session.query(Lance).filter(
                    Lance.leilao_id == leilao.id,
                    Lance.participante_id == participante_vencedor.id
                ).order_by(Lance.valor.desc()).first()
                
                session.close()
                
                if not lance_vencedor:
                    continue
                
                # Enviar email
                sucesso = self.enviar_email_vencedor(leilao, participante_vencedor, lance_vencedor.valor)
                
                if sucesso:
                    resultado['emails_enviados'] += 1
                    resultado['detalhes'].append({
                        'leilao': leilao.nome,
                        'vencedor': participante_vencedor.nome,
                        'email': participante_vencedor.email,
                        'valor_lance': lance_vencedor.valor,
                        'status': 'enviado'
                    })
                else:
                    resultado['emails_falharam'] += 1
                    resultado['detalhes'].append({
                        'leilao': leilao.nome,
                        'vencedor': participante_vencedor.nome,
                        'email': participante_vencedor.email,
                        'status': 'falhou'
                    })
            
            return resultado
            
        except Exception as e:
            print(f"Erro ao notificar vencedores: {e}")
            return resultado

    # Métodos de conveniência para diferentes ambientes
    @classmethod
    def criar_para_testes(cls):
        """Criar EmailService forçado para modo teste"""
        return cls(modo_producao=False)
    
    @classmethod
    def criar_para_producao(cls):
        """Criar EmailService forçado para modo produção"""
        return cls(modo_producao=True)
    
    @classmethod
    def criar_do_env(cls):
        """Criar EmailService usando apenas configurações do .env"""
        return cls(
            smtp_server=os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
            smtp_port=int(os.getenv('SMTP_PORT', '587')),
            email_usuario=os.getenv('EMAIL_USUARIO'),
            email_senha=os.getenv('EMAIL_SENHA')
        )