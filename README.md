# Raízes do Nordeste — API Back-End

API REST desenvolvida com FastAPI para o sistema de pedidos da rede Raízes do Nordeste.  
Projeto Multidisciplinar — Trilha Back-End — UNINTER.

---

## Pré-requisitos

- Python 3.12+
- pip

---

## Instalação e execução

```bash
# 1. Clone o repositório
git clone https://github.com/JardelTech/raizes-projeto-final.git
cd raizes-projeto-final

# 2. Crie e ative o ambiente virtual
python -m venv venv
source venv/bin/activate        # Linux/Mac
# venv\Scripts\activate         # Windows

# 3. Instale as dependências
pip install fastapi uvicorn sqlalchemy bcrypt "python-jose[cryptography]"

# 4. Inicie o servidor
uvicorn app:app --reload
```

> O banco de dados SQLite (`raizes_nordeste.db`) é criado automaticamente na primeira execução.

---

## Configuração de ambiente

A chave secreta JWT está definida diretamente em `app.py` (`SECRET_KEY`).  
Para produção, mova para uma variável de ambiente:

```bash
export SECRET_KEY="sua_chave_secreta_aqui"
```

---

## Documentação interativa (Swagger)

Com o servidor rodando, acesse:

```
http://127.0.0.1:8000/docs
```

---

## Coleção de testes (Postman)

O arquivo `postman_collection.json` na raiz do repositório contém **30 cenários de teste** organizados em 4 pastas:

| Pasta | Requests |
|---|---|
| Auth | 6 (T01–T03 + E01–E03) |
| Produtos | 6 (T04–T06 + E04–E05 + E12) |
| Pedidos | 14 (T07–T15 + E06–E09 + E13) |
| Pagamentos | 4 (T16–T17 + E10–E11) |

**Como usar:**
1. Importe `postman_collection.json` no Postman
2. Execute **T02** (registro ADMIN) e **T01** (registro CLIENTE)
3. Execute o login de cada perfil e copie os tokens
4. Cole os tokens nos requests correspondentes (ADMIN para T04, T05, T13–T15; CLIENTE nos demais)

---

## Endpoints disponíveis

| Método | Rota | Perfil | Descrição |
|---|---|---|---|
| POST | `/auth/registro` | Público | Cadastrar usuário |
| POST | `/auth/login` | Público | Login — retorna JWT |
| POST | `/produtos` | **ADMIN** | Cadastrar produto |
| GET | `/produtos` | Autenticado | Listar produtos ativos |
| POST | `/pedidos` | Autenticado | Criar pedido |
| GET | `/pedidos` | Autenticado | Listar pedidos (filtro por canal) |
| GET | `/pedidos/{id}` | Autenticado | Buscar pedido por ID |
| PATCH | `/pedidos/{id}/status` | **ADMIN** | Atualizar status do pedido |
| POST | `/pagamentos/processar/{id}` | Autenticado | Processar pagamento (mock) |

---

## Regras de negócio principais

- Pedidos aceitos nos canais: `APP`, `TOTEM`, `BALCAO`
- Pagamento mock: aprovado se valor ≤ R$ 1.000,00; recusado se > R$ 1.000,00
- Senhas armazenadas com bcrypt
- Autenticação via JWT (Bearer Token, validade de 60 minutos)
- Perfis: `ADMIN` (gestão de produtos e status) e `CLIENTE` (pedidos e pagamentos)
- Consentimento LGPD registrado com timestamp no cadastro
