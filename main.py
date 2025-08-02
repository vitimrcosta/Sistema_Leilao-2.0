from src.repositories import db_config
from src.models import Participante, Leilao, Lance, StatusLeilao
from src.utils import ValidadorParticipante, ValidadorLeilao, ValidationError
from src.services import LeilaoService, ParticipanteService, LanceService, EmailService
from datetime import datetime, timedelta

def teste_sistema_completo():
    """Teste completo do sistema reorganizado"""
    print("=== Sistema de Leilões - Teste Completo ===")
    
    try:
        # Criar tabelas
        db_config.create_tables()
        print("✓ Banco de dados configurado")
        
        # Limpar dados para teste limpo
        session = db_config.get_session()
        session.query(Lance).delete()
        session.query(Leilao).delete()
        session.query(Participante).delete()
        session.commit()
        session.close()
        print("✓ Dados limpos")
        
        # Instanciar serviços
        participante_service = ParticipanteService()
        leilao_service = LeilaoService()
        lance_service = LanceService()
        email_service = EmailService()  # Novo serviço de email
        
        # 1. Criar participantes
        p1 = participante_service.criar_participante(
            "12345678901", "João Silva", "joao@exemplo.com", datetime(1990, 5, 15)
        )
        
        p2 = participante_service.criar_participante(
            "10987654321", "Maria Santos", "maria@exemplo.com", datetime(1985, 8, 20)
        )
        
        print(f"✓ Participantes criados: {p1.nome} e {p2.nome}")
        
        # 2. Criar leilão
        leilao = leilao_service.criar_leilao(
            nome="PlayStation 5",
            lance_minimo=1000.0,
            data_inicio=datetime.now() - timedelta(minutes=10),
            data_termino=datetime.now() + timedelta(hours=1),
            permitir_passado=True
        )
        
        print(f"✓ Leilão criado: {leilao.nome}")
        
        # 3. Abrir leilão
        resultado = leilao_service.atualizar_status_leiloes(enviar_emails=False)  # Sem email ainda
        leilao = leilao_service.obter_leilao_por_id(leilao.id)
        print(f"✓ Leilão aberto: {leilao.status.value}")
        
        # 4. Fazer lances
        lance1 = lance_service.criar_lance(p1.id, leilao.id, 1100.0)
        lance2 = lance_service.criar_lance(p2.id, leilao.id, 1200.0)
        lance3 = lance_service.criar_lance(p1.id, leilao.id, 1300.0)
        
        print(f"✓ Lances criados: R$ {lance1.valor}, R$ {lance2.valor}, R$ {lance3.valor}")
        
        # 5. Verificar estatísticas
        stats = lance_service.obter_estatisticas_lances_leilao(leilao.id)
        print(f"✓ Estatísticas: {stats['total_lances']} lances, maior: R$ {stats['maior_lance']}")
        
        # 6. Ranking
        ranking = lance_service.obter_ranking_participantes_leilao(leilao.id)
        vencedor = ranking[0] if ranking else None
        if vencedor:
            print(f"✓ Vencedor atual: {vencedor['participante_nome']} com R$ {vencedor['maior_lance']}")
        
        # 7. NOVA FUNCIONALIDADE: Simular finalização do leilão e envio de email
        print("\n🎯 Testando nova funcionalidade de EMAIL...")
        
        # Forçar finalização do leilão (simular que o tempo acabou)
        session = db_config.get_session()
        leilao_db = session.query(Leilao).filter(Leilao.id == leilao.id).first()
        leilao_db.data_termino = datetime.now() - timedelta(minutes=1)  # Já terminou
        session.commit()
        session.close()
        
        # Atualizar status COM envio de emails automático
        resultado_final = leilao_service.atualizar_status_leiloes(enviar_emails=True)
        
        print(f"✓ Leilão finalizado: {resultado_final['finalizados']} leilão(ões)")
        print(f"✓ Emails enviados: {resultado_final['emails_enviados']} email(s)")
        
        # 8. Verificar vencedor final
        leilao_final = leilao_service.obter_leilao_por_id(leilao.id)
        if leilao_final.status == StatusLeilao.FINALIZADO:
            vencedor_final = participante_service.obter_participante_por_id(leilao_final.participante_vencedor_id)
            print(f"🏆 VENCEDOR FINAL: {vencedor_final.nome} ({vencedor_final.email})")
        
        print("\n🎉 Sistema funcionando perfeitamente!")
        print("📁 Estrutura organizada com sucesso!")
        print("📧 Funcionalidade de EMAIL implementada!")
        
        return True
        
    except Exception as e:
        print(f"✗ Erro: {e}")
        return False

def demonstrar_email_manual():
    """Demonstra envio manual de email"""
    print("\n=== Teste Manual de Email ===")
    
    email_service = EmailService()
    
    # Enviar email de teste
    sucesso = email_service.criar_email_personalizado(
        nome_participante="João Silva",
        email_destino="joao@exemplo.com", 
        assunto="🎉 Teste do Sistema de Leilões",
        mensagem="Este é um teste do sistema de emails do nosso sistema de leilões!"
    )
    
    if sucesso:
        print("✅ Email de teste enviado com sucesso!")
    else:
        print("❌ Falha no envio do email de teste")

def demonstrar_estrutura():
    """Mostra a nova estrutura do projeto"""
    print("\n=== Nova Estrutura do Projeto ===")
    estrutura = """
    sistema_leiloes/
    ├── src/
    │   ├── models/
    │   │   ├── __init__.py
    │   │   └── models.py           ← Modelos do banco
    │   ├── repositories/
    │   │   ├── __init__.py
    │   │   └── database.py         ← Configuração do banco
    │   ├── services/
    │   │   ├── __init__.py
    │   │   ├── leilao_service.py
    │   │   ├── participante_service.py
    │   │   ├── lance_service.py
    │   │   └── email_service.py    ← 📧 NOVO: Serviço de Email
    │   └── utils/
    │       ├── __init__.py
    │       └── validators.py       ← Validações
    ├── tests/
    │   ├── conftest.py
    │   ├── test_*.py
    │   └── integration/
    ├── main.py
    └── requirements.txt
    """
    print(estrutura)

if __name__ == "__main__":
    from src.repositories import db_config
from src.models import Participante, Leilao, Lance, StatusLeilao
from src.utils import ValidadorParticipante, ValidadorLeilao, ValidationError
from src.services import LeilaoService, ParticipanteService, LanceService
from datetime import datetime, timedelta

def teste_sistema_completo():
    """Teste completo do sistema reorganizado"""
    print("=== Sistema de Leilões - Teste Completo ===")
    
    try:
        # Criar tabelas
        db_config.create_tables()
        print("✓ Banco de dados configurado")
        
        # Limpar dados para teste limpo
        session = db_config.get_session()
        session.query(Lance).delete()
        session.query(Leilao).delete()
        session.query(Participante).delete()
        session.commit()
        session.close()
        print("✓ Dados limpos")
        
        # Instanciar serviços
        participante_service = ParticipanteService()
        leilao_service = LeilaoService()
        lance_service = LanceService()
        
        # 1. Criar participantes
        p1 = participante_service.criar_participante(
            "12345678901", "João Silva", "joao@exemplo.com", datetime(1990, 5, 15)
        )
        
        p2 = participante_service.criar_participante(
            "10987654321", "Maria Santos", "maria@exemplo.com", datetime(1985, 8, 20)
        )
        
        print(f"✓ Participantes criados: {p1.nome} e {p2.nome}")
        
        # 2. Criar leilão
        leilao = leilao_service.criar_leilao(
            nome="PlayStation 5",
            lance_minimo=1000.0,
            data_inicio=datetime.now() - timedelta(minutes=10),
            data_termino=datetime.now() + timedelta(hours=1),
            permitir_passado=True
        )
        
        print(f"✓ Leilão criado: {leilao.nome}")
        
        # 3. Abrir leilão
        resultado = leilao_service.atualizar_status_leiloes()
        leilao = leilao_service.obter_leilao_por_id(leilao.id)
        print(f"✓ Leilão aberto: {leilao.status.value}")
        
        # 4. Fazer lances
        lance1 = lance_service.criar_lance(p1.id, leilao.id, 1100.0)
        lance2 = lance_service.criar_lance(p2.id, leilao.id, 1200.0)
        lance3 = lance_service.criar_lance(p1.id, leilao.id, 1300.0)
        
        print(f"✓ Lances criados: R$ {lance1.valor}, R$ {lance2.valor}, R$ {lance3.valor}")
        
        # 5. Verificar estatísticas
        stats = lance_service.obter_estatisticas_lances_leilao(leilao.id)
        print(f"✓ Estatísticas: {stats['total_lances']} lances, maior: R$ {stats['maior_lance']}")
        
        # 6. Ranking
        ranking = lance_service.obter_ranking_participantes_leilao(leilao.id)
        vencedor = ranking[0] if ranking else None
        if vencedor:
            print(f"✓ Vencedor atual: {vencedor['participante_nome']} com R$ {vencedor['maior_lance']}")
        
        print("\n🎉 Sistema funcionando perfeitamente!")
        print("📁 Estrutura organizada com sucesso!")
        
        return True
        
    except Exception as e:
        print(f"✗ Erro: {e}")
        return False

def demonstrar_estrutura():
    """Mostra a nova estrutura do projeto"""
    print("\n=== Nova Estrutura do Projeto ===")
    estrutura = """
    sistema_leiloes/
    ├── src/
    │   ├── models/
    │   │   ├── __init__.py
    │   │   └── models.py           ← Modelos do banco
    │   ├── repositories/
    │   │   ├── __init__.py
    │   │   └── database.py         ← Configuração do banco
    │   ├── services/
    │   │   ├── __init__.py
    │   │   ├── leilao_service.py
    │   │   ├── participante_service.py
    │   │   └── lance_service.py
    │   └── utils/
    │       ├── __init__.py
    │       └── validators.py       ← Validações
    ├── tests/
    │   ├── conftest.py
    │   ├── test_*.py
    │   └── integration/
    ├── main.py
    └── requirements.txt
    """
    print(estrutura)

if __name__ == "__main__":
    demonstrar_estrutura()
    teste_sistema_completo()
    demonstrar_email_manual()