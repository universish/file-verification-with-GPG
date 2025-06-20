import os
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox
import re
import time

# Keyserver listesi
KEYSERVERS = [
    'keyserver.ubuntu.com',
    'keys.openpgp.org',
    'pgp.mit.edu',
    'keyserver.pgp.com'
]

def get_primary_key_id(subkey_id):
    """Alt anahtardan birincil anahtar ID'sini bul"""
    result = subprocess.run(
        ['gpg', '--list-keys', '--with-colons', subkey_id],
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='ignore'
    )
    
    # Çıktıyı analiz et
    for line in result.stdout.splitlines():
        if line.startswith('pub:'):
            parts = line.split(':')
            if len(parts) > 4:
                return parts[4]
    return None

def get_key_fingerprint(key_id):
    """Anahtarın parmak izini al"""
    result = subprocess.run(
        ['gpg', '--fingerprint', '--with-colons', key_id],
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='ignore'
    )
    
    # Çıktıyı analiz et
    for line in result.stdout.splitlines():
        if line.startswith('fpr:'):
            parts = line.split(':')
            if len(parts) > 9:
                return parts[9]
    return None

def get_key_details(key_id):
    """Anahtar detaylarını al (revoke, expire, trust)"""
    result = subprocess.run(
        ['gpg', '--list-keys', '--with-colons', key_id],
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='ignore'
    )
    
    details = {
        'fingerprint': None,
        'revoked': False,
        'expired': False,
        'expiry': None,
        'trust': 'unknown',
        'key_id': key_id,
        'type': 'primary'
    }
    
    # Çıktıyı analiz et
    for line in result.stdout.splitlines():
        if line.startswith('pub:'):
            parts = line.split(':')
            if len(parts) > 12:
                details['fingerprint'] = parts[12] if parts[12] else parts[4]
            if len(parts) > 1 and parts[1] == 'r':
                details['revoked'] = True
            if len(parts) > 6 and parts[6]:
                expiry = int(parts[6]) if parts[6] else 0
                if expiry > 0 and expiry < int(time.time()):
                    details['expired'] = True
                details['expiry'] = expiry
            if len(parts) > 8:
                details['trust'] = parts[8]
        elif line.startswith('sub:'):
            parts = line.split(':')
            if len(parts) > 4 and parts[4] == key_id:
                details['type'] = 'subkey'
                if len(parts) > 12:
                    details['fingerprint'] = parts[12] if parts[12] else parts[4]
                if len(parts) > 1 and parts[1] == 'r':
                    details['revoked'] = True
                if len(parts) > 6 and parts[6]:
                    expiry = int(parts[6]) if parts[6] else 0
                    if expiry > 0 and expiry < int(time.time()):
                        details['expired'] = True
                    details['expiry'] = expiry
    
    return details

def download_key(key_id):
    """Birden fazla keyserver kullanarak anahtar indir"""
    messages = []
    success = False
    
    for server in KEYSERVERS:
        try:
            result = subprocess.run(
                ['gpg', '--keyserver', server, '--recv-keys', key_id],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',
                timeout=10
            )
            
            if "imported" in result.stderr or "unchanged" in result.stderr:
                messages.append(f"✅ Anahtar sunucusundan ({server}) anahtar alındı")
                success = True
                break
            elif "not found" in result.stderr:
                messages.append(f"⚠️ Anahtar sunucusunda ({server}) anahtar bulunamadı")
            else:
                messages.append(f"ℹ️ Anahtar sunucusu ({server}) yanıtı: {result.stderr[:100]}")
        except subprocess.TimeoutExpired:
            messages.append(f"⏱️ Anahtar sunucusu ({server}) zaman aşımı")
        except Exception as e:
            messages.append(f"❌ Anahtar sunucusu hatası ({server}): {str(e)}")
    
    if not success:
        messages.append("❌ Tüm anahtar sunucularından anahtar alınamadı")
    
    return success, messages

def verify_key_chain(key_id):
    """Anahtar zinciri ve güven kontrolü"""
    result = subprocess.run(
        ['gpg', '--check-sigs', key_id],
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='ignore'
    )
    
    # İmza sayısını say
    sig_count = result.stdout.count('[  tam  ]') + result.stdout.count('[  geçerli  ]')
    
    return sig_count

def verify_file():
    # Dosya seçme penceresi
    root = tk.Tk()
    root.withdraw()
    
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
    
    # Anahtar doğrulama mesajları
    key_validation_messages = []
    summary_messages = []
    key_id = None
    primary_key_id = None
    security_status = "Şüpheli"
    security_reason = "İmza doğrulama tamamlanamadı"
    key_fingerprint = None
    primary_fingerprint = None
    
    # GPG doğrulama komutu
    result = subprocess.run(
        ['gpg', '--verify', asc_file, exe_file],
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='ignore'
    )
    
    key_validation_messages.append("=== GPG DOĞRULAMA ÇIKTISI ===")
    key_validation_messages.append(result.stderr[:500] + "..." if len(result.stderr) > 500 else result.stderr)
    
    # Anahtar bulunamadı hatası durumunda
    if "No public key" in result.stderr or "gpg: Can't check signature: No public key" in result.stderr:
        match = re.search(r"key ID (\w+)", result.stderr)
        if match:
            key_id = match.group(1)
            summary_messages.append(f"⚠️ PUBLIC ANAHTAR EKSİK: Key ID: {key_id}")
            
            # Anahtarı keyserver'dan al
            key_validation_messages.append("\n=== ANAHTAR İNDİRME ADIMLARI ===")
            success, dl_messages = download_key(key_id)
            key_validation_messages.extend(dl_messages)
            
            if success:
                summary_messages.append("✅ Anahtar sunucularından public anahtar alındı")
                # Tekrar doğrulama yap
                result = subprocess.run(
                    ['gpg', '--verify', asc_file, exe_file],
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='ignore'
                )
                key_validation_messages.append("\n=== TEKRAR DOĞRULAMA ÇIKTISI ===")
                key_validation_messages.append(result.stderr[:500] + "..." if len(result.stderr) > 500 else result.stderr)
    
    # İmza doğrulama sonrası anahtar ID'sini al
    if not key_id:
        match = re.search(r"using (\w+) key", result.stderr)
        if match:
            key_id = match.group(1)
            summary_messages.append(f"ℹ️ KULLANILAN ANAHTAR ID: {key_id}")
    
    # Anahtar doğrulama işlemleri
    if key_id:
        key_validation_messages.append("\n=== ANAHTAR DOĞRULAMA ADIMLARI ===")
        
        # Anahtar detaylarını al
        key_details = get_key_details(key_id)
        summary_messages.append(f"ℹ️ Anahtar tipi: {key_details['type']}")
        
        # Anahtar türüne göre işlemler
        if key_details['type'] == 'subkey':
            summary_messages.append(f"ℹ️ İmza alt anahtar ile oluşturulmuş (Key ID: {key_id})")
            
            # Birincil anahtarı bul
            primary_key_id = get_primary_key_id(key_id)
            if primary_key_id:
                summary_messages.append(f"ℹ️ BİRİNCİL ANAHTAR ID: {primary_key_id}")
                
                # Birincil anahtarı indir
                summary_messages.append(f"ℹ️ Birincil anahtar indiriliyor...")
                success, dl_messages = download_key(primary_key_id)
                key_validation_messages.extend(dl_messages)
                
                if success:
                    summary_messages.append("✅ Anahtar sunucularından birincil anahtar alındı")
                    # Birincil anahtar detayları
                    primary_details = get_key_details(primary_key_id)
                    primary_fingerprint = get_key_fingerprint(primary_key_id)
                    
                    # Kök anahtar parmak izi kontrolü
                    if primary_fingerprint and primary_details['fingerprint']:
                        if primary_fingerprint == primary_details['fingerprint']:
                            summary_messages.append("✅ Kök anahtar parmak izi doğrulandı, eşleşiyor")
                        else:
                            summary_messages.append("❌ Kök anahtar parmak izi doğrulanamadı, eşleşmiyor !")
                            summary_messages.append("🚨 Tehlikeli: Kök Anahtar Değişmiş!")
                            security_status = "Tehlikeli"
                            security_reason = "Kök anahtar değişmiş"
                    else:
                        summary_messages.append("⚠️ Kök anahtar parmak izi alınamadı")
                else:
                    summary_messages.append("❌ Birincil anahtar indirilemedi")
            else:
                summary_messages.append("❌ Birincil anahtar bulunamadı!")
        
        # Public anahtar parmak izi kontrolü
        key_fingerprint = get_key_fingerprint(key_id)
        if key_fingerprint and key_details['fingerprint']:
            if key_fingerprint == key_details['fingerprint']:
                summary_messages.append("✅ Public Anahtar parmak izi kontrol edildi, eşleşiyor.")
            else:
                summary_messages.append("❌ Public Anahtar parmak izi kontrol edildi, eşleşmiyor.")
                summary_messages.append("🚨 Tehlikeli: Sahte anahtar")
                security_status = "Tehlikeli"
                security_reason = "Sahte anahtar"
        else:
            summary_messages.append("⚠️ Public anahtar parmak izi alınamadı")
        
        # Alt anahtar kontrolü
        if key_details['type'] == 'subkey':
            if key_fingerprint and key_details['fingerprint']:
                if key_fingerprint == key_details['fingerprint']:
                    summary_messages.append("✅ Alt anahtar eşleşti")
                else:
                    summary_messages.append("❌ Alt anahtar eşleşmedi")
                    security_status = "Tehlikeli"
                    security_reason = "Alt anahtar eşleşmedi"
            
            if key_id:
                summary_messages.append(f"ℹ️ Alt anahtar şu: {key_id}")
            if primary_key_id:
                summary_messages.append(f"ℹ️ Birincil anahtar şu: {primary_key_id}")
        
        # Revoke durumu kontrolü
        if key_details.get('revoked'):
            summary_messages.append("🚨 Anahtar geçerlilik durumu: Revoke kontrolü: iptal edilmiş")
            summary_messages.append("🚨 Tehlikeli: İptal Edilmiş anahtar")
            security_status = "Tehlikeli"
            security_reason = "İptal edilmiş anahtar"
        else:
            summary_messages.append("ℹ️ Anahtar geçerlilik durumu: Revoke kontrolü: iptal edilmemiş")
        
        # Süre sonu kontrolü
        if key_details.get('expired'):
            summary_messages.append("⚠️ İmza süresi kontrolü yapıldı. İmza süresi dolmuş")
            summary_messages.append("⚠️ Şüpheli: Süresi dolmuş.")
            if security_status != "Tehlikeli":
                security_status = "Şüpheli"
                security_reason = "Süresi dolmuş"
        else:
            summary_messages.append("ℹ️ İmza süresi kontrolü yapıldı. İmza süresi dolmamış")
        
        # İmza zinciri kontrolü
        target_key = primary_key_id or key_id
        if target_key:
            sig_count = verify_key_chain(target_key)
            if sig_count > 0:
                summary_messages.append(f"✅ İmza zinciri kontrolü yapıldı. Yeterli güvenilir imza var ({sig_count} imza)")
            else:
                summary_messages.append("⚠️ İmza zinciri kontrolü yapıldı. Yeterli güvenilir imza yok")
                summary_messages.append("⚠️ Şüpheli: Yetersiz İmza")
                if security_status != "Tehlikeli":
                    security_status = "Şüpheli"
                    security_reason = "Yetersiz imza"
        else:
            summary_messages.append("⚠️ İmza zinciri kontrolü yapılamadı")
    
    # Sonuç analizi
    is_valid = "Good signature" in result.stderr or "gpg: İyi imza" in result.stderr
    is_invalid = "BAD signature" in result.stderr or "gpg: Geçersiz imza" in result.stderr
    
    # Sonuç mesajı oluştur
    message = f"📄 DOSYA: {os.path.basename(exe_file)}\n"
    message += f"🔏 İMZA: {os.path.basename(asc_file)}\n\n"
    
    if is_valid:
        message += "✅ DOSYA BÜTÜNLÜĞÜ ONAYLANDI\n"
        message += "✔ İmza geçerli ve güvenilir\n"
        message += "✔ Dosya orijinal haliyle değiştirilmemiş\n\n"
        security_status = "Güvenli"
        security_reason = "Tüm kontroller başarılı"
        
        # İmza zinciri kontrolü mesajını ekle
        if any("Yeterli güvenilir imza var" in msg for msg in summary_messages):
            message += "✅ İmza zinciri kontrolü yapıldı. Yeterli güvenilir imza var\n"
    elif is_invalid:
        message += "❌ CİDDİ GÜVENLİK UYARISI!\n"
        message += "✖ Dosya değiştirilmiş veya bozulmuş\n"
        message += "✖ Orijinal dosyayla uyuşmuyor\n\n"
        security_status = "Tehlikeli"
        security_reason = "Geçersiz imza"
    else:
        message += "⚠️ DİKKAT GEREKTİREN DURUM!\n"
        message += "• İmza doğrulama tamamlanamadı\n"
        message += "• Ek kontroller gerekli\n\n"
    
    # Özet mesajları ekle
    if summary_messages:
        message += "\n=== ÖZET RAPOR ===\n"
        message += "\n".join(summary_messages) + "\n\n"
    
    # Güvenlik durumu mesajını ekle
    if security_status == "Güvenli":
        message += f"🛡️ GÜVENLİK DURUMU: {security_status} - {security_reason}\n"
    elif security_status == "Tehlikeli":
        message += f"🛑 GÜVENLİK DURUMU: {security_status} - {security_reason}\n"
        message += "HEMEN SİLİN!\n"
    else:  # Şüpheli durum
        message += f"⚠️ GÜVENLİK DURUMU: {security_status} - {security_reason}\n"
        message += "Kullanıp kullanmamak size kalmış, risk ve sorumluluk size ait\n"
    
    # Detaylı doğrulama raporu ekle
    message += "\n\n🔐 DETAYLI DOĞRULAMA RAPORU:\n"
    message += "\n".join(key_validation_messages)

    # Sonuç penceresi
    messagebox.showinfo("Dosya Doğrulama Sonucu", message)

if __name__ == "__main__":
    verify_file()
