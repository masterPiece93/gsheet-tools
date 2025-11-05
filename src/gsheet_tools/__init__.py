# pylint: disable=duplicate-code
"""
GSheet Tools Package

This package provides a set of tools and utilities for interacting with Google Sheets data.
It includes functionality for validating and parsing Google Sheets URLs, fetching and processing
data using the Google Sheets API, and preparing pandas DataFrames from the retrieved data.

Modules:
- `_tools`: Contains the core tools and utilities for Google Sheets interaction.

Exports:
- GsheetToolExceptionsBase: Base exception class for all GSheet Tools-related errors.
- Exceptions: Custom exception classes for handling specific Google Sheets processing errors.
- UrlResolver: Resolves and validates Google Sheets URLs, extracting file and sheet IDs.
- NameFormatter: Provides utilities for formatting sheet names into snake_case.
- SheetOrigins: Enum for identifying the origin of a Google Sheet.
- SheetMimetype: Enum for identifying the MIME type of a Google Sheet.
- get_gid_sheets_data: Fetches data for a specific sheet by its GID or the first sheet by default.
- check_sheet_origin: Determines the origin and MIME type of a Google Sheet file.
- is_valid_google_url: Validates if a URL is a valid Google Sheets URL.
- prepare_dataframe: Converts Google Sheets data into a pandas DataFrame.

Metadata:
- Version: 0.1.1
- Author: Ankit Yadav
- Email: ankit8290@gmail.com
"""

from gsheet_tools._exceptions import GsheetToolExceptionsBase
from gsheet_tools._tools import (
    Exceptions,  # all public assistive tools
    NameFormatter,
    SheetMimetype,
    SheetOrigins,
    UrlResolver,
    check_sheet_origin,
    get_gid_sheets_data,
    is_valid_google_url,
    prepare_dataframe,
)

__all__ = [
    "GsheetToolExceptionsBase",
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
__version__ = "0.1.1"
__author__ = "Ankit Yadav"
__email__ = "ankit8290@gmail.com"
