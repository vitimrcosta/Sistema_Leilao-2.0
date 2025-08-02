from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime
import enum

Base = declarative_base()

class StatusLeilao(enum.Enum):
    INATIVO = "INATIVO"
    ABERTO = "ABERTO"
    FINALIZADO = "FINALIZADO"
    EXPIRADO = "EXPIRADO"

class Participante(Base):
    __tablename__ = 'participantes'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    cpf = Column(String(11), unique=True, nullable=False)
    nome = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    data_nascimento = Column(DateTime, nullable=False)
    data_cadastro = Column(DateTime, default=datetime.now)
    
    # Relacionamento com lances
    lances = relationship("Lance", back_populates="participante")
    
    def __repr__(self):
        return f"<Participante(cpf='{self.cpf}', nome='{self.nome}')>"

class Leilao(Base):
    __tablename__ = 'leiloes'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(200), nullable=False)
    lance_minimo = Column(Float, nullable=False)
    data_inicio = Column(DateTime, nullable=False)
    data_termino = Column(DateTime, nullable=False)
    status = Column(SQLEnum(StatusLeilao), default=StatusLeilao.INATIVO, nullable=False)
    data_cadastro = Column(DateTime, default=datetime.now)
    participante_vencedor_id = Column(Integer, ForeignKey('participantes.id'), nullable=True)
    
    # Relacionamentos
    lances = relationship("Lance", back_populates="leilao", cascade="all, delete-orphan")
    participante_vencedor = relationship("Participante")
    
    def __repr__(self):
        return f"<Leilao(nome='{self.nome}', status='{self.status.value}')>"

class Lance(Base):
    __tablename__ = 'lances'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    valor = Column(Float, nullable=False)
    data_lance = Column(DateTime, default=datetime.now)
    leilao_id = Column(Integer, ForeignKey('leiloes.id'), nullable=False)
    participante_id = Column(Integer, ForeignKey('participantes.id'), nullable=False)
    
    # Relacionamentos
    leilao = relationship("Leilao", back_populates="lances")
    participante = relationship("Participante", back_populates="lances")
    
    def __repr__(self):
        return f"<Lance(valor={self.valor}, leilao_id={self.leilao_id}, participante_id={self.participante_id})>"