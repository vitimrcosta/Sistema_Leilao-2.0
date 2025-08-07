import os
from dotenv import load_dotenv

# Carregar variáveis do arquivo .env
load_dotenv()

class EmailConfig:
    """Configurações de email carregadas do arquivo .env"""
    
    EMAIL_USUARIO = os.getenv('EMAIL_USUARIO')
    EMAIL_SENHA = os.getenv('EMAIL_SENHA')
    EMAIL_DESTINATARIO_TESTE = os.getenv('EMAIL_DESTINATARIO_TESTE')
    SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
    
    @classmethod
    def validar_configuracoes(cls):
        """Valida se todas as configurações necessárias estão presentes"""
        erros = []
        
        if not cls.EMAIL_USUARIO:
            erros.append("EMAIL_USUARIO não configurado no .env")
        
        if not cls.EMAIL_SENHA:
            erros.append("EMAIL_SENHA não configurado no .env")
            
        if not cls.EMAIL_DESTINATARIO_TESTE:
            erros.append("EMAIL_DESTINATARIO_TESTE não configurado no .env")
        
        if erros:
            raise ValueError("Configurações faltando:\n" + "\n".join(f"- {erro}" for erro in erros))
        
        return True
    
    @classmethod
    def mostrar_configuracoes(cls):
        """Mostra as configurações (sem mostrar a senha)"""
        print("📧 Configurações de Email:")
        print(f"   Usuario: {cls.EMAIL_USUARIO}")
        print(f"   Senha: {'*' * len(cls.EMAIL_SENHA) if cls.EMAIL_SENHA else 'NÃO CONFIGURADA'}")
        print(f"   Destinatário Teste: {cls.EMAIL_DESTINATARIO_TESTE}")
        print(f"   SMTP Server: {cls.SMTP_SERVER}:{cls.SMTP_PORT}")

# ===================================================================
# test_email_seguro.py - Teste usando variáveis de ambiente
# ===================================================================

from src.services import EmailService
from config_email import EmailConfig

def teste_email_com_env():
    """Teste de email usando configurações do arquivo .env"""
    print("=== Teste de Email com Variáveis de Ambiente ===")
    
    try:
        # Validar configurações
        EmailConfig.validar_configuracoes()
        EmailConfig.mostrar_configuracoes()
        
        # Criar EmailService com configurações do .env
        email_service = EmailService(
            smtp_server=EmailConfig.SMTP_SERVER,
            smtp_port=EmailConfig.SMTP_PORT,
            email_usuario=EmailConfig.EMAIL_USUARIO,
            email_senha=EmailConfig.EMAIL_SENHA
        )
        
        print(f"\n🔒 Modo produção: {not email_service.modo_teste}")
        
        # Enviar email de teste
        sucesso = email_service.criar_email_personalizado(
            nome_participante="Testador Seguro",
            email_destino=EmailConfig.EMAIL_DESTINATARIO_TESTE,
            assunto="🔐 Teste Seguro do Sistema de Leilões",
            mensagem="Este email foi enviado usando configurações seguras com variáveis de ambiente! 🎉"
        )
        
        if sucesso:
            print("✅ Email enviado com sucesso usando configuração segura!")
            print(f"📧 Verifique o email: {EmailConfig.EMAIL_DESTINATARIO_TESTE}")
        else:
            print("❌ Falha no envio do email")
        
        return sucesso
        
    except ValueError as e:
        print(f"❌ Erro de configuração: {e}")
        print("\n💡 Solução:")
        print("1. Crie um arquivo .env na raiz do projeto")
        print("2. Adicione suas configurações de email no .env")
        print("3. Execute: pip install python-dotenv")
        return False
    
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return False

if __name__ == "__main__":
    teste_email_com_env()