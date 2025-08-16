wine pip install flask waitress 

wine pyinstaller --noconfirm --onedir --console \
    --icon "Z:\app\static\favicon.ico" \
    --add-data "Z:\app\static;static/" \
    "Z:\app\server.py"

chmod 777 /app/dist/server.exe
chmod 777 /app/dist