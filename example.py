import os
from typing import List
from appstoreserverlibrary.api_client import AppStoreServerAPIClient
from appstoreserverlibrary.models.Environment import Environment
from appstoreserverlibrary.signed_data_verifier import SignedDataVerifier
from appstoreserverlibrary.models.HistoryResponse import HistoryResponse
from appstoreserverlibrary.models.TransactionHistoryRequest import (
    TransactionHistoryRequest,
    ProductType,
    Order,
)
from appstoreserverlibrary.models.AppTransaction import AppTransaction

# Configuration
# Replace these with your actual values from App Store Connect
KEY_ID = "YOUR_KEY_ID"
ISSUER_ID = "YOUR_ISSUER_ID"
BUNDLE_ID = "YOUR_BUNDLE_ID"
APP_APPLE_ID = 0000000000  # Replace with your actual App Apple ID
ENVIRONMENT = Environment.PRODUCTION  # Use Environment.SANDBOX for testing
PRIVATE_KEY_PATH = 'path/to/your/private_key.p8'
CERT_PATHS = [
    "./certs/AppleComputerRootCertificate.cer",
    "./certs/AppleIncRootCertificate.cer",
    "./certs/AppleRootCA-G2.cer",
    "./certs/AppleRootCA-G3.cer",
]

def load_certificates(file_paths: List[str]) -> List[bytes]:
    """
    Load Apple Root Certificates from the specified file paths.
    
    :param file_paths: List of paths to certificate files
    :return: List of certificate contents as bytes
    """
    print("Loading Apple Root Certificates ...")
    certificates = []
    for file_path in file_paths:
        with open(file_path, "rb") as cert_file:
            certificates.append(cert_file.read())
    return certificates

def create_signed_data_verifier(root_certificates: List[bytes]) -> SignedDataVerifier:
    """
    Create a SignedDataVerifier instance with the provided root certificates.
    
    :param root_certificates: List of root certificate contents
    :return: SignedDataVerifier instance
    """
    return SignedDataVerifier(
        root_certificates=root_certificates,
        enable_online_checks=True,
        environment=ENVIRONMENT,
        bundle_id=BUNDLE_ID,
        app_apple_id=APP_APPLE_ID,
    )

def create_app_store_client(private_key: str) -> AppStoreServerAPIClient:
    """
    Create an AppStoreServerAPIClient instance with the provided private key.
    
    :param private_key: Contents of the private key file
    :return: AppStoreServerAPIClient instance
    """
    return AppStoreServerAPIClient(
        key_id=KEY_ID,
        issuer_id=ISSUER_ID,
        bundle_id=BUNDLE_ID,
        signing_key=private_key.encode("utf-8"),
        environment=ENVIRONMENT
    )

def get_transaction_info(transaction_id: str, client: AppStoreServerAPIClient, verifier: SignedDataVerifier) -> bool:
    """
    Get transaction info for the provided transaction ID.
    
    :param transaction_id: The transaction ID to fetch info for
    :param client: AppStoreServerAPIClient instance
    :param verifier: SignedDataVerifier instance
    :return: True if the transaction info is valid, False otherwise
    """ 
    
    try:
        response = client.get_transaction_info(transaction_id)    
    except Exception as e:
        print(f"Error fetching IOS transaction info: {str(e)}")        
    
    verified_transaction = None
    if response and hasattr(response, 'signedTransactionInfo') and response.signedTransactionInfo:
        try:
            verified_transaction = verifier.verify_and_decode_signed_transaction(response.signedTransactionInfo)                
            print(verified_transaction)
        except Exception as e:
            print(f"Error verifying iOS transaction: {str(e)}")
    else:
        print("No transaction info found")
    
    #Check app bundle in verified_transaction
    if verified_transaction and hasattr(verified_transaction, 'bundleId') and verified_transaction.bundleId == BUNDLE_ID:
        print("App bundle is valid")
    else:
        print("App bundle is invalid")

def validate_app_store_purchase(transaction_id: str, client: AppStoreServerAPIClient, verifier: SignedDataVerifier) -> bool:
    """
    Validate an App Store purchase using the provided transaction ID.
    
    :param transaction_id: The transaction ID to validate
    :param client: AppStoreServerAPIClient instance
    :param verifier: SignedDataVerifier instance
    :return: True if the transaction is valid, False otherwise
    """
    request = TransactionHistoryRequest(
        sort=Order.ASCENDING,
        revoked=False,
        productTypes=[ProductType.CONSUMABLE]
    )

    transactions: List[AppTransaction] = []
    revision = None

    while True:
        try:
            response: HistoryResponse = client.get_transaction_history(transaction_id, revision, request)
        except Exception as e:
            print(f"Error fetching IOS transaction history: {str(e)}")
            return False

        if response and hasattr(response, 'signedTransactions') and response.signedTransactions:
            for signed_transaction in response.signedTransactions:
                try:
                    verified_transaction = verifier.verify_and_decode_signed_transaction(signed_transaction)
                    transactions.append(verified_transaction)
                except Exception as e:
                    print(f"Error verifying iOS transaction: {str(e)}")
                    return False

        if not response or not response.hasMore:
            break
        
        revision = response.revision       

    for transaction in transactions:
        if transaction.transactionId == transaction_id:
            print(f"iOS Transaction validated: {transaction}")

            #Check app bundle in verified_transaction
            if verified_transaction and hasattr(verified_transaction, 'bundleId') and verified_transaction.bundleId == BUNDLE_ID:
                print("App bundle is valid")
                return True
            else:
                print("App bundle is invalid")
                return False

    return False

def main():
    # Load certificates and create verifier
    root_certificates = load_certificates(CERT_PATHS)
    verifier = create_signed_data_verifier(root_certificates)

    # Load private key and create client
    with open(PRIVATE_KEY_PATH, 'r') as key_file:
        private_key = key_file.read()
    client = create_app_store_client(private_key)

    # Example usage
    transaction_id = "YOUR_TRANSACTION_ID"  # Replace with actual transaction ID
    is_valid = validate_app_store_purchase(transaction_id, client, verifier)
    
    if is_valid:
        print("Transaction is valid. Proceed with granting access to content/features.")
    else:
        print("Transaction is invalid. Deny access to content/features.")

if __name__ == "__main__":
    main()