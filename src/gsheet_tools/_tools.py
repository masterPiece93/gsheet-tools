import dataclasses
import re
from collections import namedtuple
from enum import Enum
from typing import (
    List,
    Any,
    Tuple,
    Optional,
    NamedTuple,
    Dict
)
from urllib.parse import urlparse
from gsheet_tools import GsheetToolExceptionsBase

import pandas as pd

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
    Tool Exceptions
    """

    class GoogleSpreadsheetProcessingError(GsheetToolExceptionsBase):
        """
        Issue in Parsing specific Google Sheets
        [Exception]"""

        pass
    class GsheetToolsArgumentError(GsheetToolExceptionsBase):
        def __init__(self, message, *args):
            prefix = "ArgumentError"
            self.message=f"{prefix}|{message}"
            super().__init__(*args)


class UrlResolver:
    """
    Resolves the Google sheet url.

    Args:
        - raw_url [str]: raw_url of file

    Kwargs: None

    Returns:

        - raw_url (str) : raw_url of file

        - is_valid (bool) : if the sheet url is valid

        - url_data( UrlResolver.UrlData) : resolved fields of url

    There is expectation of following types of google url only :
        - https://docs.google.com/spreadsheets/d/{GOOGLE-SHEET-RESOURCE-ID}/edit?gid={SHEET-GID}#gid=546508778
        - https://docs.google.com/spreadsheets/d/{GOOGLE-SHEET-RESOURCE-ID}/edit?usp=sharing

    GOOGLE-SHEET-RESOURCE-ID : is the id the uniquely identifies the google sheet file
    SHEET-GID : is the id the uniquely identifies the indivisual sheets inside the google sheet file
    """

    @dataclasses.dataclass(frozen=True)
    class UrlData:
        file_id: str
        gid: str

    def __init__(self, raw_url: str):
        self._raw_url: str = raw_url
        self._is_valid: bool = False
        self._url_data: Optional[UrlResolver.UrlData] = None
        self._process()

    @property
    def raw_url(self) -> str:
        return self._raw_url

    @property
    def is_valid(self) -> bool:
        return self._is_valid

    @property
    def url_data(self) -> Optional[UrlData]:
        return self._url_data

    def _process(self) -> None:
        """
        initializes the fields appropriately
        """
        if not is_valid_google_url(self._raw_url):
            return
        if "spreadsheets" not in self._raw_url:
            return
        match = re.search(r"/d/([a-zA-Z0-9-_]+)(?:.*?gid=([0-9]+))?", self._raw_url)
        if match:
            _file_id = match.group(1)
            if not _file_id:
                return
            _gid = match.group(2)
            self._is_valid = True
            self._url_data = self.UrlData(file_id=_file_id, gid=_gid)


class NameFormatter:
    """
    Name related formatting
    """

    @staticmethod
    def to_snake_case(text: str) -> str:
        """Sheet name to Snake Case"""
        # Insert underscore before uppercase letters preceded by a lowercase letter
        text = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", text)
        # Replace spaces, hyphens, and multiple underscores with a single underscore
        text = re.sub(r"[\s-]+", "_", text)
        # Convert to lowercase
        return text.lower()


class SheetOrigins(str, Enum):
    """
    Indicators for sheet origination
    """

    GOOGLE_SHEET_TOOL = "GOOGLE_SHEET_TOOL"
    UPLOADED_CONVERTED = "UPLOADED_AND_CONVERTED"
    UPLOADED_NON_CONVERTED = "UPLOADED_AND_NOT_CONVERTED"
    UNDEFINED = "UNDEFINED"


class SheetMimetype(str, Enum):
    """
    Official sheet mimetypes
    """

    ORIGINAL = "application/vnd.google-apps.spreadsheet"
    MICROSOFT_EXCEL_XLSX = (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    MICROSOFT_EXCEL_XLS = "application/vnd.ms-excel"
    STANDARD_CSV = "text/csv"


def _fetch_data(sheet: object, sheet_id: str, range: str) -> list:
    """Fetch single sheet data
    [utility]"""
    result = sheet.values().get(spreadsheetId=sheet_id, range=range).execute()
    values: list = result.get("values", [])
    return values


def get_gid_sheets_data(
    sheet: object, sheet_id: str, gid: Optional[str], without_headers: bool = False
) -> Tuple[str, list]:
    """Fetch sheet data for a particulat sheet corresponding to a `gid` or First Sheet
        - If `gid` is not specified or procured from url , First Sheet by index
            is considered & picked for processing .
    [utility]"""
    spreadsheet_metadata = sheet.get(
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
        return title, _fetch_data(sheet, sheet_id, range=_range)
    return "", []

def get_gsheet_data(sheet: object, file_id: str, by: str="all", gid: Optional[str]=None, sheet_name: Optional[str]=None, sheet_position:Optional[int]=None, without_headers: bool=False, custom_tabular_range: Tuple[str, str]=('A1','z999999'), not_found_priority: Optional[List]=[]) -> List[List]:
    """Fetches Google Sheet file data

    This function fetches google sheet file's data and provided
        options over it .

    Args:
        by (str) : sheet level selection options
            - supported values - 'all', 'gid', 'sheet_name'
        gid (str, None) : gid of particular sheet if `:by="gid"`
        sheet_name (str, None) : sheet_name of a particular sheet if `:by="sheet_name"`
        sheet_position (str, None) : sheet_position of a particular sheet if `:by="sheet_position"`

    Kwargs:
        None
    
    Returns:
        list: list of sheet data.
    
    Raises:
        Exception : If sheet does not exist by specified `by` option
    """

    if by == "gid" and gid == None:
        raise Exceptions.GsheetToolsArgumentError(f"get_gsheet_data|with `{by=}` you are cannot pass `{gid=}`.")
    if by == "sheet_name" and sheet_name == None:
        raise Exceptions.GsheetToolsArgumentError(f"get_gsheet_data|with `{by=}` you are cannot pass `{sheet_name=}`.")
    if by == "sheet_position" and sheet_position == None:
        raise Exceptions.GsheetToolsArgumentError(f"get_gsheet_data|with `{by=}` you are cannot pass `{sheet_position=}`.")
    
    # fetch metadata on google sheet
    spreadsheet_metadata = sheet.get(
        spreadsheetId=file_id,
        fields="sheets.properties",  # Request only the properties of each sheet
    ).execute()
    # check if any sheet exists
    if "sheets" not in spreadsheet_metadata:
        return "", []
    
    translation_map: Dict[str, Tuple[str, Any]] = {
        "gid": ("sheetId", gid),
        "sheet_name": ("title", sheet_name),
        "sheet_position": ("index", sheet_position)
    }
    try:
        search_on_key, search_for_value = translation_map[by]
    except KeyError as e:
        raise Exception(f'value not supported yet. {e}')
    
    # search_on_key, search_for_value = (
    #     ("sheetId", str(gid)) if gid is not None else ("index", str(0))
    # )

    sheet_title = '' 
    sheet_data: list = []

    def _find(search_on_key, search_for_value) -> bool:
        found_sheet_properties = None
        for indivisual_sheet in spreadsheet_metadata["sheets"]:
            if str(indivisual_sheet["properties"][search_on_key]) == search_for_value:
                found_sheet_properties = indivisual_sheet["properties"]
                break
        else:
            # properties not found
            # # check for not found values
            first_key = next(iter(not_found_priority))
            _value = not_found_priority.pop(first_key)
            if _value is not None:
                _key,_ = translation_map[first_key]
                try:
                    _find(_key, _value)
                except KeyError as e:
                    raise Exception(f'value not supported yet. {e}')
            # # not found values also fail
            return sheet_title, sheet_data
        # properties found
        sheet_title = found_sheet_properties.get("title")
        _range = f"{sheet_title}"
        if without_headers:
            _range = _range + "!" + "A2:z999999"
        return _fetch_data(sheet, file_id, range=_range)
    
    sheet_title, sheet_data = _find(search_on_key, search_for_value)
    return sheet_title, sheet_data
    
    

def check_sheet_origin(
    google_drive_service: object, file_id: str
) -> Tuple[str, NamedTuple]:
    file_metadata = (
        google_drive_service.files()
        .get(fileId=file_id, fields="mimeType,originalFilename")
        .execute()
    )

    mime_type = file_metadata.get("mimeType")
    original_filename = file_metadata.get(
        "originalFilename"
    )  # May not always be present or reliable for conversion history
    origin_details: NamedTuple = namedtuple(
        "origin_details",
        field_names=(
            "is_parsable",
            "mimetype",
            "original_extension",
            "original_filename",
        ),
        defaults=[None],
    )

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
    return origin, origin_details(
        is_parsable=is_parsable,
        mimetype=mime_type,
        original_extension=original_extension,
        original_filename=original_filename,
    )


def is_valid_google_url(url: str) -> bool:
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
    """Prepare dataframe from spreadsheet data"""

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


def _private()-> None: ...

"""
TODO:

apply multipledispatch on the following :

find_by: str
get_gsheet_data(
    sheet, 
    file_id, 
    find_by="gid", 
    gid="0",
    without_headers: bool=False, 
    custom_tabular_range: str=""
    not_found_priority = {
        "sheet_name": "ankit",
        "sheet_position": "Last"
    }
)

find_by: dict
get_gsheet_data(
    sheet, 
    file_id, 
    find_by={
        "gid": 0,
        "sheet_name": "ankit",
        "sheet_position": "Last",
    },
    without_headers: bool=False, 
    custom_tabular_range: str=""
)

find_by: expression_obj
get_gsheet_data(
    sheet, 
    file_id, 
    find_by="gid:0 & sheet_name:ankit | sheet_position:>6"
    without_headers: bool=False, 
    custom_tabular_range: str=""
)

find_by: tuple
get_gsheet_data(
    sheet, 
    file_id, 
    find_by=("gid",("sheet_name", "sheet_position")) 
    gid="0",
    sheet_name="ankit",
    sheet_position="Last",
    without_headers: bool=False, 
    custom_tabular_range: str=""
)

find_by: callable
get_gsheet_data(
    sheet, 
    file_id, 
    find_by=lambda properties: properties["gid"]==0 and properties["index"] > 3
    gid="0",
    sheet_name="ankit",
    sheet_position="Last",
    without_headers: bool=False, 
    custom_tabular_range: str=""
)

- in expression type , you'll need to be supporting for multiple sheet also.
- give option for "allow_multiple" and "single_result_fetch_for"
"""
