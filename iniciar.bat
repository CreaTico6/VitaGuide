@echo off
title VitaGuide - Inicializador Automático
color 0B

:: Forçar o terminal a posicionar-se na pasta deste ficheiro .bat
cd /d "%~dp0"

echo ======================================================================
echo                 VITAGUIDE - INICIALIZACAO AUTOMATICA
echo ======================================================================
echo.

set "PYTHON_CMD="

:: 1. Tentar 'python' direto no PATH
python --version >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_CMD=python"
    goto :found_python
)

:: 2. Tentar 'py' (Python Launcher padrão do Windows)
py --version >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_CMD=py"
    goto :found_python
)

:: 3. Procurar no caminho específico onde o teu sistema instalou o pythoncore
if exist "%USERPROFILE%\AppData\Local\Python\pythoncore-3.14-64\python.exe" (
    set "PYTHON_CMD=%USERPROFILE%\AppData\Local\Python\pythoncore-3.14-64\python.exe"
    goto :found_python
)

:: 4. Procurar noutras possíveis subpastas pythoncore em AppData
for /d %%d in ("%USERPROFILE%\AppData\Local\Python\pythoncore*") do (
    if exist "%%d\python.exe" (
        set "PYTHON_CMD=%%d\python.exe"
        goto :found_python
    )
)

:: 5. Procurar em caminhos padrão de utilizador (Programs\Python)
for /d %%d in ("%USERPROFILE%\AppData\Local\Programs\Python\Python*") do (
    if exist "%%d\python.exe" (
        set "PYTHON_CMD=%%d\python.exe"
        goto :found_python
    )
)

:: 6. Procurar no Program Files geral
for /d %%d in ("%ProgramFiles%\Python*") do (
    if exist "%%d\python.exe" (
        set "PYTHON_CMD=%%d\python.exe"
        goto :found_python
    )
)

:found_python
if "%PYTHON_CMD%"=="" (
    echo [ERRO CRITICO] O Python nao esta instalado ou nao foi encontrado!
    echo.
    echo Certifique-se de que instalou o Python 3.8+ corretamente.
    echo.
    pause
    exit /b
)

:: Determinar o executável sem consola correspondente (pythonw)
if "%PYTHON_CMD%"=="python" (
    set "PYTHONW_CMD=pythonw"
) else if "%PYTHON_CMD%"=="py" (
    set "PYTHONW_CMD=pyw"
) else (
    set "PYTHONW_CMD=%PYTHON_CMD:.exe=w.exe%"
)

echo [OK] Interpretador Python localizado: %PYTHON_CMD%
echo.

:: 2. Instalar ou atualizar as dependências de forma silenciosa
echo [1/3] A verificar e instalar dependencias (openpyxl, reportlab)...
"%PYTHON_CMD%" -m pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo [AVISO] Nao foi possivel verificar/instalar dependencias automaticamente.
    echo A tentar continuar a inicializacao...
) else (
    echo [OK] Dependencias instaladas e atualizadas com sucesso!
)
echo.

:: 3. Compilar o ficheiro Excel para JSON
echo [2/3] A converter a tabela Excel para a base de dados do sistema...
"%PYTHON_CMD%" scripts/build_dataset.py
if errorlevel 1 (
    echo [ERRO CRITICO] Falha ao compilar a Tabela de Interacoes!
    echo Verifique se o ficheiro TabelaInteracoes_2.xlsx ou TabelaInteracoes.xlsx
    echo existe na pasta raiz do seu projeto.
    echo.
    pause
    exit /b
)
echo.

:: 4. Iniciar a aplicação
echo [3/3] A arrancar o painel do VitaGuide no balcao...
start "" "%PYTHONW_CMD%" app.pyw

echo.
echo ======================================================================
echo [SUCESSO] O VitaGuide foi iniciado! Pode fechar esta janela preta.
echo ======================================================================
timeout /t 3 >nul
timeout /t 3 >nul