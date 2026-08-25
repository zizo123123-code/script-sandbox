from datetime import datetime


class BankAccount:
    """كلاس يمثل حساب بنكي مع سجل حركات (transactions)."""

    def __init__(self, owner: str = "Anonymous", initial_balance: float = 0):
        # اسم صاحب الحساب، الرصيد المبدئي، وسجل الحركات
        self.owner = owner
        self.balance = float(initial_balance)
        self.transactions = []

        # تسجيل الرصيد المبدئي كأول حركة لو كان أكبر من صفر
        if initial_balance > 0:
            self._record("INIT", initial_balance)

    def _record(self, kind: str, amount: float, counterparty: str = None):
        """دالة داخلية بتسجل أي حركة في قائمة transactions."""
        entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "type": kind,
            "amount": float(amount),
            "balance_after": self.balance,
            "counterparty": counterparty,
        }
        self.transactions.append(entry)
        return entry

    def deposit(self, amount: float):
        """دالة الإيداع: بتزود الرصيد بمبلغ موجب وبتسجل الحركة."""
        if amount <= 0:
            raise ValueError("المبلغ لازم يكون أكبر من صفر")
        self.balance += amount
        return self._record("DEPOSIT", amount)

    def withdraw(self, amount: float):
        """دالة السحب: بتخصم المبلغ من الرصيد لو فيه رصيد كافي وبتسجل الحركة."""
        if amount <= 0:
            raise ValueError("المبلغ لازم يكون أكبر من صفر")
        if amount > self.balance:
            raise ValueError("الرصيد مش كافي")
        self.balance -= amount
        return self._record("WITHDRAW", amount)

    def transfer(self, target_account, amount: float):
        """دالة التحويل: بتخصم المبلغ من الحساب الحالي وبتوديه للحساب التاني."""
        if not isinstance(target_account, BankAccount):
            raise TypeError("target_account لازم يكون instance من BankAccount")
        if amount <= 0:
            raise ValueError("المبلغ لازم يكون أكبر من صفر")
        if amount > self.balance:
            raise ValueError("الرصيد مش كافي للتحويل")

        # تنفيذ التحويل من طرفين
        self.balance -= amount
        target_account.balance += amount

        # تسجيل الحركة في الحساب المرسل والمستلم
        sender_entry = self._record("TRANSFER_OUT", amount, counterparty=target_account.owner)
        receiver_entry = target_account._record(
            "TRANSFER_IN", amount, counterparty=self.owner
        )
        return {"sender": sender_entry, "receiver": receiver_entry}

    def get_balance(self) -> float:
        """ترجع الرصيد الحالي."""
        return self.balance

    def get_transactions(self):
        """ترجع نسخة من سجل الحركات."""
        return list(self.transactions)


# مثال سريع للاستخدام
if __name__ == "__main__":
    ahmed = BankAccount(owner="Ahmed", initial_balance=1000)
    sara = BankAccount(owner="Sara", initial_balance=500)

    print("رصيد Ahmed المبدئي:", ahmed.get_balance())
    print("رصيد Sara المبدئي:", sara.get_balance())

    ahmed.deposit(300)
    ahmed.withdraw(150)
    ahmed.transfer(sara, 400)

    print("\nرصيد Ahmed بعد العمليات:", ahmed.get_balance())
    print("رصيد Sara بعد العمليات:", sara.get_balance())

    print("\nسجل حركات Ahmed:")
    for t in ahmed.get_transactions():
        print(t)

    print("\nسجل حركات Sara:")
    for t in sara.get_transactions():
        print(t)
