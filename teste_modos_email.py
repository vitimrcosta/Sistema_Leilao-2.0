"""
Teste dos diferentes modos de email
Execute: python teste_modos_email.py
"""
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Carregar .env
load_dotenv()

# Importar sistema (assumindo que você substituiu o email_service.py)
from src.services import EmailService, LeilaoService, ParticipanteService
from src.repositories import db_config

def demonstrar_modos_email():
    """Demonstra os diferentes modos de operação do EmailService"""
    print("🎯 DEMONSTRAÇÃO DOS MODOS DE EMAIL")
    print("=" * 60)
    
    print("\n1️⃣ MODO TESTE (Forçado)")
    email_teste = EmailService.criar_para_testes()
    print(f"   Modo produção: {email_teste.modo_producao}")
    print(f"   Modo teste: {email_teste.modo_teste}")
    
    print("\n2️⃣ MODO PRODUÇÃO (Forçado)")
    email_producao = EmailService.criar_para_producao()
    print(f"   Modo produção: {email_producao.modo_producao}")
    print(f"   Modo teste: {email_producao.modo_teste}")
    
    print("\n3️⃣ MODO DO .ENV")
    email_env = EmailService.criar_do_env()
    print(f"   Modo produção: {email_env.modo_producao}")
    print(f"   Modo teste: {email_env.modo_teste}")
    print(f"   EMAIL_MODE atual: {os.getenv('EMAIL_MODE', 'AUTO')}")

def testar_modo_configurado():
    """Testa o modo atualmente configurado no .env"""
    print("\n🧪 TESTE DO MODO ATUAL")
    print("=" * 40)
    
    # Usar EmailService padrão (lê do .env)
    email_service = EmailService()
    
    modo_atual = "PRODUÇÃO (REAL)" if email_service.modo_producao else "TESTE (SIMULAÇÃO)"
    print(f"📧 Modo atual: {modo_atual}")
    
    # Teste simples
    sucesso = email_service.criar_email_personalizado(
        nome_participante="Testador de Modo",
        email_destino=os.getenv('EMAIL_DESTINATARIO_TESTE', 'teste@exemplo.com'),
        assunto=f"🎯 Teste do Modo {modo_atual}",
        mensagem=f"""
        Este email foi enviado no modo: {modo_atual}
        
        Configuração atual do .env:
        - EMAIL_MODE: {os.getenv('EMAIL_MODE', 'AUTO')}
        - Testado em: {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}
        
        {'🔴 Este é um EMAIL REAL!' if email_service.modo_producao else '🟡 Este é uma SIMULAÇÃO.'}
        """
    )
    
    if sucesso:
        if email_service.modo_producao:
            print("✅ Email REAL enviado! Verifique sua caixa de entrada.")
        else:
            print("✅ Email simulado com sucesso!")
    else:
        print("❌ Falha no envio do email")

def testar_sistema_completo():
    """Testa o sistema completo de leilão com o modo atual"""
    print("\n🎮 TESTE DO SISTEMA COMPLETO")
    print("=" * 40)
    
    try:
        # Limpar banco
        db_config.create_tables()
        session = db_config.get_session()
        from src.models import Lance, Leilao, Participante
        session.query(Lance).delete()
        session.query(Leilao).delete()
        session.query(Participante).delete()
        session.commit()
        session.close()
        
        # Criar serviços
        participante_service = ParticipanteService()
        leilao_service = LeilaoService()
        
        # Criar participante
        participante = participante_service.criar_participante(
            cpf="12345678901",
            nome="Testador Sistema",
            email=os.getenv('EMAIL_DESTINATARIO_TESTE', 'teste@exemplo.com'),
            data_nascimento=datetime(1990, 1, 1)
        )
        
        # Criar leilão
        leilao = leilao_service.criar_leilao(
            nome="🎮 Teste do Sistema Configurado",
            lance_minimo=1000.0,
            data_inicio=datetime.now() - timedelta(hours=1),
            data_termino=datetime.now() - timedelta(minutes=30),
            permitir_passado=True
        )
        
        # Simular lance e finalização
        from src.services import LanceService
        lance_service = LanceService()
        
        # Abrir leilão
        leilao_service.atualizar_status_leiloes(enviar_emails=False)
        
        # Fazer lance
        lance = lance_service.criar_lance(participante.id, leilao.id, 1500.0)
        
        # Forçar finalização
        session = db_config.get_session()
        leilao_db = session.query(Leilao).filter(Leilao.id == leilao.id).first()
        leilao_db.data_termino = datetime.now() - timedelta(minutes=1)
        session.commit()
        session.close()
        
        # Finalizar COM email
        resultado = leilao_service.atualizar_status_leiloes(enviar_emails=True)
        
        emails_enviados = resultado.get('emails_enviados', 0)
        
        if emails_enviados > 0:
            email_mode = os.getenv('EMAIL_MODE', 'AUTO')
            if email_mode == 'TEST':
                print("✅ Sistema funcionando! Email foi simulado (modo TEST).")
            else:
                print("✅ Sistema funcionando! Email REAL foi enviado!")
                print("📧 Verifique sua caixa de entrada!")
        else:
            print("❌ Sistema não enviou email")
        
        return emails_enviados > 0
        
    except Exception as e:
        print(f"❌ Erro no teste completo: {e}")
        return False

def menu_configuracao():
    """Menu para alterar configuração"""
    print("\n⚙️ ALTERAR CONFIGURAÇÃO")
    print("=" * 30)
    print("1. TEST - Sempre simula (seguro)")
    print("2. PRODUCTION - Sempre envia real")
    print("3. AUTO - Detecta automaticamente")
    print("4. Cancelar")
    
    escolha = input("\nEscolha (1-4): ")
    
    if escolha == "1":
        novo_modo = "TEST"
    elif escolha == "2":
        novo_modo = "PRODUCTION"
    elif escolha == "3":
        novo_modo = "AUTO"
    else:
        print("👋 Cancelado")
        return
    
    print(f"\n💡 Para alterar para {novo_modo}:")
    print(f"   1. Abra o arquivo .env")
    print(f"   2. Altere a linha EMAIL_MODE para: EMAIL_MODE={novo_modo}")
    print(f"   3. Execute o teste novamente")

def main():
    """Menu principal"""
    print("🚀 SISTEMA DE EMAIL CONFIGURÁVEL")
    print("=" * 50)
    
    while True:
        print(f"\n📧 Modo atual no .env: {os.getenv('EMAIL_MODE', 'AUTO')}")
        print("\nEscolha uma opção:")
        print("1. 🔍 Demonstrar modos disponíveis")
        print("2. 🧪 Testar modo atual")
        print("3. 🎮 Testar sistema completo")
        print("4. ⚙️ Como alterar configuração")
        print("5. 👋 Sair")
        
        escolha = input("\nSua escolha (1-5): ")
        
        if escolha == "1":
            demonstrar_modos_email()
        elif escolha == "2":
            testar_modo_configurado()
        elif escolha == "3":
            testar_sistema_completo()
        elif escolha == "4":
            menu_configuracao()
        elif escolha == "5":
            print("👋 Até logo!")
            break
        else:
            print("❌ Opção inválida")

if __name__ == "__main__":
    main()