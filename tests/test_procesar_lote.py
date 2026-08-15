from unittest.mock import MagicMock
from botocore.exceptions import ClientError

import procesar_lote as mod


def _mock_s3_client():
    mock_s3 = MagicMock()
    mock_s3.exceptions.ClientError = ClientError
    return mock_s3


class TestYaProcesado:
    def test_true_si_existe_el_marcador(self, monkeypatch):
        mock_s3 = _mock_s3_client()
        monkeypatch.setattr(mod, "s3", mock_s3)

        assert mod.ya_procesado("raw/sales/ingest_date=2010-01/") is True

    def test_false_si_no_existe_el_marcador(self, monkeypatch):
        mock_s3 = _mock_s3_client()
        mock_s3.head_object.side_effect = ClientError(
            {"Error": {"Code": "404", "Message": "Not Found"}}, "HeadObject"
        )
        monkeypatch.setattr(mod, "s3", mock_s3)

        assert mod.ya_procesado("raw/sales/ingest_date=2010-01/") is False