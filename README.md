# 🌙 Nightreign Relic Editor

A powerful and user-friendly save editor for **Nightreign**, focused on full control over **Relics**, save data, and character progression for PC/PS4.



---

## ✨ Features

### 🔧 Relic Management
- Edit existing Relics  
- Replace Relics  
- Modify Relic effect IDs and values  
- Delete Relics  
- Export & import Relics via **Excel**  

### 💎 Save Editing
- Edit **Murks** and **Sigs**
- Import full save files or individual characters
- Improved **illegal relic detection**
- Multi-language support

---
## 🖥️ How to Use

### PC (Steam / Seamless Co-op)

1. Locate your save file:
   ```text
   C:\Users\%YourUsername%\AppData\Roaming\Nightreign\<User-ID>\
   NR0000.sl2
    ```
2.  If using Seamless Co-op, ensure the save file name is NR0000.sl2.
3.  Open the save file using the editor.
4.  Edit the data as desired.
5.  Save the changes and replace the original file.

### PS4/PS5 (PS4 Version)
1.  Decrypt your save file
      (see the YouTube decryption guide).
2.  Open memory.dat with the editor.

3.  Edit and save your changes.

4.  Re-encrypt the modified data.

5.  Transfer the save back to your console.



---
## 📥 Download

You can download the latest builds from the releases page:

🔗 https://github.com/alfizari/Elden-Ring-Nightreign-Save-Editor/releases


---

## 🧩 Requirements

### Python
- **Python 3.12 or newer**

### Dependencies
The following Python packages are required:

```text
cryptography >= 46.0.3
lxml >= 6.0.2
openpyxl >= 3.1.5
orjson >= 3.11.5
pandas >= 2.3.3
```
```bash
pip install cryptography lxml openpyxl orjson pandas
```

---

## ⚠️ Disclaimer
- Always **backup your save files** before editing.
- Improper edits may cause save corruption.
- Using modified saves online may result in bans.
- Use this tool **at your own risk**.

---

## 🤝 Contributors

| Name | Contribution |
|------|--------------|
|    [ip1259](https://github.com/ip1259)  | Maintainer/Illegal relic detection/Multi Languge Support             |
|   [Vanesro](https://github.com/Vanesro)   | Illegal Relic Detection Improvments/Bug Fixes             |
|   [thewerthon](https://github.com/thewerthon)   |Relics and Effect list/QoL improvement              |
|   [msurkein](https://github.com/msurkein)   |Export Relic/QoL improvement              |
|   [nacitar](https://github.com/nacitar)   |Relic List             |

Thanks to everyone who contributed.



---

## 🤝 How to Contribute
Contributions are welcome and appreciated!

You can help by:
- Adding Relic IDs
- Adding Effect IDs
- Improving illegal relic detection
- Adding translations
- Improving documentation

Feel free to submit a pull request or share data via the project page.

---

## 📌 Notes
This project is actively developed.  
Feedback, bug reports, and suggestions are welcome.
