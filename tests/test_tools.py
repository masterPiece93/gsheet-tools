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
    invalid_url_2 = "123"
    assert is_valid_google_url(valid_url) is True
    assert is_valid_google_url(invalid_url) is False
    assert is_valid_google_url(invalid_url_2) is False


def test_url_resolver_valid_url():
    url = "https://docs.google.com/spreadsheets/d/12345/edit?gid=67890"
    resolver = UrlResolver(url)
    assert resolver.is_valid is True
    assert resolver.url_data.file_id == "12345"
    assert resolver.url_data.gid == "67890"
    assert resolver.raw_url == url


def test_url_resolver_invalid_url():
    url = "https://example.com/sheets/d/12345/edit"
    resolver = UrlResolver(url)
    assert resolver.is_valid is False
    assert resolver.url_data is None
    assert resolver.raw_url == url

def test_url_resolver_invalid_url__not_spreadsheet():
    valid_scheme = "https"
    valid_domain = "docs.google.com"
    # but not a valid spreadsheet url
    url = f"{valid_scheme}://{valid_domain}/sheets/d/12345/edit"
    resolver = UrlResolver(url)
    assert resolver.is_valid is False
    assert resolver.url_data is None

def test_url_resolver_invalid_url__missing_gid():
    valid_scheme = "https"
    valid_domain = "docs.google.com"
    valid_spreadsheet_component = "spreadsheets/d/1Z8jNZTtw4lOgBSbudmHyzPZE0Ln1fqtyCuoCvpqktM0"
    # but `gid` missing
    url = f"{valid_scheme}://{valid_domain}/{valid_spreadsheet_component}/edit"
    resolver = UrlResolver(url)
    assert resolver.is_valid is True
    assert resolver.url_data is not None
    assert resolver.url_data.gid is None
    assert resolver.url_data.file_id is not None

def test_url_resolver_invalid_url__missing_file_id():
    valid_scheme = "https"
    valid_domain = "docs.google.com"
    valid_spreadsheet_component_with_missing_file_id = "spreadsheets/d/"
    # but `gid` missing
    url = f"{valid_scheme}://{valid_domain}/{valid_spreadsheet_component_with_missing_file_id}/edit"
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

def test_check_sheet_origin_uploaded_converted_t2():
    mock_service = MagicMock()
    mock_service.files().get().execute.return_value = {
        "mimeType": SheetMimetype.ORIGINAL,
        "originalFilename": "example.xls",
    }
    origin, details = check_sheet_origin(mock_service, "file_id")
    assert origin == SheetOrigins.UPLOADED_CONVERTED
    assert details.is_parsable is True
    assert details.original_extension == "xls"

def test_check_sheet_origin_uploaded_converted_t3():
    mock_service = MagicMock()
    mock_service.files().get().execute.return_value = {
        "mimeType": SheetMimetype.ORIGINAL,
        "originalFilename": "example.csv",
    }
    origin, details = check_sheet_origin(mock_service, "file_id")
    assert origin == SheetOrigins.UPLOADED_CONVERTED
    assert details.is_parsable is True
    assert details.original_extension == "csv"

def test_check_sheet_origin_uploaded_converted_t4():
    mock_service = MagicMock()
    mock_service.files().get().execute.return_value = {
        "mimeType": SheetMimetype.ORIGINAL,
        "originalFilename": "example.jpeg",
    }
    origin, details = check_sheet_origin(mock_service, "file_id")
    assert origin == SheetOrigins.UPLOADED_CONVERTED
    assert details.is_parsable is True
    assert details.original_extension == "unidentified"


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

def test_check_sheet_origin_uploaded_non_converted_t2():
    mock_service = MagicMock()
    mock_service.files().get().execute.return_value = {
        "mimeType": SheetMimetype.MICROSOFT_EXCEL_XLS,
        "originalFilename": None,
    }
    origin, details = check_sheet_origin(mock_service, "file_id")
    assert origin == SheetOrigins.UPLOADED_NON_CONVERTED
    assert details.is_parsable is False
    assert details.original_extension == "xls"

def test_check_sheet_origin_uploaded_non_converted_t3():
    mock_service = MagicMock()
    mock_service.files().get().execute.return_value = {
        "mimeType": SheetMimetype.STANDARD_CSV,
        "originalFilename": None,
    }
    origin, details = check_sheet_origin(mock_service, "file_id")
    assert origin == SheetOrigins.UPLOADED_NON_CONVERTED
    assert details.is_parsable is False
    assert details.original_extension == "csv"

def test_check_sheet_origin_uploaded_non_converted_t4():
    mock_service = MagicMock()
    mock_service.files().get().execute.return_value = {
        "mimeType": "image/jpg",
        "originalFilename": None,
    }
    origin, details = check_sheet_origin(mock_service, "file_id")
    assert origin == SheetOrigins.UPLOADED_NON_CONVERTED
    assert details.is_parsable is False
    assert details.original_extension == "unidentified"


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


def test_get_gid_sheets_data():
    mock_service = MagicMock()
    mock_service.get().execute.return_value = {
        "sheets": [
            {"properties": {"sheetId": "67890", "title": "Sheet1"}},
            {"properties": {"sheetId": "12345", "title": "Sheet2"}},
        ]
    }
    mock_service.values().get().execute.return_value = {"values": [["Name", "Age"]]}
    title, data = get_gid_sheets_data(mock_service, "file_id", "67890")
    assert title == "Sheet1"
    assert data == [["Name", "Age"]]


def test_get_gsheet_data__by_gid():
    mock_service = MagicMock()
    mock_service.get().execute.return_value = {
        "sheets": [
            {"properties": {"sheetId": "67890", "title": "Sheet1"}},
            {"properties": {"sheetId": "12345", "title": "Sheet2"}},
        ]
    }
    mock_service.values().get().execute.return_value = {"values": [["Name", "Age"]]}
    title, data = get_gsheet_data(mock_service, "file_id", by="gid", gid="67890")
    assert title == "Sheet1"
    assert data == [["Name", "Age"]]

def test_get_gsheet_data__by_gid_404():
    """
    when sheet not found by gid
    """
    mock_service = MagicMock()
    mock_service.get().execute.return_value = {
        "sheets": [
            {"properties": {"sheetId": "67890", "title": "Sheet1"}},
            {"properties": {"sheetId": "12345", "title": "Sheet2"}},
        ]
    }
    mock_service.values().get().execute.return_value = {"values": [["Name", "Age"]]}
    title, data = get_gsheet_data(mock_service, "file_id", by="gid", gid="00000", not_found_priority={'sheet_name': 'Sheet2'})
    assert title == "Sheet2"
    assert data == [["Name", "Age"]]

def test_get_gsheet_data__by_sheet_name():
    mock_service = MagicMock()
    mock_service.get().execute.return_value = {
        "sheets": [
            {"properties": {"sheetId": "67890", "title": "Sheet1"}},
            {"properties": {"sheetId": "12345", "title": "Sheet2"}},
        ]
    }
    mock_service.values().get().execute.return_value = {"values": [["Name", "Age"]]}
    title, data = get_gsheet_data(mock_service, "file_id", by="sheet_name", sheet_name="Sheet1")
    assert title == "Sheet1"
    assert data == [["Name", "Age"]]

def test_get_gsheet_data__by_sheet_name_404():
    mock_service = MagicMock()
    mock_service.get().execute.return_value = {
        "sheets": [
            {"properties": {"sheetId": "67890", "title": "Sheet1", "index": "0"}},
            {"properties": {"sheetId": "12345", "title": "Sheet2", "index": "1"}},
            {"properties": {"sheetId": "12351", "title": "default", "index": "2"}},
        ]
    }
    mock_service.values().get().execute.return_value = {"values": [["Name", "Age"]]}
    title, data = get_gsheet_data(mock_service, "file_id", by="sheet_name", sheet_name="SomeInvalidName", not_found_priority={'sheet_position': '2'})
    assert title == "default"
    assert data == [["Name", "Age"]]

def test_get_gsheet_data__fallback_404():
    mock_service = MagicMock()
    mock_service.get().execute.return_value = {
        "sheets": [
            {"properties": {"sheetId": "67890", "title": "Sheet1", "index": "0"}},
            {"properties": {"sheetId": "12345", "title": "Sheet2", "index": "1"}},
            {"properties": {"sheetId": "12351", "title": "default", "index": "2"}},
        ]
    }
    mock_service.values().get().execute.return_value = {"values": [["Name", "Age"]]}
    title, data = get_gsheet_data(mock_service, "file_id", by="sheet_name", sheet_name="SomeInvalidName", not_found_priority={'sheet_position': '3'})
    assert title == ""
    assert data == []

def test_get_gsheet_data_invalid_arguments():
    mock_service = MagicMock()
    with pytest.raises(Exceptions.GsheetToolsArgumentError, match=r"Argument::[by,gid]|with `by='gid'` you cannot pass `gid=None`"):
        get_gsheet_data(mock_service, "file_id", by="gid", gid=None)
    
def test_get_gsheet_data_invalid_arguments_t2():
    mock_service = MagicMock()
    with pytest.raises(Exceptions.GsheetToolsArgumentError, match=r"Argument::[by,sheet_name]|with `by='sheet_name'` you cannot pass `sheet_name=None`"):
        get_gsheet_data(mock_service, "file_id", by="sheet_name", sheet_name=None)

def test_get_gsheet_data_invalid_arguments_t3():
    mock_service = MagicMock()
    with pytest.raises(Exceptions.GsheetToolsArgumentError, match=r"Argument::[by,sheet_position]|with `by='sheet_position'` you cannot pass `sheet_position=None`"):
        get_gsheet_data(mock_service, "file_id", by="sheet_position", sheet_position=None)
