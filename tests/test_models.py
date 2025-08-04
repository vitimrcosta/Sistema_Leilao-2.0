from datetime import datetime, timedelta
from src.models import Participante, Leilao, Lance, StatusLeilao

def test_repr_participante(clean_database):
    """Testa __repr__ do Participante - Linha 28"""
    session = clean_database.get_session()
    
    participante = Participante(
        cpf="12345678901",
        nome="João Silva",
        email="joao@teste.com",
        data_nascimento=datetime(1990, 1, 1)
    )
    session.add(participante)
    session.commit()
    
    # Esta linha executa a linha 28 do models.py
    resultado = repr(participante)
    
    # Verificações básicas
    assert "Participante" in resultado
    assert "12345678901" in resultado
    assert "João Silva" in resultado
    
    session.close()

def test_repr_leilao(clean_database):
    """Testa __repr__ do Leilao - Linha 47"""
    session = clean_database.get_session()
    
    leilao = Leilao(
        nome="PlayStation 5",
        lance_minimo=1000.0,
        data_inicio=datetime.now() + timedelta(hours=1),
        data_termino=datetime.now() + timedelta(days=1),
        status=StatusLeilao.INATIVO
    )
    session.add(leilao)
    session.commit()
    
    # Esta linha executa a linha 47 do models.py
    resultado = repr(leilao)
    
    # Verificações básicas
    assert "Leilao" in resultado
    assert "PlayStation 5" in resultado
    assert "INATIVO" in resultado
    
    session.close()

def test_repr_lance(clean_database):
    """Testa __repr__ do Lance - Linha 63"""
    session = clean_database.get_session()
    
    # Criar dependências primeiro
    participante = Participante(
        cpf="12345678901",
        nome="João",
        email="joao@teste.com",
        data_nascimento=datetime(1990, 1, 1)
    )
    session.add(participante)
    
    leilao = Leilao(
        nome="Xbox",
        lance_minimo=800.0,
        data_inicio=datetime.now(),
        data_termino=datetime.now() + timedelta(hours=1)
    )
    session.add(leilao)
    session.commit()
    session.refresh(participante)
    session.refresh(leilao)
    
    # Criar lance
    lance = Lance(
        valor=950.0,
        leilao_id=leilao.id,
        participante_id=participante.id
    )
    session.add(lance)
    session.commit()
    session.refresh(lance)
    
    # Esta linha executa a linha 63 do models.py
    resultado = repr(lance)
    
    # Verificações básicas
    assert "Lance" in resultado
    assert "950.0" in resultado
    assert str(leilao.id) in resultado
    assert str(participante.id) in resultado
    
    session.close()