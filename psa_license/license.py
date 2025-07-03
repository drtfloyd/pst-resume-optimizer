
import os
import streamlit as st

def verify_license_key(key: str) -> bool:
    """
    Checks if the provided license key is present in the list of valid keys
    stored in Streamlit secrets.
    """
    try:
        # Expects st.secrets["psa"]["valid_keys"] to be a list, e.g., ["PSA-FREE-123", "PSA-PRO-456"]
        valid_keys = st.secrets["psa"]["valid_keys"]
        return key.strip() in valid_keys
    except KeyError:
        # Specifically catch KeyError if 'psa' or 'valid_keys' not found in secrets
        st.error("License validation failed: Secrets not configured. Expected '[psa] valid_keys = [...]'")
        return False
    except Exception as e:
        # Catch any other unexpected errors during secret access
        st.error(f"License validation failed: An unexpected error occurred: {e}")
        return False

def get_user_mode(key: str) -> str:
    """
    Determines the user's license tier ("enterprise", "pro", "freemium", "invalid")
    based on the license key and its prefix.
    """
    # First, verify if the key is generally valid (exists in our list of known keys)
    if verify_license_key(key):
        # Now, determine the specific tier based on prefixes
        # (Assuming prefixes are consistent, e.g., "PSA-ENT-", "PSA-PRO-", "PSA-FREE-")
        normalized_key = key.strip().upper() # Normalize for consistent prefix checking

        if normalized_key.startswith("PSA-ENT-"):
            return "enterprise"
        elif normalized_key.startswith("PSA-PRO-"):
            return "pro"
        elif normalized_key.startswith("PSA-FREE-"): # Explicitly check for FREE keys
            return "freemium"
        else:
            # If valid key but prefix doesn't match known tiers, default to freemium
            # or invalid depending on your policy. For robustness, "freemium" is a safe
            # default if the key is *valid* but unrecognized prefix.
            return "freemium"
    else:
        # If verify_license_key returns False, the key is not valid or not recognized
        return "invalid"

