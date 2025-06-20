import os
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox
import re

def verify_file():
    # Dosya seçme penceresi
    root = tk.Tk()
    root.withdraw()  # Ana pencereyi gizle
    
    # .exe dosyasını seçtir
    exe_file = filedialog.askopenfilename(
        title="Doğrulanacak .exe dosyasını seçin",
        filetypes=[("Executable files", "*.exe"), ("All files", "*.*")]
    )
    if not exe_file:
        return
    
    # .asc dosyasını otomatik bul
    asc_file = os.path.splitext(exe_file)[0] + ".asc"
    if not os.path.exists(asc_file):
        asc_file = filedialog.askopenfilename(
            title="İmza (.asc) dosyasını seçin",
            filetypes=[("Signature files", "*.asc *.sig"), ("All files", "*.*")],
            initialdir=os.path.dirname(exe_file)
        )
        if not asc_file:
            return
    
    # GPG doğrulama komutu
    result = subprocess.run(
        ['gpg', '--verify', asc_file, exe_file],
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='ignore'
    )
    
    # Anahtar bulunamadı hatası durumunda
    key_id = None
    if "No public key" in result.stderr:
        match = re.search(r"key ID (\w+)", result.stderr)
        if match:
            key_id = match.group(1)
            # Anahtarı keyserver'dan al
            subprocess.run(['gpg', '--keyserver', 'keyserver.ubuntu.com', '--recv-keys', key_id])
            # Tekrar doğrulama yap
            result = subprocess.run(
                ['gpg', '--verify', asc_file, exe_file],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore'
            )
    
    # Sonuç analizi
    is_valid = "Good signature" in result.stderr or "gpg: İyi imza" in result.stderr
    is_invalid = "BAD signature" in result.stderr or "gpg: Geçersiz imza" in result.stderr
    
    # Sonuç mesajı oluştur
    message = f"DOSYA: {os.path.basename(exe_file)}\n"
    message += f"İMZA: {os.path.basename(asc_file)}\n\n"
    
    if is_valid:
        message += "✅ DOSYA BÜTÜNLÜĞÜ ONAYLANDI\n"
        message += "✔ İmza geçerli ve güvenilir\n"
        message += "✔ Dosya orijinal haliyle değiştirilmemiş\n\n"
        message += "GÜVENLİK DURUMU: Güvenli - Kullanabilirsiniz"
    elif is_invalid:
        message += "❌ CİDDİ GÜVENLİK UYARISI!\n"
        message += "✖ Dosya değiştirilmiş veya bozulmuş\n"
        message += "✖ Orijinal dosyayla uyuşmuyor\n\n"
        message += "GÜVENLİK DURUMU: Tehlikeli - Hemen silin!"
    else:
        message += "⚠️ DİKKAT GEREKTİREN DURUM!\n"
        message += "• İmza doğrulama tamamlanamadı\n"
        message += "• Ek kontroller gerekli\n\n"
        message += f"Teknik detay:\n{result.stderr[-500:]}\n\n"
        message += "GÜVENLİK DURUMU: Şüpheli - Kullanmayın"

    # Sonuç penceresi
    messagebox.showinfo("Dosya Doğrulama Sonucu", message)

if __name__ == "__main__":
    verify_file()
