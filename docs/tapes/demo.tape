Output "docs/images/demo.gif"

Set FontSize 40
Set TypingSpeed 30ms
Set Width 1800
Set Height 900

Sleep 300ms
Type "pydocfix check docs/tapes/example.py"
Enter
Sleep 3s

Ctrl+L

Sleep 300ms
Type "pydocfix check docs/tapes/example.py --diff --unsafe-fixes"
Enter
Sleep 3s
