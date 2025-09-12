#!/usr/bin/env python3
"""
Script para criar versões genéricas das regras do projeto.
"""
import os
from pathlib import Path

def create_generic_clean_architecture():
    """Cria versão genérica da regra de Clean Architecture."""
    content = """---
description: Clean Architecture agnóstica - separação de responsabilidades e dependências
globs: ["src/**/*", "app/**/*", "lib/**/*", "packages/**/*", "domain/**/*"]
alwaysApply: true
---

## Objetivo
Manter a integridade da Clean Architecture em qualquer projeto, garantindo que cada camada tenha responsabilidades bem definidas e que as dependências fluam corretamente do exterior para o interior.

## 🚀 Quick Reference

### **Fluxo de Dependências (Sempre do exterior para o interior):**
```
Presentation → Application → Domain
    ↓    ↓    ↑
Infrastructure ←────┘    │
    ↑    │
Utils/Shared ←────┘
```

### **Regras Essenciais:**
- ✅ **Domain**: Independente de tudo, apenas entidades e regras de negócio
- ✅ **Application**: Coordena casos de uso, injeta dependências
- ✅ **Infrastructure**: Implementa interfaces, acessa dados externos
- ✅ **Presentation**: Interface com usuário, chama use cases
- ❌ **NUNCA**: Domain importar de outras camadas

### **Padrões Recomendados:**
- **Repository Pattern**: Para acesso a dados
- **Factory Pattern**: Para criação de objetos
- **Dependency Injection**: Para desacoplamento
- **Use Case Pattern**: Para casos de uso específicos

## Estrutura de Camadas (Agnóstica)

### 📁 Domain (src/domain/ ou domain/)
**Responsabilidade**: Entidades de negócio, modelos, exceções e interfaces
- ✅ **PODE**: Definir modelos de dados, exceções de negócio, interfaces, regras de negócio puras
- ❌ **NÃO PODE**: Importar de outras camadas, acessar banco de dados, fazer I/O, depender de frameworks

```python
# ✅ CORRETO - Exemplos genéricos
@dataclass
class User:
    id: str
    email: str
    created_at: datetime

@dataclass
class Product:
    id: str
    name: str
    price: Decimal
    category: str

class DomainError(Exception):
    pass

# ❌ INCORRETO - não importar de outras camadas
from src.infrastructure.database import Database  # ERRADO!
from src.application.services import UserService  # ERRADO!
```

### 📁 Application/Services (src/application/ ou src/services/)
**Responsabilidade**: Casos de uso, lógica de aplicação e orquestração
- ✅ **PODE**: Importar do domain, coordenar operações, implementar casos de uso
- ❌ **NÃO PODE**: Acessar dados diretamente, depender de detalhes de implementação

```python
# ✅ CORRETO - Exemplos genéricos
class CreateUserUseCase:
    def __init__(self, user_repo: UserRepository, validator: UserValidator):
        self.user_repo = user_repo
        self.validator = validator

    def execute(self, user_data: dict) -> User:
        self.validator.validate(user_data)
        user = User(**user_data)
        return self.user_repo.save(user)

# ❌ INCORRETO - acesso direto a dados
def create_user(self, user_data: dict):
    with open('users.json') as f:  # ERRADO! Acesso direto a arquivo
        data = f.read()
```

### 📁 Infrastructure (src/infrastructure/ ou src/adapters/)
**Responsabilidade**: Implementações concretas, acesso a dados, APIs externas
- ✅ **PODE**: Implementar interfaces do domain, acessar banco de dados, fazer I/O, integrar APIs
- ❌ **NÃO PODE**: Conter lógica de negócio, depender de services diretamente

```python
# ✅ CORRETO
class DatabaseUserRepository(UserRepository):
    def save(self, user: User) -> User:
        # Implementação específica do banco
        pass

    def find_by_id(self, user_id: str) -> Optional[User]:
        # Query específica
        pass

# ❌ INCORRETO - lógica de negócio no repository
def save_with_validation(self, user: User):
    if self.is_email_unique(user.email):  # ERRADO! Lógica de negócio
        # Validação deve estar no domain/application
```

### 📁 Presentation (src/presentation/ ou src/controllers/)
**Responsabilidade**: Interface com usuário, APIs, controladores
- ✅ **PODE**: Receber requests, chamar use cases, formatar responses
- ❌ **NÃO PODE**: Implementar lógica de negócio, acessar dados diretamente

```python
# ✅ CORRETO
class UserController:
    def __init__(self, create_user_use_case: CreateUserUseCase):
        self.create_user_use_case = create_user_use_case

    def create_user(self, request_data: dict) -> dict:
        user = self.create_user_use_case.execute(request_data)
        return {"id": user.id, "email": user.email}

# ❌ INCORRETO - lógica de negócio no controller
def create_user(self, request_data: dict):
    if len(request_data['email']) < 5:  # Validação deve estar no domain!
```

### 📁 Utils/Shared (src/utils/ ou src/shared/)
**Responsabilidade**: Utilitários puros, helpers, funções auxiliares
- ✅ **PODE**: Implementar funções puras, formatação, cálculos genéricos
- ❌ **NÃO PODE**: Depender de outras camadas específicas, ter estado

```python
# ✅ CORRETO
def format_currency(value: float, currency: str = "USD") -> str:
    return f"{currency} {value:,.2f}"

def generate_uuid() -> str:
    return str(uuid.uuid4())

# ❌ INCORRETO - dependência específica
def format_user_display(user: User):  # Deveria estar no domain ou application
```

## Regras de Dependência (Dependency Rule)

### ✅ Fluxo Correto de Dependências:
```
Presentation → Application/Services → Domain
    ↓    ↓    ↑
Infrastructure ←────┘    │
    ↑    │
Utils/Shared ←────┘
```

### Princípios Fundamentais:
1. **Camadas internas não conhecem camadas externas**
2. **Domain é independente de tudo**
3. **Application coordena mas não implementa detalhes**
4. **Infrastructure implementa interfaces definidas no Domain**
5. **Presentation apenas orquestra chamadas**

### ❌ Dependências Proibidas:
- Domain → Application/Services
- Domain → Infrastructure  
- Domain → Presentation
- Application → Infrastructure (apenas via interfaces)
- Application → Presentation

## Padrões de Implementação

### Dependency Injection:
```python
# ✅ CORRETO - Injeção via construtor
class OrderService:
    def __init__(self, 
                 order_repo: OrderRepository,
                 payment_service: PaymentService,
                 notification_service: NotificationService):
        self.order_repo = order_repo
        self.payment_service = payment_service
        self.notification_service = notification_service
```

### Repository Pattern:
```python
# ✅ CORRETO - Interface no Domain
class UserRepository(ABC):
    @abstractmethod
    def save(self, user: User) -> User:
        pass

    @abstractmethod
    def find_by_email(self, email: str) -> Optional[User]:
        pass

# Implementação na Infrastructure
class SQLUserRepository(UserRepository):
    def save(self, user: User) -> User:
        # Implementação específica
        pass
```

### Use Case Pattern:
```python
# ✅ CORRETO - Caso de uso específico
class AuthenticateUserUseCase:
    def __init__(self, user_repo: UserRepository, password_hasher: PasswordHasher):
        self.user_repo = user_repo
        self.password_hasher = password_hasher

    def execute(self, email: str, password: str) -> AuthResult:
        user = self.user_repo.find_by_email(email)
        if not user or not self.password_hasher.verify(password, user.password_hash):
            raise AuthenticationError("Invalid credentials")
        return AuthResult(user=user, token=self.generate_token(user))
```

## Validação da Arquitetura

### Checklist por Camada:

**Domain:**
- ✅ Apenas entidades, value objects, exceções e interfaces
- ✅ Zero imports de outras camadas do projeto
- ✅ Regras de negócio puras
- ✅ Type hints obrigatórios

**Application/Services:**
- ✅ Implementa casos de uso específicos
- ✅ Recebe dependências via injeção
- ✅ Coordena operações sem implementar detalhes
- ✅ Usa interfaces, não implementações concretas

**Infrastructure:**
- ✅ Implementa interfaces definidas no Domain
- ✅ Contém apenas código de acesso a dados/APIs
- ✅ Isolada de lógica de negócio
- ✅ Configurações específicas de tecnologia

**Presentation:**
- ✅ Apenas recebe input e formata output
- ✅ Chama use cases via injeção
- ✅ Não contém lógica de negócio
- ✅ Trata apenas aspectos de apresentação

## Testes por Camada

### Domain (Testes Unitários):
```python
def test_user_creation():
    user = User(id="123", email="test@example.com")
    assert user.is_valid()

def test_invalid_email_raises_exception():
    with pytest.raises(InvalidUserError):
        User(id="123", email="invalid-email")
```

### Application (Testes de Integração com Mocks):
```python
def test_create_user_use_case():
    mock_repo = Mock(spec=UserRepository)
    use_case = CreateUserUseCase(mock_repo)

    result = use_case.execute({"email": "test@example.com"})

    mock_repo.save.assert_called_once()
    assert result.email == "test@example.com"
```

### Infrastructure (Testes de Integração):
```python
def test_database_user_repository():
    repo = DatabaseUserRepository(connection)
    user = User(id="123", email="test@example.com")

    saved_user = repo.save(user)
    found_user = repo.find_by_id("123")

    assert saved_user == found_user
```

## Violações Comuns a Evitar

1. **Domain importando de outras camadas**
2. **Services acessando dados diretamente**
3. **Controllers com lógica de negócio**
4. **Repositories com regras de validação**
5. **Entidades dependendo de frameworks**
6. **Use cases retornando DTOs específicos de apresentação**
7. **Infrastructure vazando para camadas internas**

## Sinais de Violação da Arquitetura

### 🚨 Red Flags:
- Import de camadas externas no Domain
- Lógica de negócio em Controllers/Repositories
- Acesso direto a banco de dados em Services
- Dependências circulares entre camadas
- Entidades com anotações de framework
- Use cases conhecendo detalhes de HTTP/Database

### ✅ Indicadores de Boa Arquitetura:
- Domain completamente independente
- Testes unitários rápidos no Domain
- Fácil substituição de Infrastructure
- Use cases testáveis com mocks
- Separação clara de responsabilidades

## Refatoração de Violações

Quando encontrar violações:
1. **Identifique a camada correta** para a responsabilidade
2. **Extraia interfaces** se necessário (Domain)
3. **Mova implementações** para Infrastructure
4. **Injete dependências** via construtor
5. **Atualize testes** para refletir a nova estrutura
6. **Documente mudanças** no histórico de desenvolvimento

## 🔄 Guia de Refatoração Gradual

### **Passo 1: Identificar Violações**
```bash
# Encontrar imports incorretos no Domain
grep -r "from src\." src/domain/ --include="*.py"
grep -r "import src\." src/domain/ --include="*.py"
```

### **Passo 2: Extrair Interfaces**
```python
# Antes: Dependência direta
class Service:
    def __init__(self):
        self.repository = DatabaseRepository()  # ERRADO!

# Depois: Injeção de dependência
class Service:
    def __init__(self, repository: Repository):
        self.repository = repository  # CORRETO!
```

### **Passo 3: Mover Lógica de Negócio**
```python
# Antes: Lógica no Repository
class UserRepository:
    def save(self, user):
        if user.email == "":  # ERRADO! Lógica de negócio
            raise ValueError("Email is required")

# Depois: Lógica no Domain
class User:
    def __init__(self, email: str):
        if not email:
            raise InvalidUserError("Email is required")
        self.email = email
```

### **Passo 4: Implementar Factory Pattern**
```python
# Antes: Criação direta
def process_data(data: str):
    repository = DatabaseRepository()  # ERRADO! Acoplamento forte
    service = DataService()

# Depois: Factory Pattern
def process_data(data: str):
    repository = ComponentFactory.get_repository()
    service = ComponentFactory.get_service()
```

## Ferramentas de Validação

### Análise Estática:
```python
# Exemplo de regra para linter personalizado
def check_domain_imports(file_path: str) -> List[str]:
    if 'domain' in file_path:
        # Verificar se há imports de outras camadas
        violations = []
        # Implementar verificação
        return violations
```

### Testes Arquiteturais:
```python
def test_domain_has_no_external_dependencies():
    domain_files = get_files_in_package('src.domain')
    for file in domain_files:
        imports = get_imports(file)
        external_imports = [i for i in imports if i.startswith('src.') and 'domain' not in i]
        assert len(external_imports) == 0, f"Domain file {file} has external dependencies: {external_imports}"
```

Esta regra garante que qualquer projeto mantenha os princípios da Clean Architecture independente da tecnologia ou domínio específico.
"""
    return content

def main():
    """Função principal."""
    print("🚀 Criando versões genéricas das regras...")
    
    # Criar diretório para regras genéricas
    generic_dir = Path("rules_generic")
    generic_dir.mkdir(exist_ok=True)
    
    # Criar regra genérica de Clean Architecture
    with open(generic_dir / "clean_architecture.mdc", "w", encoding="utf-8") as f:
        f.write(create_generic_clean_architecture())
    
    print("✅ Regras genéricas criadas em: rules_generic/")
    print("📁 Arquivos gerados:")
    print("  - clean_architecture.mdc (versão genérica)")
    print("")
    print("💡 Estas regras podem ser usadas em qualquer projeto!")

if __name__ == "__main__":
    main()
