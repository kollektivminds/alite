import pytest
import json
import requests
from unittest.mock import patch, MagicMock
from alite_backend.words.lookup import LookupFDAPI

# @pytest.fixture
# def fetcher():
#     return LookupFDAPI()


# Use 'patch' to intercept calls to requests.get inside your lookup module
#@patch("alite_backend.words.lookup.requests.get")
def test_make_request_success(monkeypatch):
    """
    ARRANGE: Configure the fake API to return a 200 OK and a dummy JSON payload.
    """
    # Create a mock response object
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"word": "тест", "meanings": []}

    def mock_get(url, *args, **kwargs):
        return mock_response

    # 2. MONKEYPATCH: Safely swap the real requests.get for our fake one
    monkeypatch.setattr(requests, "get", mock_get)

    # ACT: Call your actual fetcher method
    result = LookupFDAPI()._make_request(word="тест", lang="ru")
    print(result)
    # ASSERT: Ensure the fetcher properly returned the JSON data
    assert result is not None
    assert result["word"] == "тест"
    # Ensure requests.get was actually called with the correct URL
    # result.assert_called_once_with(
    #     "https://freedictionaryapi.com/api/v1/entries/ru/тест", timeout=5
    # )


@patch("alite_backend.words.lookup.requests.get")
def test_make_request_handles_404(mock_get, fetcher):
    """
    Tests that your application doesn't crash if a word isn't in the dictionary.
    """
    import requests

    # ARRANGE: Force the mock to raise an HTTPError (simulating a 404 or 500)
    mock_get.side_effect = requests.exceptions.HTTPError("404 Not Found")

    # ACT
    result = fetcher._make_request("неизвестноеслово", lang="ru")

    # ASSERT: The fetcher should safely catch the error and return None
    assert result is None
