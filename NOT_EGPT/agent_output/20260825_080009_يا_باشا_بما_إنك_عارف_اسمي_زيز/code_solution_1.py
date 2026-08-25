import hashlib

def hash_supervisor_code(code: str, salt: str = "zizo_secret") -> str:
    # دمج الكود مع الملح ثم التشفير بـ SHA-256
    salted = salt + code
    return hashlib.sha256(salted.encode()).hexdigest()

print(hash_supervisor_code("889900"))