Instruções para Execução Local Para testar e rodar a API em um ambiente de desenvolvimento local, é necessário possuir o Python instalado. O passo a passo para a execução do servidor é: 

Clonar o repositório em uma pasta local. 

Abrir o terminal na raiz do projeto e criar um ambiente virtual (ex: python -m venv venv). 

Ativar o ambiente virtual e instalar as dependências do projeto executando o comando: pip install fastapi uvicorn sqlalchemy bcrypt python-jose. 

Iniciar o servidor local de desenvolvimento através do Uvicorn utilizando o comando: uvicorn app:app --reload. (Nota: O banco de dados SQLite raizes_nordeste.db será recriado automaticamente na primeira execução caso não exista). 

8.3. Acesso à Documentação Interativa (Swagger/OpenAPI) Atendendo aos requisitos não funcionais de padronização, a API foi construída com o framework FastAPI, que gera a documentação dos endpoints de forma nativa e automática. 

Com o servidor em execução (porta padrão 8000), a interface gráfica para testes e consulta de rotas pode ser acessada através de qualquer navegador web na seguinte URL: 

Interface Swagger UI: http://127.0.0.1:8000/docs 


Através desta interface interativa, o avaliador poderá simular todos os cenários descritos no Plano de Testes (Capítulo 7) de forma direta, injetando o token JWT e disparando requisições reais contra o banco de dados sem a necessidade de instalar clients de API externos, como Postman ou Insomnia. 

 
