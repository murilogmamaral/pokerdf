from pokerdf.core.read_and_convert import convert_txt_to_tabular_data
import pandas as pd


def test_convert_txt_to_tabular_data() -> None:
    """Test the convert_txt_to_tabular_data function in a broad way."""
    # Convert txt to pd.DataFrame
    txt_path = "tests/input/HH20250516 T99999 No Limit Hold_em US$ 1,84 + US$ 0,16.txt"
    df_converted = convert_txt_to_tabular_data(txt_path).reset_index(drop=True)
    # Load expected DataFrame
    parquet_path = "tests/output/20250516-T99999.parquet"
    df_expected = pd.read_parquet(parquet_path)
    # Check if the converted DataFrame matches the expected DataFrame
    pd.testing.assert_frame_equal(
        df_converted, df_expected, check_like=True, check_column_type=True
    )
