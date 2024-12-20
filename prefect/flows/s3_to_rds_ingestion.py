"""
S3 to RDS Ingestion Script

This script automates:
1. Listing files in the S3 `/incoming/` folder.
2. Downloading CSV files from S3.
3. Mapping CSV headers to database column names dynamically.
4. Cleaning and validating rows before inserting into the database.
5. Inserting valid records into the AWS RDS `public.transactions` table.
6. Moving processed files to the S3 `/archive/` folder.

Dependencies:
- boto3: AWS SDK for Python.
- psycopg2: PostgreSQL adapter for Python.
- csv: For parsing CSV files.
- logging: For logging progress and errors.

Author: Your Name
Date: 2024-12-18
"""

import boto3
import psycopg2
import csv
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# AWS S3 Client
s3 = boto3.client("s3")

# Database Configuration
DATABASE_CONFIG = {
    "host": os.getenv("POSTGRES_HOST"),
    "dbname": os.getenv("POSTGRES_DB"),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD")
}

# S3 Configuration
BUCKET_NAME = "aqeuduct-etl-uploads"
INCOMING_PREFIX = "incoming/"
ARCHIVE_PREFIX = "archive/"

# Mapping of CSV headers to database columns
HEADER_MAPPING = {
    "Order_ID": "order_id",
    "Order_Date": "order_date",
    "Shipment_ID": "shipment_id",
    "Shipment_Date": "shipment_date",
    "Tax_Calculated_Date (UTC)": "tax_calculated_date",
    "Posted_Date": "posted_date",
    "Marketplace": "marketplace",
    "Merchant_ID": "merchant_id",
    "Fulfillment": "fulfillment",
    "ASIN": "asin",
    "SKU": "sku",
    "Transaction_Type": "transaction_type",
    "Tax_Collection_Model": "tax_collection_model",
    "Tax_Collection_Responsible_Party": "tax_responsible_party",
    "Product_Tax_Code": "product_tax_code",
    "Quantity": "quantity",
    "Currency": "currency",
    "Buyer_Exemption_Code": "buyer_exemption_code",
    "Buyer_Exemption_Domain": "buyer_exemption_domain",
    "Buyer_Exemption_Certificate_Id": "buyer_exemption_certificate_id",
    "Display_Price": "display_price",
    "Display_Price_Tax_Inclusive": "display_price_tax_inclusive",
    "TaxExclusive_Selling_Price": "tax_exclusive_selling_price",
    "Total_Tax": "total_tax",
    "Total_Tax_Collected_By_Amazon": "total_tax_collected_by_platform",
    "Financial_Component": "financial_component",
    "Ship_From_City": "ship_from_city",
    "Ship_From_State": "ship_from_state",
    "Ship_From_Country": "ship_from_country",
    "Ship_From_Postal_Code": "ship_from_postal_code",
    "Ship_From_Tax_Location_Code": "ship_from_tax_location_code",
    "Ship_To_City": "ship_to_city",
    "Ship_To_State": "ship_to_state",
    "Ship_To_Country": "ship_to_country",
    "Ship_To_Postal_Code": "ship_to_postal_code",
    "Ship_To_Location_Code": "ship_to_location_code",
    "Taxed_Location_Code": "taxed_location_code",
    "Tax_Address_Role": "tax_address_role",
    "Jurisdiction_Level": "jurisdiction_level",
    "Jurisdiction_Name": "jurisdiction_name",
    "Display_Promo_Amount": "display_promo_amount",
    "Display_Promo_Tax_Inclusive": "display_promo_tax_inclusive",
    "isPromoApplied": "is_promo_applied",
    "postPromoTaxableBasis": "post_promo_taxable_basis",
    "prePromoTaxableBasis": "pre_promo_taxable_basis",
    "Promo_Amount_Basis": "promo_amount_basis",
    "Promo_ID_Domain": "promo_id_domain",
    "promoAmountTax": "promo_amount_tax",
    "Promotion_Identifier": "promotion_identifier",
    "Promo_Rule_Reason_Code": "promo_rule_reason_code",
    "Promo_Tax_Price_Type": "promo_tax_price_type",
    "Tax_Amount": "tax_amount",
    "Tax_Amount_Collected_By_Amazon": "tax_amount_collected_by_platform",
    "Taxed_Jurisdiction_Tax_Rate": "taxed_jurisdiction_tax_rate",
    "Tax_Category": "tax_category",
    "Tax_Type": "tax_type",
    "Tax_Calculation_Reason_Code": "tax_calculation_reason_code",
    "NonTaxable_Amount": "non_taxable_amount",
    "Taxable_Amount": "taxable_amount",
}


def clean_row(row, expected_columns):
    """
    Cleans a row by converting applicable float strings to integers and handling invalid data.

    Args:
        row (dict): A dictionary representing a CSV row.
        expected_columns (list): List of columns expected in the row.

    Returns:
        dict or None: The cleaned row, or None if the row is invalid.
    """
    try:
        for column in expected_columns:
            if column in row and row[column]:
                # Handle integers stored as floats (e.g., "1.0")
                if column in ["quantity", "total_tax"] and "." in row[column]:
                    row[column] = int(float(row[column]))
                # Handle numeric columns generally
                elif column in ["quantity", "total_tax"] and row[column].isdigit():
                    row[column] = int(row[column])
            else:
                # Replace missing values with None
                row[column] = None
    except ValueError as e:
        logging.warning(f"Skipping row due to invalid data: {row}, Error: {e}")
        return None
    return row


def process_file(s3_key):
    """
    Processes a single CSV file from S3:
    - Downloads the file to a local temporary directory.
    - Maps headers to database columns dynamically.
    - Cleans and inserts rows into the RDS `public.transactions` table.
    - Moves the file to the S3 `/archive/` folder.

    Args:
        s3_key (str): S3 key of the file.

    Raises:
        Exception: If any step in processing fails.
    """
    local_file = f"/tmp/{os.path.basename(s3_key)}"

    try:
        # Step 1: Download file from S3
        logging.info(f"Downloading file: {s3_key}")
        s3.download_file(BUCKET_NAME, s3_key, local_file)

        # Step 2: Process and validate file
        with open(local_file, 'r') as f:
            reader = csv.DictReader(f)
            mapped_header = {csv_col: HEADER_MAPPING[csv_col] for csv_col in reader.fieldnames if csv_col in HEADER_MAPPING}

            if not mapped_header:
                raise ValueError(f"CSV columns do not match expected structure. Found: {reader.fieldnames}")

            insert_query = f"""
                INSERT INTO public.transactions ({', '.join(mapped_header.values())})
                VALUES ({', '.join(['%s'] * len(mapped_header))})
            """

            # Step 3: Insert rows into RDS
            with psycopg2.connect(**DATABASE_CONFIG) as conn:
                with conn.cursor() as cursor:
                    for row in reader:
                        cleaned_row = clean_row(row)
                        if not cleaned_row:
                            continue  # Skip invalid rows
                        row_data = [cleaned_row[csv_col] for csv_col in mapped_header.keys()]
                        cursor.execute(insert_query, row_data)

                conn.commit()
                logging.info(f"Successfully inserted data from file: {s3_key}")

        # Step 4: Move file to /archive/
        archive_key = s3_key.replace(INCOMING_PREFIX, ARCHIVE_PREFIX)
        s3.copy_object(Bucket=BUCKET_NAME, CopySource=f"{BUCKET_NAME}/{s3_key}", Key=archive_key)
        s3.delete_object(Bucket=BUCKET_NAME, Key=s3_key)
        logging.info(f"File processed and moved to archive: {archive_key}")

    except Exception as e:
        logging.error(f"Error processing file {s3_key}: {e}")
        raise
    finally:
        if os.path.exists(local_file):
            os.remove(local_file)  # Clean up the local file


def main():
    """
    Main function to process all files in the S3 /incoming/ folder.
    """
    try:
        logging.info("Listing files in the S3 /incoming/ folder...")
        response = s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix=INCOMING_PREFIX)
        for obj in response.get("Contents", []):
            file_key = obj["Key"]
            if not file_key.endswith("/"):  # Skip folder keys
                try:
                    process_file(file_key)
                except Exception as e:
                    logging.error(f"Failed to process {file_key}: {e}")
    except Exception as e:
        logging.critical(f"Failed to list or process files: {e}")


if __name__ == "__main__":
    main()