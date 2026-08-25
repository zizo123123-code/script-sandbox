"""
tests.py
=======
سويت Unit Tests شامل باستخدام unittest بيجاوب على:
- Task: التسلسل، الحالات، retries
- Storage: CRUD، claim، ترتيب الأولوية
- CircuitBreaker: CLOSED → OPEN → HALF_OPEN → CLOSED
- Worker: تنفيذ، فشل، تحديث الحالة
- TaskQueue (end-to-end): عادي + سيناريو الـ Circuit Breaker
"""

import os
import sys
import time
import tempfile
import unittest

# ضمان استيراد الـ modules من نفس الفولدر
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from task import Task, TaskStatus, Priority, register_task, TASK_REGISTRY
from storage import Storage
from circuit_breaker import CircuitBreaker, CircuitOpenError, CircuitState
from worker import Worker
from queue import TaskQueue


# ============ Task tasks للاختبار ============
@register_task("add")
def _add(a, b):
    return a + b


@register_task("always_fail")
def _always_fail():
    raise RuntimeError("boom")


@register_task("flaky")
def _flaky():
    _flaky.calls += 1
    if _flaky.calls < 3:
        raise ValueError("not yet")
    return "ok"


_flaky.calls = 0


@register_task("slow")
def _slow():
    time.sleep(0.05)
    return "done"


class TestTask(unittest.TestCase):
    def test_to_from_dict_roundtrip(self):
        t = Task(name="add", args=(1, 2), priority=Priority.HIGH, max_retries=5)
        clone = Task.from_dict(t.to_dict())
        self.assertEqual(clone.name, "add")
        self.assertEqual(clone.args, (1, 2))
        self.assertEqual(clone.priority, Priority.HIGH)
        self.assertEqual(clone.max_retries, 5)
        self.assertEqual(clone.status, TaskStatus.PENDING)

    def test_to_from_json_roundtrip(self):
        t = Task(name="add", kwargs={"x": 1})
        clone = Task.from_json(t.to_json())
        self.assertEqual(clone.kwargs, {"x": 1})

    def test_can_retry(self):
        t = Task(name="always_fail", max_retries=2)
        self.assertTrue(t.can_retry())
        t.mark_failed(RuntimeError("x"))
        self.assertTrue(t.can_retry())
        t.mark_failed(RuntimeError("x"))
        self.assertFalse(t.can_retry())
        self.assertEqual(t.status, TaskStatus.FAILED)

    def test_mark_success_serializes_result(self):
        t = Task(name="add")
        t.mark_success({"hello": "world"})
        self.assertIn("hello", t.result)
        self.assertEqual(t.status, TaskStatus.SUCCESS)

    def test_execute_uses_registry(self):
        t = Task(name="add", args=(3, 4))
        self.assertEqual(t.execute(), 7)

    def test_unknown_task_raises(self):
        t = Task(name="does_not_exist")
        with self.assertRaises(KeyError):
            t.execute()


class TestStorage(unittest.TestCase):
    def setUp(self):
        self.storage = Storage(":memory:")

    def tearDown(self):
        self.storage.close()

    def test_enqueue_and_get(self):
        t = Task(name="add", args=(1, 2))
        self.storage.enqueue(t)
        got = self.storage.get(t.id)
        self.assertIsNotNone(got)
        self.assertEqual(got.name, "add")
        self.assertEqual(got.status, TaskStatus.PENDING)

    def test_claim_next_priority_order(self):
        low = Task(name="add", args=(1, 1), priority=Priority.LOW)
        high = Task(name="add", args=(2, 2), priority=Priority.HIGH)
        normal = Task(name="add", args=(3, 3), priority=Priority.NORMAL)

        # ترتيب الإضافة: low → high → normal
        self.storage.enqueue(low)
        time.sleep(0.001)
        self.storage.enqueue(high)
        time.sleep(0.001)
        self.storage.enqueue(normal)

        first = self.storage.claim_next()
        second = self.storage.claim_next()
        third = self.storage.claim_next()

        self.assertEqual(first.priority, Priority.HIGH)
        self.assertEqual(second.priority, Priority.NORMAL)
        self.assertEqual(third.priority, Priority.LOW)

        # claimed → RUNNING
        self.assertEqual(first.status, TaskStatus.RUNNING)

    def test_claim_next_returns_none_when_empty(self):
        self.assertIsNone(self.storage.claim_next())

    def test_update_changes_status(self):
        t = Task(name="add")
        self.storage.enqueue(t)
        t.mark_success(99)
        self.storage.update(t)
        got = self.storage.get(t.id)
        self.assertEqual(got.status, TaskStatus.SUCCESS)
        self.assertIn("99", got.result)

    def test_count_by_status(self):
        for _ in range(3):
            self.storage.enqueue(Task(name="add"))
        self.storage.enqueue(Task(name="always_fail", max_retries=0))
        # علام على واحد كـ FAILED
        failed = self.storage.list_by_status(TaskStatus.PENDING)[-1]
        failed.status = TaskStatus.FAILED
        self.storage.update(failed)

        self.assertEqual(self.storage.count_by_status(TaskStatus.PENDING), 3)
        self.assertEqual(self.storage.count_by_status(TaskStatus.FAILED), 1)


class TestCircuitBreaker(unittest.TestCase):
    def test_starts_closed(self):
        cb = CircuitBreaker(failure_threshold=2, reset_timeout=0.1)
        self.assertEqual(cb.state, CircuitState.CLOSED)

    def test_opens_after_threshold(self):
        cb = CircuitBreaker(failure_threshold=2, reset_timeout=0.5)

        def bad():
            raise RuntimeError("fail")

        for _ in range(2):
            with self.assertRaises(RuntimeError):
                cb.call(bad)
        self.assertEqual(cb.state, CircuitState.OPEN)

        # استدعاء بعد فتح الدائرة لازم يرمي CircuitOpenError
        with self.assertRaises(CircuitOpenError):
            cb.call(bad)

    def test_half_open_then_closed_on_success(self):
        cb = CircuitBreaker(failure_threshold=1, reset_timeout=0.1)

        def bad():
            raise RuntimeError("x")

        def good():
            return "ok"

        with self.assertRaises(RuntimeError):
            cb.call(bad)
        self.assertEqual(cb.state, CircuitState.OPEN)

        time.sleep(0.15)
        result = cb.call(good)
        self.assertEqual(result, "ok")
        self.assertEqual(cb.state, CircuitState.CLOSED)

    def test_half_open_failure_returns_to_open(self):
        cb = CircuitBreaker(failure_threshold=1, reset_timeout=0.05)

        def bad():
            raise RuntimeError("x")

        with self.assertRaises(RuntimeError):
            cb.call(bad)
        self.assertEqual(cb.state, CircuitState.OPEN)

        time.sleep(0.08)
        with self.assertRaises(RuntimeError):
            cb.call(bad)
        self.assertEqual(cb.state, CircuitState.OPEN)

    def test_force_methods(self):
        cb = CircuitBreaker(failure_threshold=1, reset_timeout=10.0)
        cb.force_open()
        self.assertEqual(cb.state, CircuitState.OPEN)
        cb.force_close()
        self.assertEqual(cb.state, CircuitState.CLOSED)


class TestWorker(unittest.TestCase):
    def setUp(self):
        self.storage = Storage(":memory:")
        self.breaker = CircuitBreaker(failure_threshold=2, reset_timeout=0.2)
        self.worker = Worker(
            worker_id="0",
            storage=self.storage,
            breaker=self.breaker,
            poll_interval=0.01,
            sleep_on_empty=0.01,
        )

    def tearDown(self):
        self.worker.stop()
        self.storage.close()

    def test_process_once_success(self):
        t = Task(name="add", args=(5, 7))
        self.storage.enqueue(t)
        self.assertTrue(self.worker.process_once())
        got = self.storage.get(t.id)
        self.assertEqual(got.status, TaskStatus.SUCCESS)
        self.assertIn("12", got.result)

    def test_process_once_failure_retries(self):
        _flaky.calls = 0
        t = Task(name="flaky", max_retries=5)
        self.storage.enqueue(t)

        # أول call: هتفشل → PENDING + retries=1
        self.assertTrue(self.worker.process_once())
        after = self.storage.get(t.id)
        self.assertEqual(after.status, TaskStatus.PENDING)
        self.assertEqual(after.retries, 1)

        # تاني call: هتفشل → retries=2
        self.worker.process_once()
        after = self.storage.get(t.id)
        self.assertEqual(after.retries, 2)

        # تالت call: هتنجح
        self.worker.process_once()
        after = self.storage.get(t.id)
        self.assertEqual(after.status, TaskStatus.SUCCESS)

    def test_process_once_returns_false_when_empty(self):
        self.assertFalse(self.worker.process_once())

    def test_worker_loop_processes_tasks(self):
        for i in range(5):
            self.storage.enqueue(Task(name="add", args=(i, i)))
        self.worker.start()
        # نستنى لحد ما كل حاجة تخلص
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline:
            if self.storage.count_by_status(TaskStatus.PENDING) == 0 and \
               self.storage.count_by_status(TaskStatus.RUNNING) == 0:
                break
            time.sleep(0.02)
        self.worker.stop()
        self.assertEqual(self.storage.count_by_status(TaskStatus.SUCCESS), 5)


class TestTaskQueue(unittest.TestCase):
    def test_end_to_end_success(self):
        q = TaskQueue(db_path=":memory:", num_workers=2,
                      poll_interval=0.01, sleep_on_empty=0.01)
        try:
            q.enqueue(Task(name="add", args=(10, 20)))
            q.enqueue(Task(name="slow"))
            q.start_workers()
            done = q.wait_until_done(timeout=5.0)
            self.assertTrue(done)
            self.assertEqual(q.count(TaskStatus.SUCCESS), 2)
        finally:
            q.shutdown()

    def test_end_to_end_with_failure_and_circuit_breaker(self):
        # الـ breaker هيتفتح بسرعة بسبب المهمة اللي دايمًا بتفشل
        q = TaskQueue(
            db_path=":memory:",
            num_workers=1,
            failure_threshold=2,
            reset_timeout=0.2,
            poll_interval=0.01,
            sleep_on_empty=0.01,
        )
        try:
            bad = Task(name="always_fail", max_retries=1)
            good = Task(name="add", args=(1, 1))
            q.enqueue(bad)
            q.enqueue(good)
            q.start_workers()
            done = q.wait_until_done(timeout=5.0)
            self.assertTrue(done)

            # الـ bad: max_retries=1 → أول فشل بيرجّعها PENDING مع retries=1
            # تاني فشل → FAILED
            bad_after = q.get(bad.id)
            self.assertEqual(bad_after.status, TaskStatus.FAILED)

            # الـ good لازم تنجح في النهاية
            good_after = q.get(good.id)
            self.assertEqual(good_after.status, TaskStatus.SUCCESS)

            # الـ breaker خلّص في حالة CLOSED لأن الـ good_call قفلها
            self.assertEqual(q.breaker.state, CircuitState.CLOSED)
        finally:
            q.shutdown()

    def test_breaker_opens_under_storm_of_failures(self):
        # بنضيف 5 مهام دايمًا بتفشل → الـ breaker لازم يتفتح
        q = TaskQueue(
            db_path=":memory:",
            num_workers=1,
            failure_threshold=3,
            reset_timeout=1.0,
            poll_interval=0.005,
            sleep_on_empty=0.005,
        )
        try:
            for _ in range(5):
                q.enqueue(Task(name="always_fail", max_retries=10))
            q.start_workers()
            # نستنى شوية
            time.sleep(0.4)
            # لازم يبقى في مهمة واحدة على الأقل في OPEN أو الـ breaker OPEN
            self.assertEqual(q.breaker.state, CircuitState.OPEN)
        finally:
            q.shutdown()


if __name__ == "__main__":
    unittest.main(verbosity=2)
