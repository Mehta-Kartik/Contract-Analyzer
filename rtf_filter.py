import pandas as pd

df1=pd.read_csv(r"D:\\ProjectAarya\\Contract Analyzer\\data.csv",index_col=False)
print(df1.head())

docx_only=df1[df1['source_url'].str.endswith(".rtf",na=False)]
docx_only.to_csv("rtf_only.csv",index=False)