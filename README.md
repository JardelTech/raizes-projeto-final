# API Raízes do Nordeste - Projeto Back-End

Olá! Seja bem-vindo(a) ao repositório da API do **Raízes do Nordeste**. Este projeto foi desenvolvido para a entrega final do Projeto Multidisciplinar (Trilha Back-End) da Uninter. 

# Como rodar o projeto na sua máquina?

É super simples! Você só precisa ter o **Python** instalado. Segue o passo a passo:

1. Faça o clone deste repositório para uma pasta local no seu computador.
2. Abra o terminal lá na raiz do projeto e crie um ambiente virtual (para não misturar as bibliotecas do seu PC):
   `python -m venv venv`
3. Ative o ambiente virtual e instale as dependências que usei no projeto:
   `pip install fastapi uvicorn sqlalchemy bcrypt python-jose`
4. Dê o play no servidor local:
   `uvicorn app:app --reload`
   
*(Ah, um detalhe importante: não precisa se preocupar em criar o banco de dados na mão! O código já mapeia tudo pelo SQLAlchemy e cria o arquivo `raizes_nordeste.db` automaticamente na primeira vez que você rodar a aplicação).*

## Testando a API pelo navegador (Swagger)

Como escolhi construir a API com o framework **FastAPI**, a documentação interativa já nasce pronta. 

Com o servidor rodando aí no seu terminal, é só clicar no link abaixo ou colar no seu navegador para ver todas as rotas e testar tudo de forma visual:
👉 **Interface Swagger:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

##  Plano de Testes (Postman)

Para facilitar a correção e mostrar todas as regras de negócio funcionando certinho (os cenários de sucesso e as travas de erro), deixei o arquivo `postman_collection.json` salvo aqui na raiz do projeto. 

**Como usar:**
1. Importe o arquivo no seu Postman (ou Insomnia).
2. Comece rodando o cenário **T01** para cadastrar o primeiro usuário.
3. Faça o Login (**T03**), copie o token gerado e não esqueça de colocar nas requisições que exigem autenticação. Divirta-se testando!
