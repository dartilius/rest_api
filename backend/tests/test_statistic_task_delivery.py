from ch_statistic.tasks import create_statistic


def test_statistic_task_acknowledges_only_after_processing() -> None:
    assert create_statistic.acks_late is True
    assert create_statistic.reject_on_worker_lost is True
    assert create_statistic.max_retries == 5
