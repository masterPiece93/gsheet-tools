import pytest
from gsheet_tools._tools import (
    Exceptions,
    UrlResolver,
    NameFormatter,
    SheetOrigins,
    SheetMimetype,
    get_gid_sheets_data,
    get_gsheet_data,
    check_sheet_origin,
    is_valid_google_url,
    prepare_dataframe,
)
from unittest.mock import MagicMock


def test_is_valid_google_url():
    valid_url = "https://docs.google.com/spreadsheets/d/12345/edit?usp=sharing"
    invalid_url = "https://example.com/sheets/d/12345/edit"
    assert is_valid_google_url(valid_url) is True
    assert is_valid_google_url(invalid_url) is False


def test_url_resolver_valid_url():
    url = "https://docs.google.com/spreadsheets/d/12345/edit?gid=67890"
    resolver = UrlResolver(url)
    assert resolver.is_valid is True
    assert resolver.url_data.file_id == "12345"
    assert resolver.url_data.gid == "67890"


def test_url_resolver_invalid_url():
    url = "https://example.com/sheets/d/12345/edit"
    resolver = UrlResolver(url)
    assert resolver.is_valid is False
    assert resolver.url_data is None


def test_name_formatter_to_snake_case():
    assert NameFormatter.to_snake_case("SheetName") == "sheet_name"
    assert NameFormatter.to_snake_case("Sheet Name") == "sheet_name"
    assert NameFormatter.to_snake_case("Sheet-Name") == "sheet_name"


def test_check_sheet_origin_google_sheet_tool():
    mock_service = MagicMock()
    mock_service.files().get().execute.return_value = {
        "mimeType": SheetMimetype.ORIGINAL,
        "originalFilename": None,
    }
    origin, details = check_sheet_origin(mock_service, "file_id")
    assert origin == SheetOrigins.GOOGLE_SHEET_TOOL
    assert details.is_parsable is True
    assert details.mimetype == SheetMimetype.ORIGINAL


def test_check_sheet_origin_uploaded_converted():
    mock_service = MagicMock()
    mock_service.files().get().execute.return_value = {
        "mimeType": SheetMimetype.ORIGINAL,
        "originalFilename": "example.xlsx",
    }
    origin, details = check_sheet_origin(mock_service, "file_id")
    assert origin == SheetOrigins.UPLOADED_CONVERTED
    assert details.is_parsable is True
    assert details.original_extension == "xlsx"


def test_check_sheet_origin_uploaded_non_converted():
    mock_service = MagicMock()
    mock_service.files().get().execute.return_value = {
        "mimeType": SheetMimetype.MICROSOFT_EXCEL_XLSX,
        "originalFilename": None,
    }
    origin, details = check_sheet_origin(mock_service, "file_id")
    assert origin == SheetOrigins.UPLOADED_NON_CONVERTED
    assert details.is_parsable is False
    assert details.original_extension == "xlsx"


def test_prepare_dataframe_valid_data():
    data = [["Name", "Age"], ["Alice", 30], ["Bob", 25]]
    df = prepare_dataframe(data)
    assert list(df.columns) == ["Name", "Age"]
    assert df.iloc[0]["Name"] == "Alice"
    assert df.iloc[1]["Age"] == 25


def test_prepare_dataframe_empty_data():
    with pytest.raises(Exceptions.GoogleSpreadsheetProcessingError):
        prepare_dataframe([])


def test_prepare_dataframe_missing_column_names():
    data = [["", "Age"], ["Alice", 30], ["Bob", 25]]
    with pytest.raises(Exceptions.GoogleSpreadsheetProcessingError):
        prepare_dataframe(data)


# def test_get_gid_sheets_data():
#     mock_service = MagicMock()
#     mock_service.get().execute.return_value = {
#         "sheets": [
#             {"properties": {"sheetId": "67890", "title": "Sheet1"}},
#             {"properties": {"sheetId": "12345", "title": "Sheet2"}},
#         ]
#     }
#     mock_service.values().get().execute.return_value = {"values": [["Name", "Age"]]}
#     title, data = get_gid_sheets_data(mock_service, "file_id", "67890")
#     assert title == "Sheet1"
#     assert data == [["Name", "Age"]]


# def test_get_gsheet_data_by_gid():
#     mock_service = MagicMock()
#     mock_service.get().execute.return_value = {
#         "sheets": [
#             {"properties": {"sheetId": "67890", "title": "Sheet1"}},
#             {"properties": {"sheetId": "12345", "title": "Sheet2"}},
#         ]
#     }
#     mock_service.values().get().execute.return_value = {"values": [["Name", "Age"]]}
#     data = get_gsheet_data(mock_service, "file_id", by="gid", gid="67890")
#     assert data == [["Name", "Age"]]


def test_get_gsheet_data_invalid_arguments():
    mock_service = MagicMock()
    with pytest.raises(Exceptions.GsheetToolsArgumentError):
        get_gsheet_data(mock_service, "file_id", by="gid", gid=None)