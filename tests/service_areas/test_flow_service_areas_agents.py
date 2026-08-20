import pytest
import sys
import os
from unittest.mock import patch, MagicMock

# Add the root directory so we can import our modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Import the module to be tested
from examples.service_areas import flow_service_areas_agents as sa

AREA_ID = "6e2a9c41-7b35-4d88-a1f0-92c4e7b5d306"
OTHER_ID = "b81f3d07-2c69-4a15-8e73-5f0a9c62d418"

SAMPLE_AREA = {
    "id": AREA_ID,
    "name": "Cleveland HQ - Floor 3",
    "address": "1000 Example Ave, Cleveland, OH 44113",
    "locationId": "4d1e8b7c-9a35-4c72-b6f0-2e5a9d3c8f41",
    "createdAt": "2026-03-11T15:04:22Z",
    "updatedAt": "2026-07-28T09:41:07Z",
}

SAMPLE_LIST = {
    "results": [SAMPLE_AREA],
    "pagination": {"perPage": 10, "page": 1, "total": 1, "pages": 1},
}


def mock_json_response(payload, status_code=200):
    mock_response = MagicMock()
    mock_response.status_code = status_code
    mock_response.json.return_value = payload
    mock_response.raise_for_status = MagicMock()
    return mock_response


# Test that the expected functions exist
def test_functions_exist():
    assert hasattr(sa, "list_service_areas")
    assert hasattr(sa, "get_service_area")
    assert hasattr(sa, "create_service_areas")
    assert hasattr(sa, "update_service_areas")
    assert hasattr(sa, "update_service_area")
    assert hasattr(sa, "delete_service_areas")
    assert hasattr(sa, "delete_service_area")
    assert hasattr(sa, "display_service_areas")


# Test that list_service_areas handles a successful API call
@patch("examples.service_areas.flow_service_areas_agents.requests.get")
def test_list_service_areas_success(mock_get):
    mock_get.return_value = mock_json_response(SAMPLE_LIST)

    data = sa.list_service_areas("fake-token")

    assert data["results"][0]["id"] == AREA_ID


# Test that the id filter is sent as one comma-separated string
@patch("examples.service_areas.flow_service_areas_agents.requests.get")
def test_list_service_areas_joins_ids_with_commas(mock_get):
    mock_get.return_value = mock_json_response(SAMPLE_LIST)

    sa.list_service_areas("fake-token", service_area_ids=[AREA_ID, OTHER_ID])

    params = dict(mock_get.call_args.kwargs["params"])
    assert params["serviceAreaIds"] == f"{AREA_ID},{OTHER_ID}"


# Test that multiple sort keys are sent as a repeated parameter, not collapsed
@patch("examples.service_areas.flow_service_areas_agents.requests.get")
def test_list_service_areas_repeats_sort_parameter(mock_get):
    mock_get.return_value = mock_json_response(SAMPLE_LIST)

    sa.list_service_areas("fake-token", sort=["name,asc", "createdAt,desc"])

    params = mock_get.call_args.kwargs["params"]
    # A dict would lose one of the two values, so params must be a sequence of pairs
    assert ("sort", "name,asc") in params
    assert ("sort", "createdAt,desc") in params


# Test that sorting by score without a window is refused before any request
@patch("examples.service_areas.flow_service_areas_agents.requests.get")
def test_list_service_areas_score_sort_requires_window(mock_get, caplog):
    with caplog.at_level("ERROR"):
        data = sa.list_service_areas("fake-token", sort=["score"])

    assert data is None
    mock_get.assert_not_called()
    assert "scoreSortStart" in caplog.text


# Test that score sorting works when the window is supplied
@patch("examples.service_areas.flow_service_areas_agents.requests.get")
def test_list_service_areas_score_sort_with_window(mock_get):
    mock_get.return_value = mock_json_response(SAMPLE_LIST)

    sa.list_service_areas(
        "fake-token", sort=["score"], score_sort_start=1, score_sort_end=2
    )

    params = dict(mock_get.call_args.kwargs["params"])
    assert params["scoreSortStart"] == 1
    assert params["scoreSortEnd"] == 2


# Test that get_service_area returns None on 404 rather than raising
@patch("examples.service_areas.flow_service_areas_agents.requests.get")
def test_get_service_area_404_returns_none(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_get.return_value = mock_response

    assert sa.get_service_area("fake-token", "missing-id") is None


# Test that the bulk create wraps entries in a serviceAreas array
@patch("examples.service_areas.flow_service_areas_agents.requests.post")
def test_create_service_areas_wraps_in_array(mock_post):
    mock_post.return_value = mock_json_response({"results": [SAMPLE_AREA]}, status_code=201)

    sa.create_service_areas("fake-token", [{"name": "Floor 3", "address": "1000 Example Ave"}])

    payload = mock_post.call_args.kwargs["json"]
    assert "serviceAreas" in payload
    assert payload["serviceAreas"][0]["name"] == "Floor 3"


# Test that the bulk update refuses entries missing an id, since without one the
# server cannot match the entry to an existing record
@patch("examples.service_areas.flow_service_areas_agents.requests.put")
def test_update_service_areas_requires_id_in_each_entry(mock_put, caplog):
    with caplog.at_level("ERROR"):
        result = sa.update_service_areas("fake-token", [{"name": "No id here"}])

    assert result is None
    mock_put.assert_not_called()
    assert "id" in caplog.text


# Test that a valid bulk update is sent
@patch("builtins.input", return_value="yes")
@patch("examples.service_areas.flow_service_areas_agents.requests.put")
def test_update_service_areas_success(mock_put, mock_input):
    mock_put.return_value = mock_json_response({"results": [SAMPLE_AREA]}, status_code=201)

    sa.update_service_areas("fake-token", [{"id": AREA_ID, "name": "Renamed"}])

    payload = mock_put.call_args.kwargs["json"]
    assert payload["serviceAreas"][0]["id"] == AREA_ID


# Test that the single update puts the id in the path and NOT in the body
@patch("examples.service_areas.flow_service_areas_agents.requests.put")
def test_update_service_area_body_has_no_id(mock_put):
    mock_put.return_value = mock_json_response(SAMPLE_AREA)

    sa.update_service_area("fake-token", AREA_ID, "Renamed", "1000 Example Ave")

    payload = mock_put.call_args.kwargs["json"]
    assert payload == {"name": "Renamed", "address": "1000 Example Ave"}
    assert AREA_ID in mock_put.call_args.args[0]


# Test that the bulk delete sends ids as repeated query parameters, not a body
@patch("examples.service_areas.flow_service_areas_agents.requests.delete")
@patch("builtins.input", return_value="yes")
def test_delete_service_areas_uses_repeated_query_ids(mock_input, mock_delete):
    mock_response = MagicMock()
    mock_response.status_code = 204
    mock_response.raise_for_status = MagicMock()
    mock_delete.return_value = mock_response

    deleted = sa.delete_service_areas("fake-token", [AREA_ID, OTHER_ID])

    assert deleted is True
    params = mock_delete.call_args.kwargs["params"]
    assert ("ids", AREA_ID) in params
    assert ("ids", OTHER_ID) in params
    assert "json" not in mock_delete.call_args.kwargs


# Test that declining the confirmation aborts the bulk delete entirely
@patch("examples.service_areas.flow_service_areas_agents.requests.delete")
@patch("builtins.input", return_value="no")
def test_delete_service_areas_aborts_without_confirmation(mock_input, mock_delete):
    assert sa.delete_service_areas("fake-token", [AREA_ID]) is False
    mock_delete.assert_not_called()


# Test that declining the confirmation aborts the single delete entirely
@patch("examples.service_areas.flow_service_areas_agents.requests.delete")
@patch("builtins.input", return_value="no")
def test_delete_service_area_aborts_without_confirmation(mock_input, mock_delete):
    assert sa.delete_service_area("fake-token", AREA_ID) is False
    mock_delete.assert_not_called()


# Test that display_service_areas logs the key details
def test_display_service_areas(caplog):
    with caplog.at_level("INFO"):
        sa.display_service_areas(SAMPLE_LIST)

    assert "Cleveland HQ - Floor 3" in caplog.text
    assert AREA_ID in caplog.text


# Test that display handles missing/partial data gracefully
def test_display_service_areas_partial_data(caplog):
    with caplog.at_level("INFO"):
        sa.display_service_areas({"results": [{"id": "abc"}]})

    assert "abc" in caplog.text


# Test that an empty result set is reported rather than failing
def test_display_service_areas_empty(caplog):
    with caplog.at_level("INFO"):
        sa.display_service_areas({"results": [], "pagination": {}})

    assert "No agent service areas" in caplog.text


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
@patch("examples.service_areas.flow_service_areas_agents.requests.get")
def test_read_calls_http_error(mock_get, caplog):
    mock_get.return_value = http_error_response()

    with caplog.at_level("ERROR"):
        assert sa.list_service_areas("fake-token") is None
        assert sa.get_service_area("fake-token", AREA_ID) is None

    assert "HTTP error" in caplog.text


# Test that a connection-level failure is caught rather than escaping
@patch("examples.service_areas.flow_service_areas_agents.requests.get",
       side_effect=_requests.exceptions.ConnectionError("boom"))
def test_list_connection_error(mock_get, caplog):
    with caplog.at_level("ERROR"):
        assert sa.list_service_areas("fake-token") is None

    assert "Unexpected error" in caplog.text


# Test that the name search filter is forwarded
@patch("examples.service_areas.flow_service_areas_agents.requests.get")
def test_list_forwards_search_value(mock_get):
    mock_get.return_value = mock_json_response(SAMPLE_LIST)

    sa.list_service_areas("fake-token", search_value="floor")

    params = dict(mock_get.call_args.kwargs["params"])
    assert params["searchValue"] == "floor"


# Test that HTTP errors on the write calls return None
@patch("examples.service_areas.flow_service_areas_agents.requests.post")
def test_create_http_error(mock_post):
    mock_post.return_value = http_error_response()
    assert sa.create_service_areas("fake-token", [{"name": "n"}]) is None


@patch("builtins.input", return_value="yes")
@patch("examples.service_areas.flow_service_areas_agents.requests.put")
def test_bulk_update_http_error(mock_put, mock_input):
    mock_put.return_value = http_error_response()
    assert sa.update_service_areas("fake-token", [{"id": AREA_ID}]) is None


# Test that declining the bulk update confirmation sends nothing
@patch("builtins.input", return_value="no")
@patch("examples.service_areas.flow_service_areas_agents.requests.put")
def test_bulk_update_declined(mock_put, mock_input):
    assert sa.update_service_areas("fake-token", [{"id": AREA_ID, "name": "n"}]) is None
    mock_put.assert_not_called()


@patch("examples.service_areas.flow_service_areas_agents.requests.put")
def test_single_update_http_error(mock_put):
    mock_put.return_value = http_error_response()
    assert sa.update_service_area("fake-token", AREA_ID, "n", "a") is None


# Test that an HTTP error on the bulk delete returns False
@patch("examples.service_areas.flow_service_areas_agents.requests.delete")
@patch("builtins.input", return_value="yes")
def test_bulk_delete_http_error(mock_input, mock_delete):
    mock_delete.return_value = http_error_response()
    assert sa.delete_service_areas("fake-token", [AREA_ID]) is False


# Test that a bulk delete with no ids is refused
def test_bulk_delete_requires_ids(caplog):
    with caplog.at_level("ERROR"):
        assert sa.delete_service_areas("fake-token", []) is False

    assert "No service area ids" in caplog.text


# Test that the single delete succeeds when confirmed, and reports an HTTP error
@patch("examples.service_areas.flow_service_areas_agents.requests.delete")
@patch("builtins.input", return_value="yes")
def test_single_delete_success_and_error(mock_input, mock_delete):
    r = MagicMock()
    r.status_code = 204
    r.raise_for_status = MagicMock()
    mock_delete.return_value = r
    assert sa.delete_service_area("fake-token", AREA_ID) is True

    mock_delete.return_value = http_error_response()
    assert sa.delete_service_area("fake-token", AREA_ID) is False


def run_main(input_values, **extra):
    applied = [
        patch("examples.service_areas.flow_service_areas_agents.get_token", return_value=("tok", 0)),
        patch("examples.service_areas.flow_service_areas_agents.list_service_areas",
              return_value=SAMPLE_LIST),
        patch("builtins.input", side_effect=input_values),
    ]
    for target, value in extra.items():
        applied.append(
            patch(f"examples.service_areas.flow_service_areas_agents.{target}", return_value=value)
        )
    for p in applied:
        p.start()
    try:
        sa.main()
    finally:
        for p in reversed(applied):
            p.stop()


# Test main's exit branch
def test_main_exit_branch(caplog):
    with caplog.at_level("INFO"):
        run_main(["8"])

    assert "Nothing to do" in caplog.text


# Test main's search branch
def test_main_search_branch():
    run_main(["1", "floor"])


# Test that an empty search value exits
def test_main_search_empty_exits():
    with pytest.raises(SystemExit):
        run_main(["1", " "])


# Test main's score-ranking branch
def test_main_score_branch():
    run_main(["2"])


# Test main's fetch-single branch
def test_main_fetch_single_branch():
    run_main(["3", AREA_ID], get_service_area=SAMPLE_AREA)


# Test that an empty id exits on the fetch branch
def test_main_fetch_single_empty_exits():
    with pytest.raises(SystemExit):
        run_main(["3", " "])


# Test main's bulk create branch, terminated by a blank line
def test_main_bulk_create_branch():
    run_main(
        ["4", "Floor 3|1000 Example Ave", "Floor 4|1000 Example Ave", "", "yes"],
        create_service_areas={"results": [SAMPLE_AREA]},
    )


# Test that a line without the pipe separator is rejected and retried
def test_main_bulk_create_rejects_bad_line(caplog):
    with caplog.at_level("ERROR"):
        run_main(
            ["4", "no-separator-here", "Floor 3|1000 Example Ave", "", "yes"],
            create_service_areas={"results": [SAMPLE_AREA]},
        )

    assert "name|address" in caplog.text


# Test that entering nothing at all creates nothing
def test_main_bulk_create_nothing(caplog):
    with caplog.at_level("INFO"):
        run_main(["4", ""])

    assert "Nothing to create" in caplog.text


# Test that declining the bulk create confirmation sends nothing
def test_main_bulk_create_declined():
    with patch("examples.service_areas.flow_service_areas_agents.create_service_areas") as mock_create:
        run_main(["4", "Floor 3|Addr", "", "no"])
        mock_create.assert_not_called()


# Test main's single rename branch
def test_main_rename_branch():
    run_main(["5", AREA_ID, "New name", "New address", "yes"], update_service_area=SAMPLE_AREA)


# Test that empty values on the rename branch exit
def test_main_rename_empty_values_exit():
    with pytest.raises(SystemExit):
        run_main(["5", " "])
    with pytest.raises(SystemExit):
        run_main(["5", AREA_ID, " "])
    with pytest.raises(SystemExit):
        run_main(["5", AREA_ID, "n", " "])


# Test main's bulk delete branch
def test_main_bulk_delete_branch():
    run_main(["7", f"{AREA_ID}, {OTHER_ID}"], delete_service_areas=True)


# Test that a bulk delete with no ids exits
def test_main_bulk_delete_empty_exits():
    with pytest.raises(SystemExit):
        run_main(["7", " , "])


# Test main's bulk rename branch, which requires an id on every line
def test_main_bulk_rename_branch():
    run_main(
        ["6", f"{AREA_ID}|Floor 3|Addr", ""],
        update_service_areas={"results": [SAMPLE_AREA]},
    )


# Test that a bulk rename line missing its id is rejected and retried
def test_main_bulk_rename_rejects_missing_id(caplog):
    with caplog.at_level("ERROR"):
        run_main(
            ["6", "|Floor 3|Addr", f"{AREA_ID}|Floor 3|Addr", ""],
            update_service_areas={"results": [SAMPLE_AREA]},
        )

    assert "id|name|address" in caplog.text


# Test that entering nothing updates nothing
def test_main_bulk_rename_nothing(caplog):
    with caplog.at_level("INFO"):
        run_main(["6", ""])

    assert "Nothing to update" in caplog.text
