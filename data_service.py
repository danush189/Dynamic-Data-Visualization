import boto3
import pandas as pd
from io import BytesIO
import zipfile
from scipy.io import loadmat
import h5py
import numpy as np

class DataService:
    def __init__(self, aws_access_key_id, aws_secret_access_key):
        self.s3 = boto3.client(
            's3',
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key
        )
        self.data = None
    
    def load_dataset_from_s3(self, bucket_name, prefix):
        try:
            response = self.s3.get_object(Bucket=bucket_name, Key=prefix)

            # Determine the file type based on the prefix (file name)
            if prefix.endswith('.csv'):
                # Load single CSV file
                data = pd.read_csv(BytesIO(response['Body'].read()))
                print("Single CSV file loaded successfully.")
                self.data = {"Single CSV File": data}
                return self.data

            elif prefix.endswith('.xlsx'):
                # Load single Excel file
                data = pd.read_excel(BytesIO(response['Body'].read()))
                print("Single Excel file loaded successfully.")
                self.data = {"Single Excel File": data}
                return self.data

            elif prefix.endswith('.zip'):
                # Handle zip file containing multiple files
                dataframes = {}
                with zipfile.ZipFile(BytesIO(response['Body'].read())) as z:
                    file_list = z.namelist()
                    print("Files in the zip:", file_list)

                    # Loop through all files in the zip
                    for file_name in file_list:
                        if file_name.endswith('.csv'):
                            print(f"Loading CSV file: {file_name}")
                            with z.open(file_name) as f:
                                dataframes[file_name] = pd.read_csv(f)
                                print(f"CSV file '{file_name}' loaded.")

                        elif file_name.endswith('.xlsx'):
                            print(f"Loading Excel file: {file_name}")
                            with z.open(file_name) as f:
                                dataframes[file_name] = pd.read_excel(f)
                                print(f"Excel file '{file_name}' loaded.")

                print("All files in the zip loaded successfully.")
                self.data = dataframes
                return self.data

            else:
                print("Unsupported file format.")
                return None

        except Exception as e:
            print(f"Error loading dataset: {e}")
            return None
    
    def get_dataset(self):
        """Return the loaded dataset"""
        return self.data
    
    def get_dataframe(self):
        """Return the first dataframe in the dataset"""
        if self.data:
            return list(self.data.values())[0] if isinstance(self.data, dict) else self.data
        return None

    def classify_columns(self):
        """Classify columns as categorical or numerical"""
        df = self.get_dataframe()
        if df is None:
            return [], []
            
        categorical_cols = df.select_dtypes(include=['object', 'datetime']).columns.tolist()
        
        # Exclude ID-like numerical columns
        numerical_cols = [
            col for col in df.select_dtypes(include=['number']).columns
            if not any(keyword in col.lower() for keyword in ["id", "index"])
        ]
        
        return categorical_cols, numerical_cols