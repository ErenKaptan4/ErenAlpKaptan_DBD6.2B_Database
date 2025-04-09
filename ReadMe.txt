Setup

1. installed and opened PyCharm from JetBrains Toolbox and creating the project
2. Made github repo from PyCharm and committed/pushed the Project
3. Installed packages to make the environment be able to run
python -m venv env 
source env/bin/activate
pip install fastapi
pip install uvicorn
pip install motor
pip install pydantic
pip install python-dotenv
pip install requests
4. Make sure every package is there
pip freeze > requirements.txt
5. Setup the database, get the connection string and the password from MongoDB
6. Used it in the pre-given code
7. For testing purposes, run the code locally by choosing FastAPI to run the code
8. Open postman to test the POST endpoints
