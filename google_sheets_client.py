"""
Google Sheets Client - Integration with Google Sheets API
Allows pulling prescriber and patient data from Google Sheets
"""

import gspread
from google.oauth2.service_account import Credentials
from typing import List, Dict, Optional
import pandas as pd
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class GoogleSheetsClient:
    """
    Client for integrating with Google Sheets.
    Supports pulling prescriber and patient data from sheets.
    """
    
    def __init__(self, credentials_path: Optional[str] = None):
        """
        Initialize Google Sheets client.
        
        Args:
            credentials_path: Path to service account JSON file
        """
        self.client = None
        self.credentials_path = credentials_path or os.getenv('GOOGLE_SHEETS_CREDENTIALS_PATH')
        self.spreadsheet = None
        self.initialize()
    
    def initialize(self):
        """Initialize connection to Google Sheets"""
        try:
            if not self.credentials_path:
                print("⚠️ Google Sheets credentials not configured")
                return False
            
            # Authenticate
            scope = [
                'https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
            
            credentials = Credentials.from_service_account_file(
                self.credentials_path,
                scopes=scope
            )
            
            self.client = gspread.authorize(credentials)
            print("✅ Google Sheets client initialized")
            return True
        
        except Exception as e:
            print(f"❌ Error initializing Google Sheets: {e}")
            return False
    
    def open_spreadsheet(self, spreadsheet_name: str):
        """
        Open a spreadsheet by name.
        
        Args:
            spreadsheet_name: Name of the spreadsheet
        """
        try:
            if not self.client:
                raise Exception("Client not initialized")
            
            self.spreadsheet = self.client.open(spreadsheet_name)
            print(f"✅ Opened spreadsheet: {spreadsheet_name}")
            return True
        
        except Exception as e:
            print(f"❌ Error opening spreadsheet: {e}")
            return False
    
    def get_worksheet(self, worksheet_name: str):
        """
        Get a specific worksheet.
        
        Args:
            worksheet_name: Name of the worksheet
        """
        try:
            if not self.spreadsheet:
                raise Exception("No spreadsheet opened")
            
            worksheet = self.spreadsheet.worksheet(worksheet_name)
            return worksheet
        
        except Exception as e:
            print(f"❌ Error getting worksheet: {e}")
            return None
    
    def get_all_records(self, worksheet_name: str) -> List[Dict]:
        """
        Get all records from a worksheet as list of dictionaries.
        
        Args:
            worksheet_name: Name of the worksheet
        
        Returns:
            List of dictionaries with row data
        """
        try:
            worksheet = self.get_worksheet(worksheet_name)
            if not worksheet:
                return []
            
            records = worksheet.get_all_records()
            print(f"✅ Retrieved {len(records)} records from {worksheet_name}")
            return records
        
        except Exception as e:
            print(f"❌ Error getting records: {e}")
            return []
    
    def get_as_dataframe(self, worksheet_name: str) -> Optional[pd.DataFrame]:
        """
        Get worksheet data as pandas DataFrame.
        
        Args:
            worksheet_name: Name of the worksheet
        
        Returns:
            DataFrame or None if error
        """
        try:
            worksheet = self.get_worksheet(worksheet_name)
            if not worksheet:
                return None
            
            records = worksheet.get_all_records()
            df = pd.DataFrame(records)
            print(f"✅ Converted {worksheet_name} to DataFrame")
            return df
        
        except Exception as e:
            print(f"❌ Error converting to DataFrame: {e}")
            return None
    
    def append_row(self, worksheet_name: str, values: List) -> bool:
        """
        Append a row to a worksheet.
        
        Args:
            worksheet_name: Name of the worksheet
            values: List of values to append
        """
        try:
            worksheet = self.get_worksheet(worksheet_name)
            if not worksheet:
                return False
            
            worksheet.append_row(values)
            print(f"✅ Appended row to {worksheet_name}")
            return True
        
        except Exception as e:
            print(f"❌ Error appending row: {e}")
            return False
    
    def update_cell(
        self,
        worksheet_name: str,
        row: int,
        col: int,
        value: str
    ) -> bool:
        """
        Update a specific cell.
        
        Args:
            worksheet_name: Name of the worksheet
            row: Row number (1-indexed)
            col: Column number (1-indexed)
            value: New value
        """
        try:
            worksheet = self.get_worksheet(worksheet_name)
            if not worksheet:
                return False
            
            worksheet.update_cell(row, col, value)
            print(f"✅ Updated cell [{row},{col}] in {worksheet_name}")
            return True
        
        except Exception as e:
            print(f"❌ Error updating cell: {e}")
            return False
    
    def get_prescribers(self) -> List[Dict]:
        """Get prescriber data from Google Sheets"""
        return self.get_all_records('Prescribers')
    
    def get_patients(self) -> List[Dict]:
        """Get patient data from Google Sheets"""
        return self.get_all_records('Patients')
    
    def log_prescription_decision(
        self,
        prescriber_id: str,
        patient_id: str,
        drug: str,
        dose: float,
        approved: bool,
        reason: str
    ) -> bool:
        """
        Log prescription decision to audit sheet.
        
        Args:
            prescriber_id: ID of prescriber
            patient_id: ID of patient
            drug: Drug name
            dose: Dosage in mg
            approved: Whether approved or denied
            reason: Reason for decision
        """
        try:
            from datetime import datetime
            
            timestamp = datetime.now().isoformat()
            status = "APPROVED" if approved else "DENIED"
            
            row = [timestamp, prescriber_id, patient_id, drug, dose, status, reason]
            return self.append_row('Audit Log', row)
        
        except Exception as e:
            print(f"❌ Error logging decision: {e}")
            return False


# ============== Utility Functions ==============

def create_google_sheets_client(credentials_path: Optional[str] = None) -> GoogleSheetsClient:
    """
    Create and return a Google Sheets client.
    
    Args:
        credentials_path: Path to service account credentials JSON
    
    Returns:
        GoogleSheetsClient instance
    """
    return GoogleSheetsClient(credentials_path)


def sync_prescribers_from_sheets() -> Optional[pd.DataFrame]:
    """
    Sync prescriber data from Google Sheets to local DataFrame.
    
    Returns:
        DataFrame with prescriber data or None
    """
    try:
        client = GoogleSheetsClient()
        if not client.client:
            return None
        
        return client.get_as_dataframe('Prescribers')
    except Exception as e:
        print(f"❌ Error syncing prescribers: {e}")
        return None


def sync_patients_from_sheets() -> Optional[pd.DataFrame]:
    """
    Sync patient data from Google Sheets to local DataFrame.
    
    Returns:
        DataFrame with patient data or None
    """
    try:
        client = GoogleSheetsClient()
        if not client.client:
            return None
        
        return client.get_as_dataframe('Patients')
    except Exception as e:
        print(f"❌ Error syncing patients: {e}")
        return None


if __name__ == "__main__":
    # Example usage
    print("Google Sheets Integration Example")
    print("=" * 50)
    
    # Create client
    client = GoogleSheetsClient()
    
    if client.client:
        # Open spreadsheet
        client.open_spreadsheet("Medical Prescription Firewall")
        
        # Get prescriber data
        prescribers = client.get_prescribers()
        print(f"\n📋 Prescribers: {len(prescribers)} records")
        
        # Get patient data
        patients = client.get_patients()
        print(f"👥 Patients: {len(patients)} records")
    else:
        print("⚠️ Google Sheets client not available")
        print("Set GOOGLE_SHEETS_CREDENTIALS_PATH in .env file")
