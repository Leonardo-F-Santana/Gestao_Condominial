import ecdsa
import base64

def generate():
    sk = ecdsa.SigningKey.generate(curve=ecdsa.NIST256p)
    vk = sk.get_verifying_key()
    
    priv_bytes = sk.to_string()
    pub_bytes = b'\x04' + vk.to_string()
    
    priv_b64 = base64.urlsafe_b64encode(priv_bytes).decode('utf-8').replace('=', '')
    pub_b64 = base64.urlsafe_b64encode(pub_bytes).decode('utf-8').replace('=', '')
    
    with open('vapid.txt', 'w') as f:
        f.write(f"VAPID_PRIVATE_KEY='{priv_b64}'\n")
        f.write(f"VAPID_PUBLIC_KEY='{pub_b64}'\n")
        f.write(f"VAPID_ADMIN_EMAIL='mailto:admin@gestaocondominial.com'\n")

if __name__ == '__main__':
    generate()
