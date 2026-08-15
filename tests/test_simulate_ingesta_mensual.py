from unittest.mock import MagicMock
from botocore.exceptions import ClientError
import pytest

import simulate_ingesta_mensual as mod


def _mock_s3_client():
    mock_s3 = MagicMock()
    mock_s3.exceptions.ClientError = ClientError
    return mock_s3


class TestYaSubido:
    def test_true_si_el_objeto_existe(self, monkeypatch):
        mock_s3 = _mock_s3_client()
        monkeypatch.setattr(mod, "s3", mock_s3)

        assert mod.ya_subido("2010-01") is True
        mock_s3.head_object.assert_called_once_with(
            Bucket=mod.BUCKET, Key="raw/sales/ingest_date=2010-01/ventas.csv"
        )

    def test_false_si_el_objeto_no_existe(self, monkeypatch):
        mock_s3 = _mock_s3_client()
        mock_s3.head_object.side_effect = ClientError(
            {"Error": {"Code": "404", "Message": "Not Found"}}, "HeadObject"
        )
        monkeypatch.setattr(mod, "s3", mock_s3)

        assert mod.ya_subido("2010-01") is False


class TestSubirMes:
    def test_no_sube_si_ya_existe(self, monkeypatch):
        mock_s3 = _mock_s3_client()
        monkeypatch.setattr(mod, "s3", mock_s3)

        mod.subir_mes(MagicMock(), "2010-01")

        mock_s3.upload_file.assert_not_called()

    def test_rechaza_formato_invalido(self, monkeypatch):
        mock_s3 = _mock_s3_client()
        monkeypatch.setattr(mod, "s3", mock_s3)

        with pytest.raises(SystemExit):
            mod.subir_mes(MagicMock(), "enero-2010")