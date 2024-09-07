@echo off
REM Démarrer Docker Desktop
start "Docker Desktop" "C:\Program Files\Docker\Docker\Docker Desktop.exe"

REM Attendre que Docker Desktop soit démarré
:wait_for_docker
echo Attente du démarrage de Docker Desktop...
timeout /t 5 /nobreak >nul
docker info >nul 2>&1
if errorlevel 1 (
    goto wait_for_docker
)
echo Docker Desktop est démarré.

REM Démarrer un conteneur Docker Grafana
start "Docker Container" cmd /k "docker start grafana_3001"

REM Chemin vers l'installation d'Anaconda
set CONDA_PATH=C:\Users\%USERNAME%\Anaconda3

REM Ajouter Anaconda au PATH
set PATH=%CONDA_PATH%;%CONDA_PATH%\Scripts;%CONDA_PATH%\Library\bin;%PATH%

REM Activer l'environnement conda
CALL conda.bat activate ANIMOV_Yolo

REM Répertoire de base
set BASE_DIR=%~dp0

cd /d %BASE_DIR%E3\api_flask
REM Démarrer le serveur mlflow
start "MLflow Server" cmd /k "CALL conda.bat activate ANIMOV_Yolo && mlflow server --backend-store-uri sqlite:///./mlflow.db --default-artifact-root ./mlflow-artifacts --host localhost --port 5000"

REM API E5
cd /d %BASE_DIR%E5
start "API E5" cmd /k "CALL conda.bat activate ANIMOV_Yolo && python api.py"

REM API E3E4
cd /d %BASE_DIR%E4\API
start "API E4" cmd /k "CALL conda.bat activate ANIMOV_Yolo && python api_data_animov.py"

REM Démarrer l'API Flask
cd /d %BASE_DIR%E3\api_flask
REM start "API Flask" cmd /k "CALL conda.bat activate ANIMOV_Yolo && python appjwt_refactoring_gpu.py"
start "API Flask" cmd /k "CALL conda.bat activate ANIMOV_Yolo && python appjwt.py"

REM Démarrer l'application Streamlit
cd /d %BASE_DIR%E3\app
start "Streamlit App IA" cmd /k "CALL conda.bat activate ANIMOV_Yolo && streamlit run app.py"

REM Démarrer l'application Streamlit
cd /d %BASE_DIR%E4\Streamlit
start "Streamlit App EDA" cmd /k "CALL conda.bat activate ANIMOV_Yolo && streamlit run Accueil.py --server.port 8502"

REM Démarrer l'application Streamlit
cd /d %BASE_DIR%E5
start "demon" cmd /k "CALL conda.bat activate ANIMOV_Yolo && python demon.py"
	
REM Ouvrir l'URL spécifique dans le navigateur
start "" "http://localhost:3001/public-dashboards/cb39155f86d3468fb72a2a83cbf123f7?orgId=1&refresh=5s"

REM Ouvrir l'URL http://127.0.0.1:5000 dans le navigateur par défaut
start "" "http://127.0.0.1:5000"

REM Ouvrir l'URL http://127.0.0.1:5500 dans le navigateur par défaut
start "" "http://127.0.0.1:5500/apidocs"

REM Ouvrir l'URL http://127.0.0.1:5100 dans le navigateur par défaut
start "" "http://127.0.0.1:5100/apidocs"

REM Ouvrir l'URL http://127.0.0.1:5002 dans le navigateur par défaut
start "" "http://127.0.0.1:5002/manage"

REM Répertoire racine du projet
cd /d %BASE_DIR%
start "ANIMOV_Yolo conda"
