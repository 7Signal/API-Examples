import pytest
import sys
import os
from unittest.mock import patch, MagicMock

# Add the root directory so we can import our modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Import the module to be tested
from examples.network_keys import flow_network_keys

# Secrets come back masked, never as their real value
SAMPLE_KEY = {
    "id": 88,
    "name": "Corporate WPA2",
    "type": "WPA2",
    "usePassphrase": True,
    "passphraseOrPsk": "********",
    "customFields": [],
}

SAMPLE_LIST = {
    "results": [SAMPLE_KEY],
    "pagination": {"perPage": 10, "page": 1, "total": 1, "pages": 1},
}


# Test that the expected functions exist
def test_functions_exist():
    assert hasattr(flow_network_keys, "list_network_keys")
    assert hasattr(flow_network_keys, "list_templates")
    assert hasattr(flow_network_keys, "get_network_key")
    assert hasattr(flow_network_keys, "create_network_key")
    assert hasattr(flow_network_keys, "replace_network_key")
    assert hasattr(flow_network_keys, "delete_network_key")
    assert hasattr(flow_network_keys, "contains_masked_secret")
    assert hasattr(flow_network_keys, "display_network_keys")


# Test that list_network_keys handles a successful API call
@patch("examples.network_keys.flow_network_keys.requests.get")
def test_list_network_keys_success(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = SAMPLE_LIST
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response

    data = flow_network_keys.list_network_keys("fake-token")

    assert data["results"][0]["id"] == 88


# Test that the templates endpoint is read from its own path
@patch("examples.network_keys.flow_network_keys.requests.get")
def test_list_templates_uses_templates_path(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"results": [], "pagination": {}}
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response

    flow_network_keys.list_templates("fake-token")

    assert "/network-keys/sensors/templates" in mock_get.call_args.args[0]


# Test that get_network_key returns None on 404 rather than raising
@patch("examples.network_keys.flow_network_keys.requests.get")
def test_get_network_key_404_returns_none(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_get.return_value = mock_response

    assert flow_network_keys.get_network_key("fake-token", 999) is None


# Test that create_network_key sends the two required fields
@patch("examples.network_keys.flow_network_keys.requests.post")
def test_create_network_key_sends_required_fields(mock_post):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = SAMPLE_KEY
    mock_response.raise_for_status = MagicMock()
    mock_post.return_value = mock_response

    created = flow_network_keys.create_network_key(
        "fake-token", "WPA2", "Corporate WPA2",
        extra_fields={"usePassphrase": True, "passphraseOrPsk": "a-real-passphrase"},
    )

    payload = mock_post.call_args.kwargs["json"]
    assert payload["type"] == "WPA2"
    assert payload["name"] == "Corporate WPA2"
    assert payload["passphraseOrPsk"] == "a-real-passphrase"
    assert created["id"] == 88


# Test that an unsupported key type is refused before any request
@patch("examples.network_keys.flow_network_keys.requests.post")
def test_create_network_key_rejects_invalid_type(mock_post, caplog):
    with caplog.at_level("ERROR"):
        created = flow_network_keys.create_network_key("fake-token", "WEP", "Old and broken")

    assert created is None
    mock_post.assert_not_called()


# Test that the masked-secret detector spots a fetched-and-echoed payload
def test_contains_masked_secret_detects_mask():
    assert flow_network_keys.contains_masked_secret(SAMPLE_KEY) is True


# Test that a payload carrying real values is not flagged
def test_contains_masked_secret_allows_real_values():
    payload = dict(SAMPLE_KEY, passphraseOrPsk="a-real-passphrase")
    assert flow_network_keys.contains_masked_secret(payload) is False


# Test that a payload with no secret fields at all is not flagged
def test_contains_masked_secret_ignores_keys_without_secrets():
    assert flow_network_keys.contains_masked_secret({"type": "WPA3_OWE", "name": "Guest"}) is False


# Test that replacing a key with a masked secret is refused without sending anything.
# PUT is a full replace, so echoing a fetched object back would write the literal
# mask as the new passphrase.
@patch("examples.network_keys.flow_network_keys.requests.put")
def test_replace_network_key_refuses_masked_secret(mock_put, caplog):
    with caplog.at_level("ERROR"):
        updated = flow_network_keys.replace_network_key("fake-token", 88, dict(SAMPLE_KEY))

    assert updated is None
    mock_put.assert_not_called()
    assert "********" in caplog.text


# Test that replacing a key with real values goes through
@patch("builtins.input", return_value="yes")
@patch("examples.network_keys.flow_network_keys.requests.put")
def test_replace_network_key_sends_real_values(mock_put, mock_input):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = SAMPLE_KEY
    mock_response.raise_for_status = MagicMock()
    mock_put.return_value = mock_response

    payload = dict(SAMPLE_KEY, name="Renamed", passphraseOrPsk="a-real-passphrase")
    updated = flow_network_keys.replace_network_key("fake-token", 88, payload)

    assert updated["id"] == 88
    mock_put.assert_called_once()


# Test that declining the confirmation prompt aborts the delete entirely
@patch("examples.network_keys.flow_network_keys.requests.delete")
@patch("builtins.input", return_value="no")
def test_delete_network_key_aborts_without_confirmation(mock_input, mock_delete):
    assert flow_network_keys.delete_network_key("fake-token", 88) is False
    mock_delete.assert_not_called()


# Test that a key still bound to a network or sensor (409) is reported clearly
@patch("examples.network_keys.flow_network_keys.requests.delete")
@patch("builtins.input", return_value="yes")
def test_delete_network_key_409_still_bound(mock_input, mock_delete, caplog):
    mock_response = MagicMock()
    mock_response.status_code = 409
    mock_delete.return_value = mock_response

    with caplog.at_level("INFO"):
        deleted = flow_network_keys.delete_network_key("fake-token", 88)

    assert deleted is False
    assert "still bound" in caplog.text.lower()


# Test that display_network_keys logs the key details without revealing secrets
def test_display_network_keys(caplog):
    with caplog.at_level("INFO"):
        flow_network_keys.display_network_keys(SAMPLE_LIST)

    assert "Corporate WPA2" in caplog.text
    assert "WPA2" in caplog.text


# Test that an empty result set is reported rather than failing
def test_display_network_keys_empty(caplog):
    with caplog.at_level("INFO"):
        flow_network_keys.display_network_keys({"results": [], "pagination": {}})

    assert "No sensor network keys" in caplog.text


# ---------------------------------------------------------------------------
# Error handling and main() flows
# ---------------------------------------------------------------------------

import requests as _requests


def http_error_response(text="Bad Request"):
    r = MagicMock()
    r.status_code = 400
    r.text = text
    r.raise_for_status.side_effect = _requests.exceptions.HTTPError("400")
    return r


# Test that HTTP errors on the read calls return None
@patch("examples.network_keys.flow_network_keys.requests.get")
def test_read_calls_http_error(mock_get, caplog):
    mock_get.return_value = http_error_response()

    with caplog.at_level("ERROR"):
        assert flow_network_keys.list_network_keys("fake-token") is None
        assert flow_network_keys.list_templates("fake-token") is None
        assert flow_network_keys.get_network_key("fake-token", 1) is None

    assert "HTTP error" in caplog.text


# Test that a connection-level failure is caught rather than escaping
@patch("examples.network_keys.flow_network_keys.requests.get",
       side_effect=_requests.exceptions.ConnectionError("boom"))
def test_list_network_keys_connection_error(mock_get, caplog):
    with caplog.at_level("ERROR"):
        assert flow_network_keys.list_network_keys("fake-token") is None

    assert "Unexpected error" in caplog.text


# Test that an HTTP error on create returns None
@patch("examples.network_keys.flow_network_keys.requests.post")
def test_create_network_key_http_error(mock_post):
    mock_post.return_value = http_error_response()
    assert flow_network_keys.create_network_key("fake-token", "WPA2", "n") is None


# Test that an HTTP error on replace returns None
@patch("builtins.input", return_value="yes")
@patch("examples.network_keys.flow_network_keys.requests.put")
def test_replace_network_key_http_error(mock_put, mock_input):
    mock_put.return_value = http_error_response()
    assert flow_network_keys.replace_network_key("fake-token", 1, {"type": "WPA2"}) is None


# Test that declining the replace confirmation sends nothing
@patch("builtins.input", return_value="no")
@patch("examples.network_keys.flow_network_keys.requests.put")
def test_replace_network_key_declined(mock_put, mock_input):
    assert flow_network_keys.replace_network_key("fake-token", 1, {"type": "WPA2"}) is None
    mock_put.assert_not_called()


# Test that deleting an unknown key is reported rather than raised
@patch("examples.network_keys.flow_network_keys.requests.delete")
@patch("builtins.input", return_value="yes")
def test_delete_network_key_404(mock_input, mock_delete, caplog):
    r = MagicMock()
    r.status_code = 404
    mock_delete.return_value = r

    with caplog.at_level("INFO"):
        assert flow_network_keys.delete_network_key("fake-token", 1) is False

    assert "No sensor network key found" in caplog.text


# Test that a successful delete returns True
@patch("examples.network_keys.flow_network_keys.requests.delete")
@patch("builtins.input", return_value="yes")
def test_delete_network_key_success(mock_input, mock_delete):
    r = MagicMock()
    r.status_code = 204
    r.raise_for_status = MagicMock()
    mock_delete.return_value = r

    assert flow_network_keys.delete_network_key("fake-token", 1) is True


# Test that an HTTP error on delete returns False
@patch("examples.network_keys.flow_network_keys.requests.delete")
@patch("builtins.input", return_value="yes")
def test_delete_network_key_http_error(mock_input, mock_delete):
    mock_delete.return_value = http_error_response()
    assert flow_network_keys.delete_network_key("fake-token", 1) is False


# Test that the EAP method is shown when present
def test_display_network_keys_shows_eap(caplog):
    eap = {"results": [{"id": 1, "name": "Corp EAP", "type": "WPA_EAP", "eapMethod": "EAP_PEAP"}]}

    with caplog.at_level("INFO"):
        flow_network_keys.display_network_keys(eap)

    assert "EAP_PEAP" in caplog.text


def run_main(input_values, **extra):
    applied = [
        patch("examples.network_keys.flow_network_keys.get_token", return_value=("tok", 0)),
        patch("examples.network_keys.flow_network_keys.list_network_keys", return_value=SAMPLE_LIST),
        patch("builtins.input", side_effect=input_values),
    ]
    for target, value in extra.items():
        applied.append(patch(f"examples.network_keys.flow_network_keys.{target}", return_value=value))
    for p in applied:
        p.start()
    try:
        flow_network_keys.main()
    finally:
        for p in reversed(applied):
            p.stop()


# Test main's exit branch
def test_main_exit_branch(caplog):
    with caplog.at_level("INFO"):
        run_main(["6"])

    assert "Nothing to do" in caplog.text


# Test main's fetch branch, which also warns about the masked secret
def test_main_fetch_branch_warns_about_mask(caplog):
    with caplog.at_level("INFO"):
        run_main(["1", "88"], get_network_key=SAMPLE_KEY)

    assert "re-supply the real secret" in caplog.text.lower()


# Test that an empty key id exits
def test_main_fetch_empty_exits():
    with pytest.raises(SystemExit):
        run_main(["1", " "])


# Test main's templates branch
def test_main_templates_branch(caplog):
    with caplog.at_level("INFO"):
        run_main(["2"], list_templates={"results": [], "pagination": {}})

    assert "No sensor network keys" in caplog.text


# Test main's create branch
def test_main_create_branch():
    run_main(["3", "Corp WPA2", "a-real-passphrase", "yes"], create_network_key=SAMPLE_KEY)


# Test that an empty name exits
def test_main_create_empty_name_exits():
    with pytest.raises(SystemExit):
        run_main(["3", " "])


# Test that an empty passphrase exits
def test_main_create_empty_passphrase_exits():
    with pytest.raises(SystemExit):
        run_main(["3", "n", " "])


# Test that typing the mask as the passphrase is refused
def test_main_create_mask_as_passphrase_exits():
    with pytest.raises(SystemExit):
        run_main(["3", "n", "********"])


# Test that declining the create confirmation sends nothing
def test_main_create_declined():
    with patch("examples.network_keys.flow_network_keys.create_network_key") as mock_create:
        run_main(["3", "n", "real", "no"])
        mock_create.assert_not_called()


# Test main's delete branch
def test_main_delete_branch():
    run_main(["5", "88"], delete_network_key=True)


# Test that an empty id on the delete branch exits
def test_main_delete_empty_exits():
    with pytest.raises(SystemExit):
        run_main(["5", " "])


# Test main's rename branch, which must re-supply the real passphrase because a
# full replace would otherwise write the mask over it
def test_main_rename_branch():
    run_main(
        ["4", "88", "Renamed", "a-real-passphrase"],
        get_network_key=SAMPLE_KEY,
        replace_network_key=SAMPLE_KEY,
    )


# Test that the rename branch refuses a non-WPA2 key rather than dropping its fields
def test_main_rename_refuses_other_key_types(caplog):
    with caplog.at_level("ERROR"):
        run_main(["4", "88"], get_network_key={"id": 88, "type": "WPA_EAP", "name": "EAP"})

    assert "only renames WPA2" in caplog.text


# Test that the rename branch refuses the mask as a passphrase
def test_main_rename_refuses_mask():
    with pytest.raises(SystemExit):
        run_main(["4", "88", "Renamed", "********"], get_network_key=SAMPLE_KEY)
