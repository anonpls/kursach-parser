# Как восстановить DOCX-файлы из base64

Веб-интерфейс Codex/GitHub может не поддерживать бинарные `.docx` в PR. Поэтому рядом добавлены текстовые base64-копии документов:

- `coursework.docx.b64` — курсовая работа;
- `review.docx.b64` — рецензия.

## Восстановление на Windows PowerShell

Скачайте или скопируйте файлы `.b64`, затем выполните в папке с ними:

```powershell
[IO.File]::WriteAllBytes("Курсовая.docx", [Convert]::FromBase64String((Get-Content .\coursework.docx.b64 -Raw)))
[IO.File]::WriteAllBytes("Рецензия.docx", [Convert]::FromBase64String((Get-Content .\review.docx.b64 -Raw)))
```

После этого появятся обычные файлы Word: `Курсовая.docx` и `Рецензия.docx`.

## Восстановление на Linux/macOS

```bash
base64 -d artifacts/coursework.docx.b64 > Курсовая.docx
base64 -d artifacts/review.docx.b64 > Рецензия.docx
```

## Проверка

Откройте восстановленные `.docx` в Microsoft Word, LibreOffice Writer или OnlyOffice.
