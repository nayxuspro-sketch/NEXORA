Set WshShell = CreateObject("WScript.Shell")
strPath = WshShell.CurrentDirectory

' 1. Lancer le Backend Django en arriere-plan complet (0 = cache)
WshShell.Run "cmd /c ""cd /d """ & strPath & """ && call .venv\Scripts\activate.bat && python manage.py runserver 0.0.0.0:8000""", 0, False

' 2. Attendre 2 secondes que Django s'initialise
WScript.Sleep 2000

' 3. Lancer le Frontend Next.js en arriere-plan complet (0 = cache)
WshShell.Run "cmd /c ""cd /d """ & strPath & "\frontend"" && npm run dev""", 0, False
