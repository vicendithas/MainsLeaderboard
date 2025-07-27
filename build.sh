wine pip install flask waitress 

wine pyinstaller --noconfirm --onefile --console \
    --icon "Z:\app\static\favicon.ico" \
    --add-data "Z:\app\static;static/" \
    --add-data "Z:\app\config.json;config.json" \
    "Z:\app\server.py"

chmod 777 /app/dist/server.exe
chmod 777 /app/dist