@echo off
echo ============================================================
echo   Criando executavel do Gerador de Peticoes...
echo ============================================================
echo.

echo Instalando dependencias...
python -m pip install pyinstaller python-docx openpyxl
echo.

echo Gerando executavel...
echo.

python -m PyInstaller --noconfirm --onefile --windowed --name "Gerador de Peticoes" executavel.py

echo.
echo ============================================================
if exist "dist\Gerador de Peticoes.exe" (
    echo   SUCESSO! O executavel foi criado em:
    echo   dist\Gerador de Peticoes.exe
    echo.
    echo   Copie esse arquivo para qualquer pasta e execute
    echo   com duplo clique.
) else (
    echo   ERRO: O executavel nao foi criado.
    echo   Verifique as mensagens acima.
)
echo ============================================================
echo.
pause
