import pandas as pd
import streamlit as st
from io import BytesIO

st.title("Excel Data Validation Tool")

# Upload files
part1 = st.file_uploader("Upload File 1 - Smart Brake Part 1", type=['xlsx'])
part2 = st.file_uploader("Upload File 2 - Smart Brake Part 2", type=['xlsx'])
ep_list = st.file_uploader("Upload File 3 - EP List", type=['xlsx'])

if part1 and part2 and ep_list:
    try:
        # Load Excel files
        df1 = pd.read_excel(part1)
        df2 = pd.read_excel(part2)
        df_ep = pd.read_excel(ep_list, skiprows=1)

        # Strip column names
        for df in [df1, df2, df_ep]:
            df.columns = df.columns.str.strip()

        # Rename columns to consistent names
        rename_dict_sb = {
            'Component ID': 'Component_ID',
            'Symbol': 'Symbol',
            'C': 'C'
        }
        df1 = df1.rename(columns=rename_dict_sb)
        df2 = df2.rename(columns=rename_dict_sb)

        rename_dict_ep = {
            'DRAWING NUM.': 'Component_ID',
            'REF.': 'Symbol',
            'AA': 'AA'
        }
        df_ep = df_ep.rename(columns=rename_dict_ep)

        # Combine Smart Brake parts
        combined_sb = pd.concat([df1, df2], ignore_index=True)

        # Map 'C' column: '-' = 1, 'S' = 0
        combined_sb['C_mapped'] = combined_sb['C'].map({'-': 1, 'S': 0})

        # Merge combined Smart Brake with EP list
        merged = pd.merge(
            combined_sb,
            df_ep[['Component_ID', 'Symbol', 'AA']],
            on=['Component_ID', 'Symbol'],
            how='left'
        )

        # Find discrepancies
        discrepancies = []
        for _, row in merged.iterrows():
            if pd.isna(row['AA']):
                discrepancies.append({
                    'Component_ID': row['Component_ID'],
                    'Symbol': row['Symbol'],
                    'Field': 'No Match Found in EP List',
                    'File_C': row['C'],
                    'EP_AA': ''
                })
            elif row['C_mapped'] != row['AA']:
                discrepancies.append({
                    'Component_ID': row['Component_ID'],
                    'Symbol': row['Symbol'],
                    'Field': 'C vs AA',
                    'File_C': row['C'],
                    'EP_AA': row['AA']
                })

        # Display results
        if discrepancies:
            result_df = pd.DataFrame(discrepancies)
            st.subheader("Discrepancies Found")
            st.dataframe(result_df)

            # Download button
            output = BytesIO()
            result_df.to_excel(output, index=False)
            st.download_button(
                label="📥 Download Report",
                data=output.getvalue(),
                file_name="validation_discrepancies.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.success("No discrepancies found!")

    except Exception as e:
        st.error(f"⚠️ Error: {e}")
