import pytest
from gsheet_tools.flows import Flow, DataframeFrameFlow, CsvFlow


# def test_flow_is_abstract():
#     """
#     Test that the Flow class is abstract and cannot be instantiated directly.
#     """
#     with pytest.raises(TypeError):
#         Flow()


def test_dataframe_frame_flow_inherits_flow():
    """
    Test that DataframeFrameFlow is a subclass of Flow and can be instantiated.
    """
    flow = DataframeFrameFlow()
    assert isinstance(flow, Flow)
    assert isinstance(flow, DataframeFrameFlow)


def test_csv_flow_inherits_flow():
    """
    Test that CsvFlow is a subclass of Flow and can be instantiated.
    """
    flow = CsvFlow()
    assert isinstance(flow, Flow)
    assert isinstance(flow, CsvFlow)