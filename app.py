from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, Session
from datetime import datetime, timedelta
from typing import Optional, List
import bcrypt as _bcrypt
from jose import JWTError, jwt
import uuid

# =================================================================
# 1. BANCO DE DADOS
# =================================================================
SQLALCHEMY_DATABASE_URL = "sqlite:///./raizes_nordeste.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# =================================================================
# 2. SEGURANÇA (JWT + BCrypt)
# =================================================================
SECRET_KEY = "raizes_nordeste_chave_secreta_2026"
ALGORITHM = "HS256"
TOKEN_EXPIRA_MINUTOS = 60

bearer_scheme = HTTPBearer()

# =================================================================
# 3. MODELOS DO BANCO (Tabelas)
# =================================================================
class Usuario(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    senha_hash = Column(String, nullable=False)
    perfil = Column(String, default="CLIENTE")          # ADMIN ou CLIENTE
    consentimento_lgpd = Column(Boolean, default=False)
    data_consentimento = Column(DateTime, nullable=True)
    criado_em = Column(DateTime, default=datetime.utcnow)

class Produto(Base):
    __tablename__ = "produtos"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    descricao = Column(String)
    preco = Column(Float, nullable=False)
    ativo = Column(Boolean, default=True)

class Pedido(Base):
    __tablename__ = "pedidos"
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    data_criacao = Column(DateTime, default=datetime.utcnow)
    valor_total = Column(Float, default=0.0)
    status = Column(String, default="AGUARDANDO_PAGAMENTO")
    canal_pedido = Column(String, nullable=False)       # APP, TOTEM, BALCAO
    forma_pagamento = Column(String, nullable=False)    # PIX, CARTAO, DINHEIRO

    usuario = relationship("Usuario")
    itens = relationship("ItemPedido", back_populates="pedido")
    pagamento = relationship("Pagamento", back_populates="pedido", uselist=False)

class ItemPedido(Base):
    __tablename__ = "itens_pedido"
    id = Column(Integer, primary_key=True, index=True)
    pedido_id = Column(Integer, ForeignKey("pedidos.id"), nullable=False)
    produto_id = Column(Integer, ForeignKey("produtos.id"), nullable=False)
    quantidade = Column(Integer, nullable=False)
    preco_unitario = Column(Float, nullable=False)

    pedido = relationship("Pedido", back_populates="itens")
    produto = relationship("Produto")

class Pagamento(Base):
    __tablename__ = "pagamentos"
    id = Column(Integer, primary_key=True, index=True)
    pedido_id = Column(Integer, ForeignKey("pedidos.id"), nullable=False)
    metodo = Column(String)
    status_mock = Column(String)   # APROVADO ou RECUSADO
    transacao_id = Column(String)
    data_processamento = Column(DateTime, default=datetime.utcnow)

    pedido = relationship("Pedido", back_populates="pagamento")

# Cria todas as tabelas no banco SQLite
Base.metadata.create_all(bind=engine)

# =================================================================
# 4. DEPENDENCY: SESSÃO DO BANCO
# =================================================================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# =================================================================
# 5. FUNÇÕES DE AUTENTICAÇÃO
# =================================================================
def hash_senha(senha: str) -> str:
    return _bcrypt.hashpw(senha.encode(), _bcrypt.gensalt()).decode()

def verificar_senha(senha: str, hash_armazenado: str) -> bool:
    return _bcrypt.checkpw(senha.encode(), hash_armazenado.encode())

def criar_token(email: str, perfil: str) -> str:
    expira = datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRA_MINUTOS)
    payload = {"sub": email, "perfil": perfil, "exp": expira}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def obter_usuario_logado(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db)
):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail={"error": "NAO_AUTENTICADO", "message": "Token inválido."})
    except JWTError:
        raise HTTPException(status_code=401, detail={"error": "NAO_AUTENTICADO", "message": "Token ausente ou inválido."})

    usuario = db.query(Usuario).filter(Usuario.email == email).first()
    if not usuario:
        raise HTTPException(status_code=401, detail={"error": "NAO_AUTENTICADO", "message": "Usuário não encontrado."})
    return usuario

# =================================================================
# 6. SCHEMAS (Contratos da API / Swagger)
# =================================================================
class RegistroSchema(BaseModel):
    nome: str
    email: str
    senha: str
    perfil: str = "CLIENTE"
    consentimento_lgpd: bool = False

class LoginSchema(BaseModel):
    email: str
    senha: str

class ProdutoCreate(BaseModel):
    nome: str
    descricao: str
    preco: float

class ItemSchema(BaseModel):
    produto_id: int
    quantidade: int

class PedidoCreate(BaseModel):
    canal_pedido: str       # APP, TOTEM, BALCAO
    forma_pagamento: str    # PIX, CARTAO, DINHEIRO
    itens: List[ItemSchema]

class AtualizarStatusSchema(BaseModel):
    status: str

# =================================================================
# 7. APP FASTAPI
# =================================================================
app = FastAPI(
    title="API Raízes do Nordeste",
    description="Sistema de pedidos da rede Raízes do Nordeste — Projeto Multidisciplinar Back-End",
    version="1.0.0"
)

# Handler global: garante que erros sempre retornem {"error": ..., "message": ...}
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    detail = exc.detail
    if isinstance(detail, dict):
        return JSONResponse(status_code=exc.status_code, content=detail)
    return JSONResponse(status_code=exc.status_code, content={"error": "ERRO", "message": str(detail)})

# =================================================================
# 8. ENDPOINTS — AUTH
# =================================================================
@app.post("/auth/registro", tags=["Auth"], summary="Registrar novo usuário", status_code=201)
def registro(dados: RegistroSchema, db: Session = Depends(get_db)):
    if db.query(Usuario).filter(Usuario.email == dados.email).first():
        raise HTTPException(400, {"error": "EMAIL_JA_CADASTRADO", "message": "E-mail já cadastrado."})

    perfis_validos = ["ADMIN", "CLIENTE"]
    if dados.perfil.upper() not in perfis_validos:
        raise HTTPException(400, {"error": "PERFIL_INVALIDO", "message": f"Perfil inválido. Use: {perfis_validos}"})

    novo_usuario = Usuario(
        nome=dados.nome,
        email=dados.email,
        senha_hash=hash_senha(dados.senha),
        perfil=dados.perfil.upper(),
        consentimento_lgpd=dados.consentimento_lgpd,
        data_consentimento=datetime.utcnow() if dados.consentimento_lgpd else None
    )
    db.add(novo_usuario)
    db.commit()
    return {"message": "Usuário cadastrado com sucesso."}


@app.post("/auth/login", tags=["Auth"], summary="Login — retorna token JWT")
def login(dados: LoginSchema, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.email == dados.email).first()
    if not usuario or not verificar_senha(dados.senha, usuario.senha_hash):
        raise HTTPException(401, {"error": "CREDENCIAIS_INVALIDAS", "message": "E-mail ou senha inválidos."})

    token = criar_token(usuario.email, usuario.perfil)
    return {"token": token}

# =================================================================
# 9. ENDPOINTS — PRODUTOS
# =================================================================
@app.post("/produtos", tags=["Produtos"], summary="Cadastrar produto", status_code=201)
def criar_produto(dados: ProdutoCreate, db: Session = Depends(get_db), usuario=Depends(obter_usuario_logado)):
    if dados.preco <= 0:
        raise HTTPException(400, {"error": "PRECO_INVALIDO", "message": "O preço deve ser maior que zero."})

    produto = Produto(nome=dados.nome, descricao=dados.descricao, preco=dados.preco)
    db.add(produto)
    db.commit()
    db.refresh(produto)
    return {"id": produto.id, "nome": produto.nome, "descricao": produto.descricao, "preco": produto.preco}


@app.get("/produtos", tags=["Produtos"], summary="Listar produtos ativos")
def listar_produtos(db: Session = Depends(get_db), usuario=Depends(obter_usuario_logado)):
    produtos = db.query(Produto).filter(Produto.ativo == True).all()
    return [{"id": p.id, "nome": p.nome, "descricao": p.descricao, "preco": p.preco} for p in produtos]

# =================================================================
# 10. ENDPOINTS — PEDIDOS
# =================================================================
CANAIS_VALIDOS = ["APP", "TOTEM", "BALCAO"]
STATUS_VALIDOS = ["AGUARDANDO_PAGAMENTO", "PAGAMENTO_APROVADO", "EM_PREPARO", "PRONTO", "ENTREGUE", "CANCELADO"]

@app.post("/pedidos", tags=["Pedidos"], summary="Criar pedido", status_code=201)
def criar_pedido(dados: PedidoCreate, db: Session = Depends(get_db), usuario=Depends(obter_usuario_logado)):
    # Validar campos obrigatórios
    campos_faltando = []
    if not dados.canal_pedido:
        campos_faltando.append("canal_pedido")
    if not dados.forma_pagamento:
        campos_faltando.append("forma_pagamento")
    if not dados.itens:
        campos_faltando.append("itens")
    if campos_faltando:
        raise HTTPException(400, {"error": "CAMPOS_OBRIGATORIOS", "message": f"Campos obrigatórios ausentes: {campos_faltando}"})

    if dados.canal_pedido.upper() not in CANAIS_VALIDOS:
        raise HTTPException(400, {"error": "CANAL_INVALIDO", "message": f"Canal inválido. Use: {CANAIS_VALIDOS}"})

    # Criar o pedido
    pedido = Pedido(
        usuario_id=usuario.id,
        status="AGUARDANDO_PAGAMENTO",
        canal_pedido=dados.canal_pedido.upper(),
        forma_pagamento=dados.forma_pagamento.upper(),
        valor_total=0.0
    )
    db.add(pedido)
    db.flush()  # obtém o id do pedido sem commitar ainda

    total = 0.0
    for item_dados in dados.itens:
        produto = db.query(Produto).filter(Produto.id == item_dados.produto_id, Produto.ativo == True).first()
        if not produto:
            db.rollback()
            raise HTTPException(404, {"error": "PRODUTO_NAO_ENCONTRADO", "message": f"Produto {item_dados.produto_id} não encontrado."})

        if item_dados.quantidade <= 0:
            db.rollback()
            raise HTTPException(400, {"error": "QUANTIDADE_INVALIDA", "message": "A quantidade deve ser maior que zero."})

        total += produto.preco * item_dados.quantidade
        item = ItemPedido(
            pedido_id=pedido.id,
            produto_id=produto.id,
            quantidade=item_dados.quantidade,
            preco_unitario=produto.preco
        )
        db.add(item)

    pedido.valor_total = round(total, 2)
    db.commit()
    db.refresh(pedido)

    return {
        "pedido_id": pedido.id,
        "status": pedido.status,
        "canal_pedido": pedido.canal_pedido,
        "forma_pagamento": pedido.forma_pagamento,
        "valor_total": pedido.valor_total,
        "status_pagamento": "PENDENTE"
    }


@app.get("/pedidos", tags=["Pedidos"], summary="Listar todos os pedidos")
def listar_pedidos(
    canal_pedido: Optional[str] = None,
    db: Session = Depends(get_db),
    usuario=Depends(obter_usuario_logado)
):
    query = db.query(Pedido)
    if canal_pedido:
        query = query.filter(Pedido.canal_pedido == canal_pedido.upper())
    pedidos = query.all()

    resultado = [
        {
            "id": p.id,
            "usuario_id": p.usuario_id,
            "status": p.status,
            "canal_pedido": p.canal_pedido,
            "forma_pagamento": p.forma_pagamento,
            "valor_total": p.valor_total,
            "data_criacao": p.data_criacao
        }
        for p in pedidos
    ]
    return {"total": len(resultado), "pedidos": resultado}


@app.get("/pedidos/{id}", tags=["Pedidos"], summary="Buscar pedido por ID")
def buscar_pedido(id: int, db: Session = Depends(get_db), usuario=Depends(obter_usuario_logado)):
    pedido = db.query(Pedido).filter(Pedido.id == id).first()
    if not pedido:
        raise HTTPException(404, {"error": "PEDIDO_NAO_ENCONTRADO", "message": "Pedido não encontrado."})

    itens = [
        {
            "produto_id": item.produto_id,
            "produto_nome": item.produto.nome,
            "quantidade": item.quantidade,
            "preco_unitario": item.preco_unitario,
            "subtotal": round(item.quantidade * item.preco_unitario, 2)
        }
        for item in pedido.itens
    ]

    return {
        "id": pedido.id,
        "usuario_id": pedido.usuario_id,
        "status": pedido.status,
        "canal_pedido": pedido.canal_pedido,
        "forma_pagamento": pedido.forma_pagamento,
        "valor_total": pedido.valor_total,
        "data_criacao": pedido.data_criacao,
        "itens": itens
    }


@app.patch("/pedidos/{id}/status", tags=["Pedidos"], summary="Atualizar status do pedido")
def atualizar_status(id: int, dados: AtualizarStatusSchema, db: Session = Depends(get_db), usuario=Depends(obter_usuario_logado)):
    pedido = db.query(Pedido).filter(Pedido.id == id).first()
    if not pedido:
        raise HTTPException(404, {"error": "PEDIDO_NAO_ENCONTRADO", "message": "Pedido não encontrado."})

    if dados.status.upper() not in STATUS_VALIDOS:
        raise HTTPException(400, {"error": "STATUS_INVALIDO", "message": f"Status inválido. Use: {STATUS_VALIDOS}"})

    pedido.status = dados.status.upper()
    db.commit()
    return {"pedido_id": pedido.id, "novo_status": pedido.status}

# =================================================================
# 11. ENDPOINTS — PAGAMENTOS
# =================================================================
@app.post("/pagamentos/processar/{id}", tags=["Pagamentos"], summary="Processar pagamento (mock)")
def processar_pagamento(id: int, db: Session = Depends(get_db), usuario=Depends(obter_usuario_logado)):
    pedido = db.query(Pedido).filter(Pedido.id == id).first()
    if not pedido:
        raise HTTPException(404, {"error": "PEDIDO_NAO_ENCONTRADO", "message": "Pedido não encontrado."})

    if pedido.status != "AGUARDANDO_PAGAMENTO":
        raise HTTPException(409, {"error": "STATUS_INVALIDO", "message": "Pedido não está aguardando pagamento."})

    # Regra do gateway mock: aprova até R$ 1000, recusa acima
    transacao_id = str(uuid.uuid4())
    if pedido.valor_total <= 1000.0:
        status_pagamento = "APROVADO"
        novo_status_pedido = "PAGAMENTO_APROVADO"
        mensagem = "Pagamento aprovado com sucesso."
    else:
        status_pagamento = "RECUSADO"
        novo_status_pedido = "CANCELADO"
        mensagem = "Pagamento recusado: valor acima do limite permitido."

    pagamento = Pagamento(
        pedido_id=pedido.id,
        metodo=pedido.forma_pagamento,
        status_mock=status_pagamento,
        transacao_id=transacao_id
    )
    db.add(pagamento)
    pedido.status = novo_status_pedido
    db.commit()

    return {
        "status_pagamento": status_pagamento,
        "pedido_id": pedido.id,
        "novo_status_pedido": novo_status_pedido,
        "mensagem": mensagem,
        "transacao_id": transacao_id
    }
