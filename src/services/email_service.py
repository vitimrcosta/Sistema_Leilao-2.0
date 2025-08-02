import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Optional

from src.models import Leilao, Participante
from src.utils import ValidationError

class EmailService:
    def __init__(self, smtp_server: str = "smtp.gmail.com", smtp_port: int = 587, 
                 email_usuario: str = None, email_senha: str = None):
        """
        Inicializa o serviço de email
        Para produção, use variáveis de ambiente para email/senha
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.email_usuario = email_usuario or "sistema.leiloes@exemplo.com"
        self.email_senha = email_senha or "senha_do_sistema"
        self.modo_teste = email_usuario is None  # Se não tem credenciais, é modo teste
    
    def enviar_email_vencedor(self, leilao: Leilao, participante_vencedor: Participante, 
                             valor_lance_vencedor: float) -> bool:
        """
        Envia email de parabenização para o vencedor do leilão
        REGRA m: O ganhador do leilão deve receber um email parabenizando-o pelo arremate
        """
        try:
            # Criar mensagem
            mensagem = self._criar_mensagem_vencedor(leilao, participante_vencedor, valor_lance_vencedor)
            
            if self.modo_teste:
                # Modo teste - apenas simular envio
                return self._simular_envio_email(mensagem, participante_vencedor.email)
            else:
                # Modo produção - enviar email real
                return self._enviar_email_real(mensagem, participante_vencedor.email)
                
        except Exception as e:
            print(f"Erro ao enviar email para {participante_vencedor.email}: {e}")
            return False
    
    def _criar_mensagem_vencedor(self, leilao: Leilao, participante: Participante, 
                                valor_lance: float) -> MIMEMultipart:
        """Cria a mensagem de email para o vencedor"""
        
        # Criar mensagem
        msg = MIMEMultipart()
        msg['From'] = self.email_usuario
        msg['To'] = participante.email
        msg['Subject'] = f"🎉 Parabéns! Você venceu o leilão: {leilao.nome}"
        
        # Template do email
        corpo_email = f"""
        <html>
        <body>
            <h2>🎉 Parabéns, {participante.nome}!</h2>
            
            <p>É com grande prazer que informamos que você <strong>VENCEU</strong> o leilão!</p>
            
            <div style="background-color: #f0f8ff; padding: 20px; border-radius: 10px; margin: 20px 0;">
                <h3>📋 Detalhes do Leilão Vencido:</h3>
                <ul>
                    <li><strong>Produto:</strong> {leilao.nome}</li>
                    <li><strong>Seu Lance Vencedor:</strong> R$ {valor_lance:,.2f}</li>
                    <li><strong>Data de Início:</strong> {leilao.data_inicio.strftime('%d/%m/%Y às %H:%M')}</li>
                    <li><strong>Data de Encerramento:</strong> {leilao.data_termino.strftime('%d/%m/%Y às %H:%M')}</li>
                    <li><strong>Lance Mínimo:</strong> R$ {leilao.lance_minimo:,.2f}</li>
                </ul>
            </div>
            
            <div style="background-color: #f0fff0; padding: 15px; border-radius: 10px; margin: 20px 0;">
                <h3>🏆 Você foi o melhor!</h3>
                <p>Seu lance de <strong>R$ {valor_lance:,.2f}</strong> foi o maior entre todos os participantes!</p>
            </div>
            
            <div style="background-color: #fff8dc; padding: 15px; border-radius: 10px; margin: 20px 0;">
                <h3>📞 Próximos Passos:</h3>
                <p>Nossa equipe entrará em contato em breve para finalizar o processo de arrematação.</p>
                <p>Por favor, mantenha este email como comprovante da sua vitória no leilão.</p>
            </div>
            
            <hr>
            <p style="color: #666; font-size: 12px;">
                <strong>Sistema de Leilões</strong><br>
                Email enviado automaticamente em {datetime.now().strftime('%d/%m/%Y às %H:%M')}<br>
                Leilão ID: {leilao.id} | Participante: {participante.cpf}
            </p>
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
        print("✅ Email de vitória enviado com sucesso (modo simulação)")
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
                
            print(f"✅ Email enviado com sucesso para {email_destino}")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao enviar email: {e}")
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
                participante_vencedor = leilao_service.db_config.get_session().query(Participante).filter(
                    Participante.id == leilao.participante_vencedor_id
                ).first()
                
                if not participante_vencedor:
                    continue
                
                # Buscar valor do lance vencedor
                from src.models import Lance
                lance_vencedor = leilao_service.db_config.get_session().query(Lance).filter(
                    Lance.leilao_id == leilao.id,
                    Lance.participante_id == participante_vencedor.id
                ).order_by(Lance.valor.desc()).first()
                
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
    
    def criar_email_personalizado(self, nome_participante: str, email_destino: str, 
                                 assunto: str, mensagem: str) -> bool:
        """
        Envia email personalizado (para outras notificações do sistema)
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
            
            if self.modo_teste:
                return self._simular_envio_email(msg, email_destino)
            else:
                return self._enviar_email_real(msg, email_destino)
                
        except Exception as e:
            print(f"Erro ao enviar email personalizado: {e}")
            return False