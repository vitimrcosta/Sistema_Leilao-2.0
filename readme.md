# 🏆 Sistema de Leilões

Um sistema completo de leilões desenvolvido em Python com SQLAlchemy, implementando todas as regras de negócio necessárias para gerenciar leilões online de forma segura e eficiente.

## 📋 Índice

- [Características](#-características)
- [Tecnologias](#-tecnologias)
- [Estrutura do Projeto](#-estrutura-do-projeto)
- [Instalação](#-instalação)
- [Uso](#-uso)
- [Regras de Negócio](#-regras-de-negócio)
- [API/Serviços](#-apiserviços)
- [Modelos de Dados](#-modelos-de-dados)
- [Validações](#-validações)
- [Contribuição](#-contribuição)
- [Licença](#-licença)

## 🚀 Características

- **Gestão Completa de Participantes**: Cadastro, validação e gerenciamento de participantes
- **Sistema de Leilões**: Criação, atualização e controle de status automático
- **Sistema de Lances**: Validação rigorosa de lances com regras de negócio
- **Notificações por Email**: Sistema automático de notificação para vencedores
- **Estados Automáticos**: Controle automático de estados dos leilões (INATIVO → ABERTO → FINALIZADO/EXPIRADO)
- **Validações Robustas**: Validação de CPF, email, datas e valores

## 🛠 Tecnologias

- **Python 3.8+**
- **SQLAlchemy**: ORM para gerenciamento do banco de dados
- **SQLite**: Banco de dados (configurável para outros SGBDs)
- **email-validator**: Validação de emails
- **SMTP**: Sistema de envio de emails
- **pytest**: Framework de testes
- **pytest-cov**: Cobertura de testes

## 📁 Estrutura do Projeto

```
src/
├── models/
│   └── models.py           # Modelos SQLAlchemy (Participante, Leilao, Lance)
├── repositories/
│   └── database.py         # Configuração do banco de dados
├── services/
│   ├── participante_service.py  # Lógica de negócio para participantes
│   ├── leilao_service.py       # Lógica de negócio para leilões
│   ├── lance_service.py        # Lógica de negócio para lances
│   └── email_service.py        # Sistema de notificações por email
└── utils/
    └── validators.py       # Validadores e regras de validação

tests/
├── conftest.py                    # Configurações e fixtures para testes
├── test_participante_service.py   # Testes unitários do ParticipanteService
├── test_leilao_service.py        # Testes unitários do LeilaoService
├── test_lance_service.py         # Testes unitários do LanceService
├── test_email_service.py         # Testes unitários do EmailService
└── integration/                  # Testes de integração
    ├── test_integration.py       # Testes de integração gerais
    ├── test_lance_integration.py # Testes de integração de lances
    └── test_participante_integration.py # Testes integração participantes
```

## 🔧 Instalação

1. **Clone o repositório**
```bash
git clone https://github.com/seu-usuario/sistema-leiloes.git
cd sistema-leiloes
```

2. **Crie um ambiente virtual**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows
```

3. **Instale as dependências**
```bash
pip install sqlalchemy email-validator pytest
```

4. **Configure o banco de dados**
```python
from src.repositories.database import db_config

# Criar as tabelas
db_config.create_tables()
```

5. **Execute os testes**
```bash
# Executar todos os testes
pytest

# Executar testes com detalhes
pytest -v

# Executar testes de um módulo específico
pytest tests/test_lance_service.py -v

# Executar com coverage
pytest --cov=src
```

## 💡 Uso

### Exemplo Básico

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

# Atualizar status dos leilões (INATIVO → ABERTO quando chegar a hora)
leilao_service.atualizar_status_leiloes()

# Criar lance
lance = lance_service.criar_lance(
    participante_id=participante.id,
    leilao_id=leilao.id,
    valor=1100.0
)
```

## 📜 Regras de Negócio

### **Participantes**
- ✅ Participantes devem ter pelo menos 18 anos
- ✅ CPF único e válido (11 dígitos numéricos)
- ✅ Email único e válido
- ⚠️ Participantes com lances não podem ser alterados/excluídos

### **Leilões**
- ✅ Quatro estados: `INATIVO`, `ABERTO`, `FINALIZADO`, `EXPIRADO`
- ✅ Transições automáticas baseadas em data/hora
- ✅ Apenas leilões `INATIVOS` podem ser alterados/excluídos
- ✅ Data de término deve ser posterior à data de início
- ✅ Lance mínimo obrigatório e > 0

### **Lances**
- ✅ Apenas em leilões `ABERTOS`
- ✅ Participante deve estar cadastrado
- ✅ Lance deve ser ≥ lance mínimo
- ✅ Lance deve ser maior que o último lance
- ⚠️ Mesmo participante não pode dar dois lances consecutivos
- ❌ Lances não podem ser alterados após criação

### **Notificações**
- 📧 Vencedores recebem email automático
- 🏆 Sistema identifica vencedor automaticamente (maior lance)

## 🔌 API/Serviços

### ParticipanteService

```python
# Criar participante
participante = participante_service.criar_participante(cpf, nome, email, data_nascimento)

# Listar participantes
participantes = participante_service.listar_participantes(nome_parcial="João")

# Obter estatísticas
stats = participante_service.obter_estatisticas_participante(participante_id)
```

### LeilaoService

```python
# Criar leilão
leilao = leilao_service.criar_leilao(nome, lance_minimo, data_inicio, data_termino)

# Atualizar status automaticamente
resultado = leilao_service.atualizar_status_leiloes(enviar_emails=True)

# Listar leilões por status
leiloes_abertos = leilao_service.listar_leiloes(status=StatusLeilao.ABERTO)
```

### LanceService

```python
# Criar lance
lance = lance_service.criar_lance(participante_id, leilao_id, valor)

# Obter lances de um leilão (ordem crescente)
lances = lance_service.obter_lances_leilao(leilao_id, ordem_crescente=True)

# Verificar se pode dar lance
pode, motivo = lance_service.verificar_pode_dar_lance(participante_id, leilao_id)

# Obter ranking dos participantes
ranking = lance_service.obter_ranking_participantes_leilao(leilao_id)
```

### EmailService

```python
# Enviar email para vencedor
email_service = EmailService()
sucesso = email_service.enviar_email_vencedor(leilao, participante, valor_lance)

# Notificar todos os vencedores pendentes
resultado = email_service.notificar_vencedores_pendentes(leilao_service)
```

## 🗃 Modelos de Dados

### Participante
- **id**: Chave primária
- **cpf**: CPF único (11 dígitos)
- **nome**: Nome completo
- **email**: Email único
- **data_nascimento**: Data de nascimento
- **data_cadastro**: Timestamp de cadastro

### Leilao
- **id**: Chave primária
- **nome**: Nome/descrição do leilão
- **lance_minimo**: Valor mínimo para lances
- **data_inicio**: Data/hora de início
- **data_termino**: Data/hora de término
- **status**: Estado atual (INATIVO/ABERTO/FINALIZADO/EXPIRADO)
- **participante_vencedor_id**: ID do vencedor (quando finalizado)

### Lance
- **id**: Chave primária
- **valor**: Valor do lance
- **data_lance**: Timestamp do lance
- **leilao_id**: Referência ao leilão
- **participante_id**: Referência ao participante

## ✅ Validações

O sistema implementa validações robustas através da classe `validators.py`:

### ValidadorParticipante
- **CPF**: Formato, 11 dígitos, não pode ser sequência igual
- **Email**: Formato válido usando `email-validator`
- **Nome**: Mínimo 2 caracteres
- **Idade**: Mínimo 18 anos

### ValidadorLeilao
- **Nome**: Mínimo 3 caracteres
- **Lance mínimo**: Número positivo
- **Datas**: Término posterior ao início, início não no passado

### ValidadorLance
- **Valor**: Número positivo obrigatório

## 🤝 Contribuição

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. **Execute os testes** para garantir que tudo funciona:
   ```bash
   pytest -v
   ```
4. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
5. Push para a branch (`git push origin feature/AmazingFeature`)
6. Abra um Pull Request

### Diretrizes para Contribuição

- **Cobertura de Testes**: Mantenha a cobertura acima de 95%
- **Documentação**: Documente novas funcionalidades
- **Regras de Negócio**: Respeite todas as regras implementadas
- **Testes de Integração**: Adicione testes de integração para novas features
- **Validações**: Implemente validações robustas para novos campos

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

---

## 🧪 Testes

O projeto possui uma suíte completa de testes automatizados com **98%+ de cobertura**.

### Tipos de Testes

#### **Testes Unitários**
- `test_participante_service.py`: Testa todas as funcionalidades do ParticipanteService
- `test_leilao_service.py`: Testa todas as funcionalidades do LeilaoService  
- `test_lance_service.py`: Testa todas as funcionalidades do LanceService
- `test_email_service.py`: Testa o sistema de notificações por email

#### **Testes de Integração**
- `integration/test_integration.py`: Testa cenários completos do sistema
- `integration/test_lance_integration.py`: Testa fluxos completos de lances
- `integration/test_participante_integration.py`: Testa integração participante-leilão

### Executando os Testes

```bash
# Todos os testes
pytest

# Com informações detalhadas
pytest -v

# Com cobertura de código
pytest --cov=src

# Apenas testes de um serviço específico
pytest tests/test_lance_service.py -v

# Apenas testes de integração
pytest tests/integration/ -v

# Teste específico de integração
pytest tests/integration/test_lance_integration.py -v
```

### Fixtures e Configuração

O sistema de testes utiliza fixtures avançadas:

- **`clean_database`**: Banco de dados limpo para cada teste
- **`cenario_leilao_aberto`**: Cenário completo com participantes e leilão aberto
- **`participante_valido`**: Participante válido para testes
- **`leilao_valido`**: Leilão válido para testes
- **`varios_leiloes`**: Múltiplos leilões para testes de listagem

### Cenários Testados

#### **Regras de Negócio**
- ✅ Validações de idade, CPF e email
- ✅ Transições de estados de leilões
- ✅ Regras de lances consecutivos
- ✅ Proteção de dados com lances

#### **Integração Completa**
- ✅ Ciclo completo de leilão (criação → abertura → finalização)
- ✅ Múltiplos participantes em múltiplos leilões
- ✅ Sistema de emails automáticos
- ✅ Relatórios e estatísticas

#### **Casos Extremos**
- ✅ Leilões sem lances (expiração)
- ✅ Tentativas de violação de regras
- ✅ Operações em leilões em diferentes estados
- ✅ Validações de integridade de dados

---

## 🔍 Features Avançadas

### Relatórios Disponíveis
- 📊 Estatísticas de leilões (total de lances, participantes únicos)
- 🥇 Ranking de participantes por leilão
- 📈 Histórico completo de lances
- 💰 Estatísticas financeiras por participante

### Sistema de Estados
```
INATIVO → ABERTO → FINALIZADO (com lances)
    ↓         ↓
EXPIRADO ← EXPIRADO (sem lances)
```

### Simulação de Lances
```python
# Simular lance antes de criar
resultado = lance_service.simular_lance(participante_id, leilao_id, valor)
if resultado['valido']:
    lance = lance_service.criar_lance(participante_id, leilao_id, valor)
```

---

**Desenvolvido com ❤️ em Python**