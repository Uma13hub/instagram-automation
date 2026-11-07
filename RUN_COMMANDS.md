# Run Commands (Windows PowerShell)

## 1. Open the project folder
```powershell
cd C:\Users\Admin\Downloads\Open_Insta
```

## 2. One-time setup
```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy config.example.json config.json
notepad config.json
```
Put your real Instagram username and password in `config.json`, save and close.

## 3. READ (changes nothing, run these first)
```powershell
python main.py read profile
python main.py read posts --limit 3
python main.py read reels --limit 3
python main.py read followers --limit 10
python main.py read comments --url "https://www.instagram.com/p/DfbH4FYTmbK/?utm_source=ig_web_copy_link&cplk=NTc4MTIwNjQ2YQ=="
python main.py read report --limit 2
```

## 4. CREATE
```powershell
python main.py create comment --url "https://www.instagram.com/p/XXXXXXXX/" --text "test comment"
python main.py create message --to some_username --text "Hello!"
```

## 5. UPDATE
```powershell
python main.py update caption --url "https://www.instagram.com/p/XXXXXXXX/" --text "New caption"
```

## 6. DELETE (permanent, test on a throwaway post)
```powershell
python main.py delete comment --url "https://www.instagram.com/p/XXXXXXXX/" --text "test comment"
python main.py delete post --url "https://www.instagram.com/p/XXXXXXXX/"
```

## Tips
- Replace `XXXXXXXX` with the real post link (open the post in Instagram and copy the address).
- If Instagram asks for a code or security check, finish it in the Chrome window, then press Enter in PowerShell.
- When the script says "Press Enter to finish", press Enter. Chrome stays open.
- Results are saved as JSON files in the `output` folder.
- macOS / Linux: use `source .venv/bin/activate` and `cp` instead of `copy`.
