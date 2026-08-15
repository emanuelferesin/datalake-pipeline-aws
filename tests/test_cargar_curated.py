import json
from unittest.mock import MagicMock

import cargar_curated as mod


class TestObtenerCredencial:
    def test_parsea_el_json_del_secreto(self, monkeypatch):
        mock_secrets = MagicMock()
        mock_secrets.get_secret_value.return_value = {
            "SecretString": json.dumps({
                "username": "app", "password": "x",
                "host": "localhost", "port": 5432, "dbname": "appdb",
            })
        }
        monkeypatch.setattr(mod, "secrets", mock_secrets)

        cred = mod.obtener_credencial()

        assert cred["username"] == "app"
        mock_secrets.get_secret_value.assert_called_once_with(SecretId="app/db")