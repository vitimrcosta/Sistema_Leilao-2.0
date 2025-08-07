# 🏆 Sistema de Leilões

Um sistema completo de leilões desenvolvido em Python com SQLAlchemy, implementando todas as regras de negócio necessárias para gerenciar leilões online de forma segura e eficiente.

## 🚀 Características

- **Gestão Completa de Participantes**: Cadastro, validação e gerenciamento
- **Sistema de Leilões**: Criação e controle de status automático
- **Sistema de Lances**: Validação rigorosa com regras de negócio
- **Notificações por Email**: Sistema automático para vencedores
- **Estados Automáticos**: INATIVO → ABERTO → FINALIZADO/EXPIRADO
- **Validações Robustas**: CPF, email, datas e valores

## 🛠 Tecnologias

- **Python 3.8+**
- **SQLAlchemy**: ORM para banco de dados
- **SQLite**: Banco de dados padrão
- **email-validator**: Validação de emails
- **pytest**: Framework de testes com 98%+ de cobertura

## 📁 Estrutura do Projeto

```
src/
├── models/
│   └── models.py           # Modelos SQLAlchemy
├── repositories/
│   └── database.py         # Configuração do banco
├── services/
│   ├── participante_service.py
│   ├── leilao_service.py
│   ├── lance_service.py
│   └── email_service.py
└── utils/
    └── validators.py       # Validadores

tests/
├── test_participante_service.py
├── test_leilao_service.py
├── test_lance_service.py
├── test_validators.py
└── integration/            # Testes de integração
```

## 🔧 Instalação

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/sistema-leiloes.git
cd sistema-leiloes

# Crie um ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Instale as dependências
pip install -r requirements.txt

# Configure o banco
python -c "from src.repositories.database import db_config; db_config.create_tables()"

# Execute os testes
pytest --cov=src -v
```

## 💡 Uso Básico

```python
from datetime import datetime, timedelta
from src.services import ParticipanteService, LeilaoService, LanceService

# Inicializar serviços
participante_service = ParticipanteService()
leilao_service = LeilaoService()
lance_service = LanceService()

# Criar participante
participante = participante_service.criar_participante(
    cpf="12345678901",
    nome="João Silva",
    email="joao@email.com",
    data_nascimento=datetime(1990, 1, 1)
)

# Criar leilão
leilao = leilao_service.criar_leilao(
    nome="iPhone 15 Pro",
    lance_minimo=1000.0,
    data_inicio=datetime.now() + timedelta(minutes=5),
    data_termino=datetime.now() + timedelta(hours=24)
)

# Abrir leilões automaticamente
leilao_service.atualizar_status_leiloes()

# Criar lance
lance = lance_service.criar_lance(
    participante_id=participante.id,
    leilao_id=leilao.id,
    valor=1100.0
)
```

## 📜 Principais Regras de Negócio

### **Participantes**
- ✅ Idade mínima: 18 anos
- ✅ CPF único e válido
- ✅ Email único e válido
- ⚠️ Não podem ser alterados após fazer lances

### **Leilões**
- ✅ Estados: `INATIVO` → `ABERTO` → `FINALIZADO/EXPIRADO`
- ✅ Transições automáticas por data/hora
- ✅ Apenas leilões inativos podem ser alterados

### **Lances**
- ✅ Apenas em leilões abertos
- ✅ Deve ser maior que lance anterior
- ✅ Mesmo participante não pode dar lances consecutivos
- ❌ Não podem ser alterados após criação

## 🗃 Modelos de Dados

- **Participante**: id, cpf, nome, email, data_nascimento, data_cadastro
- **Leilao**: id, nome, lance_minimo, data_inicio, data_termino, status, participante_vencedor_id
- **Lance**: id, valor, data_lance, leilao_id, participante_id

## 🔌 Principais Funcionalidades

```python
# Listar participantes com filtros
participantes = participante_service.listar_participantes(nome_parcial="João")

# Obter estatísticas de participante
stats = participante_service.obter_estatisticas_participante(participante_id)

# Obter lances ordenados
lances = lance_service.obter_lances_leilao(leilao_id, ordem_crescente=True)

# Verificar se pode dar lance
pode, motivo = lance_service.verificar_pode_dar_lance(participante_id, leilao_id)

# Obter ranking dos participantes
ranking = lance_service.obter_ranking_participantes_leilao(leilao_id)

# Simular lance antes de criar
simulacao = lance_service.simular_lance(participante_id, leilao_id, valor)
```

## 🧪 Testes

Sistema completo de testes automatizados com **98%+ de cobertura**.

```bash
# Executar todos os testes
pytest -v

# Executar com cobertura
pytest --cov=src --cov-report=html

# Testes específicos
pytest tests/test_lance_service.py -v
pytest tests/integration/ -v
```

### Tipos de Testes
- **Unitários**: Cada serviço individualmente
- **Integração**: Cenários completos do sistema
- **Validações**: Todas as regras de negócio

---

## 👥 Desenvolvedores

Este sistema foi desenvolvido por:

- **Luis** - Desenvolvedor
- **Victor** - Desenvolvedor  
- **Roberta** - Desenvolvedor

**Desenvolvido com ❤️ em Python**