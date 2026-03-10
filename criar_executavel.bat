@echo off
echo ============================================================
echo   Criando executavel do Gerador de Peticoes...
echo ============================================================
echo.

pip install pyinstaller python-docx openpyxl

echo.
echo Gerando executavel...
echo.

pyinstaller --noconfirm --onefile --windowed --name "Gerador de Peticoes" --icon NONE executavel.py

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
