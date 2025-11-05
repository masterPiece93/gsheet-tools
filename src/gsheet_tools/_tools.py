"""
This module provides a set of tools for interacting with Google Sheets data.

It includes utilities for:
- Validating and parsing Google Sheets URLs.
- Fetching data from Google Sheets using the Google Sheets API.
- Formatting sheet names into snake_case.
- Identifying the origin and MIME type of Google Sheets files.
- Preparing pandas DataFrames from Google Sheets data.

Classes:
- Exceptions: Custom exception classes for handling errors specific to Google Sheets processing.
- UrlResolver: Resolves and validates Google Sheets URLs, extracting file and sheet IDs.
- NameFormatter: Provides utilities for formatting sheet names.
- SheetOrigins: Enum for identifying the origin of a Google Sheet.
- SheetMimetype: Enum for identifying the MIME type of a Google Sheet.

Functions:
- get_gid_sheets_data: Fetches data for a specific sheet by its GID or the first sheet by default.
- get_gsheet_data: Fetches data from a Google Sheet with various selection options.
- check_sheet_origin: Determines the origin and MIME type of a Google Sheet file.
- is_valid_google_url: Validates if a URL is a valid Google Sheets URL.
- prepare_dataframe: Converts Google Sheets data into a pandas DataFrame.

This module is designed to simplify working with Google Sheets data and provide robust error
handling for common issues.
"""

import dataclasses
import re
from collections import namedtuple
from enum import Enum
from typing import Any, Dict, List, NamedTuple, Optional, Tuple
from urllib.parse import urlparse

import pandas as pd

from gsheet_tools._exceptions import GsheetToolExceptionsBase

__all__ = [
    "Exceptions",
    "UrlResolver",
    "NameFormatter",
    "SheetOrigins",
    "SheetMimetype",
    "get_gid_sheets_data",
    "check_sheet_origin",
    "is_valid_google_url",
    "prepare_dataframe",
]


class Exceptions:
    """
    Custom exception classes for handling errors specific to Google Sheets processing.
    """

    class GoogleSpreadsheetProcessingError(GsheetToolExceptionsBase):
        """
        Raised when there is an issue in parsing specific Google Sheets.
        """

    class GsheetToolsArgumentError(GsheetToolExceptionsBase):
        """
        Raised when invalid arguments are passed to GSheet tools functions.
        """

        def __init__(self, arg_name: str, message: str, *args: tuple) -> None:
            prefix = f"Argument::{arg_name}"
            self.message = f"{prefix}|{message}"
            super().__init__(self.message, *args)


class UrlResolver:
    """
    Resolves and validates Google Sheets URLs, extracting file and sheet IDs.

    Args:
        raw_url (str): The raw URL of the Google Sheet.

    Attributes:
        raw_url (str): The raw URL of the Google Sheet.
        is_valid (bool): Indicates whether the URL is valid.
        url_data (Optional[UrlResolver.UrlData]): Resolved fields of the URL.

    Notes:
        Supported URL formats:
        - https://docs.google.com/spreadsheets/d/{GOOGLE-SHEET-RESOURCE-ID}/edit?gid={SHEET-GID}#gid=546508778 # pylint: disable=C0301
        - https://docs.google.com/spreadsheets/d/{GOOGLE-SHEET-RESOURCE-ID}/edit?usp=sharing
    """

    @dataclasses.dataclass(frozen=True)
    class UrlData:
        """
        Represents Url Data retrieved
        """

        file_id: str
        gid: str

    def __init__(self, raw_url: str):
        self._raw_url: str = raw_url
        self._is_valid: bool = False
        self._url_data: Optional[UrlResolver.UrlData] = None
        self._process()

    @property
    def raw_url(self) -> str:
        """ReadOnly"""
        return self._raw_url

    @property
    def is_valid(self) -> bool:
        """ReadOnly"""
        return self._is_valid

    @property
    def url_data(self) -> Optional[UrlData]:
        """ReadOnly"""
        return self._url_data

    def _process(self) -> None:
        """
        Initializes the fields by validating and parsing the URL.
        """
        if not is_valid_google_url(self._raw_url):
            return
        if "spreadsheets" not in self._raw_url:
            return
        match = re.search(r"/d/([a-zA-Z0-9-_]+)(?:.*?gid=([0-9]+))?", self._raw_url)
        if match:
            _file_id = match.group(1)
            _gid = match.group(2)
            self._is_valid = True
            self._url_data = self.UrlData(file_id=_file_id, gid=_gid)


class NameFormatter:
    """
    Provides utilities for formatting sheet names.
    """

    @staticmethod
    def to_snake_case(text: str) -> str:
        """
        Converts a sheet name to snake_case.

        Args:
            text (str): The input text to format.

        Returns:
            str: The formatted text in snake_case.
        """
        text = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", text)
        text = re.sub(r"[\s-]+", "_", text)
        return text.lower()


class SheetOrigins(str, Enum):
    """
    Enum for identifying the origin of a Google Sheet.
    """

    GOOGLE_SHEET_TOOL = "GOOGLE_SHEET_TOOL"
    UPLOADED_CONVERTED = "UPLOADED_AND_CONVERTED"
    UPLOADED_NON_CONVERTED = "UPLOADED_AND_NOT_CONVERTED"
    UNDEFINED = "UNDEFINED"


class SheetMimetype(str, Enum):
    """
    Enum for identifying the MIME type of a Google Sheet.
    """

    ORIGINAL = "application/vnd.google-apps.spreadsheet"
    MICROSOFT_EXCEL_XLSX = (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    MICROSOFT_EXCEL_XLS = "application/vnd.ms-excel"
    STANDARD_CSV = "text/csv"


def _fetch_data(sheet: object, sheet_id: str, cell_range: str) -> list:
    """
    Fetches data from a single sheet.

    Args:
        sheet (object): The Google Sheets API service object.
        sheet_id (str): The ID of the spreadsheet.
        range (str): The range of cells to fetch.

    Returns:
        list: The fetched data.
    """
    result = (
        sheet.values()  # type: ignore[attr-defined]
        .get(spreadsheetId=sheet_id, range=cell_range)  # type: ignore[attr-defined]
        .execute()
    )
    return result.get("values", [])


def get_gid_sheets_data(
    sheet: object, sheet_id: str, gid: Optional[str], without_headers: bool = False
) -> Tuple[str, list]:
    """
    Fetches data for a specific sheet by its GID or the first sheet by default.

    Args:
        sheet (object): The Google Sheets API service object.
        sheet_id (str): The ID of the spreadsheet.
        gid (Optional[str]): The GID of the sheet.
        without_headers (bool): Whether to exclude headers from the data.

    Returns:
        Tuple[str, list]: The sheet title and its data.

    Raises:
        Exception: If the sheet is not found.
    """

    spreadsheet_metadata = sheet.get(  # type: ignore[attr-defined]
        spreadsheetId=sheet_id,
        fields="sheets.properties",  # Request only the properties of each sheet
    ).execute()

    found_sheet_properties = None
    if "sheets" in spreadsheet_metadata:

        search_on_key, search_for_value = (
            ("sheetId", str(gid)) if gid is not None else ("index", str(0))
        )

        for indivisual_sheet in spreadsheet_metadata["sheets"]:
            if str(indivisual_sheet["properties"][search_on_key]) == search_for_value:
                found_sheet_properties = indivisual_sheet["properties"]
                break
        if not found_sheet_properties:
            raise Exception("sheet not found")
        title: str = found_sheet_properties.get("title")
        _range = f"{title}"
        if without_headers:
            _range = _range + "!" + "A2:z999999"
        return title, _fetch_data(sheet, sheet_id, cell_range=_range)
    return "", []


def get_gsheet_data(
    sheet: object,
    file_id: str,
    by: str = "all",
    gid: Optional[str] = None,
    sheet_name: Optional[str] = None,
    sheet_position: Optional[int] = None,
    without_headers: bool = False,
    custom_tabular_range: Tuple[str, str] = ("A1", "z999999"),
    not_found_priority: Optional[Dict[str, Any]] = None,
) -> Tuple[str, List[Optional[List]]]:
    """
    Fetches data from a Google Sheet with various selection options.

    Args:
        sheet (object): The Google Sheets API service object.
        file_id (str): The ID of the spreadsheet.
        by (str): The selection method ('all', 'gid', 'sheet_name', etc.).
        gid (Optional[str]): The GID of the sheet (if by='gid').
        sheet_name (Optional[str]): The name of the sheet (if by='sheet_name').
        sheet_position (Optional[int]): The position of the sheet (if by='sheet_position').
        without_headers (bool): Whether to exclude headers from the data.
        custom_tabular_range (Tuple[str, str]): The custom range of cells to fetch.
        not_found_priority (Optional[List]): Priority list for fallback options.

    Returns:
        List[List]: The fetched data.

    Raises:
        Exceptions.GsheetToolsArgumentError: If invalid arguments are passed.
    """

    if by == "gid" and gid is None:
        raise Exceptions.GsheetToolsArgumentError(
            "[by,gid]", f"with `{by=}` you cannot pass `{gid=}`."
        )
    if by == "sheet_name" and sheet_name is None:
        raise Exceptions.GsheetToolsArgumentError(
            "[by,sheet_name]", f"with `{by=}` you cannot pass `{sheet_name=}`."
        )
    if by == "sheet_position" and sheet_position is None:
        raise Exceptions.GsheetToolsArgumentError(
            "[by,sheet_position]", f"with `{by=}` you cannot pass `{sheet_position=}`."
        )

    # fetch metadata on google sheet
    spreadsheet_metadata = sheet.get(  # type: ignore[attr-defined]
        spreadsheetId=file_id,
        fields="sheets.properties",  # Request only the properties of each sheet
    ).execute()
    # check if any sheet exists
    if "sheets" not in spreadsheet_metadata:
        return "", []

    translation_map: Dict[str, Tuple[str, Any]] = {
        "gid": ("sheetId", gid),
        "sheet_name": ("title", sheet_name),
        "sheet_position": ("index", sheet_position),
    }
    try:
        search_on_key, search_for_value = translation_map[by]
    except KeyError as e:
        raise Exception(f"value not supported yet. {e}")

    def _find(
        indivisual_sheet_properties: list, search_on_key: str, search_for_value: str
    ) -> Optional[dict]:
        """ """
        found_sheet_properties = None
        for indivisual_sheet in indivisual_sheet_properties:
            if str(indivisual_sheet["properties"][search_on_key]) == search_for_value:
                found_sheet_properties = indivisual_sheet["properties"]
                break
        return found_sheet_properties

    def _fallback_safe_find_proprties(spreadsheet_metadata: dict) -> Optional[dict]:
        """ """
        found_sheet_properties = _find(
            spreadsheet_metadata["sheets"], search_on_key, search_for_value
        )
        if found_sheet_properties or not not_found_priority:
            return found_sheet_properties
        for (
            first_fallback_search_key,
            first_fallback_search_value,
        ) in not_found_priority.items():
            if (
                first_fallback_search_value is not None
                and first_fallback_search_key in translation_map
            ):
                first_fallback_search_key_translated, _ = translation_map[
                    first_fallback_search_key
                ]
                found_sheet_properties = _find(
                    spreadsheet_metadata["sheets"],
                    first_fallback_search_key_translated,
                    first_fallback_search_value,
                )
                if found_sheet_properties:
                    return found_sheet_properties
        return None

    found_sheet_properties = _fallback_safe_find_proprties(spreadsheet_metadata)
    sheet_title: str = ""
    sheet_data: list = []
    if found_sheet_properties:
        # properties found
        sheet_title = found_sheet_properties.get("title")  # type: ignore[assignment]
        _range = f"{sheet_title}"
        if without_headers:
            _range = _range + "!" + "A2:z999999"
        return sheet_title, _fetch_data(sheet, file_id, cell_range=_range)
    # default return
    return sheet_title, sheet_data


def check_sheet_origin(
    google_drive_service: object, file_id: str
) -> Tuple[str, NamedTuple]:
    """
    Determines the origin and MIME type of a Google Sheet file.

    Args:
        google_drive_service (object): The Google Drive API service object.
        file_id (str): The ID of the file.

    Returns:
        Tuple[str, NamedTuple]: The origin and details of the file.
    """

    file_metadata = (
        google_drive_service.files()  # type: ignore[attr-defined]
        .get(fileId=file_id, fields="mimeType,originalFilename")
        .execute()
    )

    mime_type = file_metadata.get("mimeType")
    original_filename = file_metadata.get(
        "originalFilename"
    )  # May not always be present or reliable for conversion history
    OriginDetails: namedtuple = namedtuple(  # type: ignore[misc]
        "OriginDetails",
        field_names=(
            "is_parsable",
            "mimetype",
            "original_extension",
            "original_filename",
        ),
        defaults=[None],
    )
    OriginDetails.__annotations__ = {
        "is_parsable": bool,
        "mimetype": str,
        "original_extension": str,
        "original_filename": str,
    }

    origin: str = SheetOrigins.UNDEFINED.value
    is_parsable = True
    original_extension = None
    if mime_type == SheetMimetype.ORIGINAL:
        if original_filename:
            origin = SheetOrigins.UPLOADED_CONVERTED.value
            is_parsable = True
            if original_filename.lower().endswith(".xlsx"):
                original_extension = "xlsx"
            elif original_filename.lower().endswith(".xls"):
                original_extension = "xls"
            elif original_filename.lower().endswith(".csv"):
                original_extension = "csv"
            else:
                # unsupported deriving origin
                original_extension = "unidentified"
        else:
            # we are unsure if it is a derived one OR original
            origin = SheetOrigins.GOOGLE_SHEET_TOOL.value
    else:
        # derived origin & not original
        # unsupported formats
        origin = SheetOrigins.UPLOADED_NON_CONVERTED.value
        is_parsable = False
        if mime_type == SheetMimetype.MICROSOFT_EXCEL_XLSX:
            # identified & usupported - please use upload from comp.
            original_extension = "xlsx"
        elif mime_type == SheetMimetype.MICROSOFT_EXCEL_XLS:
            # identified & usupported - please use upload from comp.
            original_extension = "xls"
        elif mime_type == SheetMimetype.STANDARD_CSV:
            # identified & usupported - please use upload from comp.
            original_extension = "csv"
        else:
            # un-identified format & unsupported
            original_extension = "unidentified"
    return origin, OriginDetails(  # type: ignore[call-arg]
        is_parsable=is_parsable,
        mimetype=mime_type,
        original_extension=original_extension,
        original_filename=original_filename,
    )


def is_valid_google_url(url: str) -> bool:
    """
    Validates if a URL is a valid Google Sheets URL.

    Args:
        url (str): The URL to validate.

    Returns:
        bool: True if the URL is valid, False otherwise.
    """
    VALID_SCHEME = "https"  # pylint: disable=C0103
    VALID_DOMAIN = "docs.google.com"  # pylint: disable=C0103
    try:
        result = urlparse(url)
        return (
            all([result.scheme, result.netloc])
            and result.scheme == VALID_SCHEME
            and result.netloc == VALID_DOMAIN
        )
    except ValueError:
        return False


def prepare_dataframe(spreadsheet_data: List[List[Any]]) -> pd.DataFrame:
    """
    Converts Google Sheets data into a pandas DataFrame.

    Args:
        spreadsheet_data (List[List[Any]]): The data from the spreadsheet.

    Returns:
        pd.DataFrame: The resulting DataFrame.

    Raises:
        Exceptions.GoogleSpreadsheetProcessingError: If the data is invalid or empty.
    """

    spreadsheet_data = list(filter(None, spreadsheet_data))  # remove empty rows .
    if not spreadsheet_data:
        raise Exceptions.GoogleSpreadsheetProcessingError("GSHEET.PROCESSING.BLANK01")
    column_names: List[str] = spreadsheet_data[0]
    if "" in column_names:
        raise Exceptions.GoogleSpreadsheetProcessingError("GSHEET.PROCESSING.BLANK02")
    padded_spreadsheet_data: List[List[Any]] = [
        arr + [""] * (len(column_names) - len(arr)) for arr in spreadsheet_data[1:]
    ]
    spreadsheet_dataframe = pd.DataFrame(padded_spreadsheet_data, columns=column_names)
    return spreadsheet_dataframe
