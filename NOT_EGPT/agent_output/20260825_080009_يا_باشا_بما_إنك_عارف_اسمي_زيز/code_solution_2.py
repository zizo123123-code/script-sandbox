import hashlib

def hash_supervisor_code(code: str, salt: str = "zizo_secret") -> str:
    # بنضيف الـ salt للكود قبل التشفير عشان نقلل خطر الهجمات
    salted = salt + code
    return hashlib.sha256(salted.encode()).hexdigest()

print(hash_supervisor_code("889900"))