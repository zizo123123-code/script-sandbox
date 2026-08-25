import random

# توليد بيانات مبيعات عشوائية لـ 100 عملية
sales = [random.randint(50, 5000) for _ in range(100)]

total = sum(sales)  # إجمالي المبيعات
max_sale = max(sales)  # أعلى عملية بيع

print(f"إجمالي المبيعات: {total}")
print(f"أعلى عملية بيع: {max_sale}")