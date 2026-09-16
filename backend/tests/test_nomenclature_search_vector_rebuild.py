from unittest.mock import patch

from nomenclatures import signals


def test_rebuild_search_vectors_uses_requested_batch_size():
    with patch("nomenclatures.signals.call_command") as call_command:
        signals._rebuild_search_vectors()

    call_command.assert_called_once_with("rebuild_search_vectors", batch_size=5000)
