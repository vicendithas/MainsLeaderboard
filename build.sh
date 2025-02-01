wine pip install flask waitress 

wine pyinstaller --noconfirm --onefile --console \
    --icon "Z:\app\static\favicon.ico" \
    --add-data "Z:\app\static;static/"  "Z:\app\server.py"