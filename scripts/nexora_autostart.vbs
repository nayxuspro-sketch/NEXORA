Set WshShell = CreateObject("WScript.Shell")
strAppDir = "C:\NEXORA"

' 1. Lancer le Backend Django (8008) de façon 100% invisible (0 = fenetre cachee)
WshShell.Run "cmd /c ""cd /d " & strAppDir & " && python manage.py runserver 127.0.0.1:8008""", 0, False

' 2. Attendre 3 secondes
WScript.Sleep 3000

' 3. Lancer le Frontend Next.js (3000) de façon 100% invisible (0 = fenetre cachee)
WshShell.Run "cmd /c ""cd /d " & strAppDir & "\frontend && npm run dev""", 0, False
