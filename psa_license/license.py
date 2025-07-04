import os
import streamlit as st

def verify_license_key(key: str, available_tiers_dict: dict) -> bool:
    """
    Checks if the provided license key is present in the keys of the available_tiers_dict.
    This function no longer directly accesses st.secrets, but takes the loaded tiers as input.
    """
    try:
        # Compare the provided key (case-insensitively) against the keys in the dictionary
        return key.strip().upper() in (k.upper() for k in available_tiers_dict.keys())
    except Exception as e:
        st.error(f"License validation failed (verify_license_key): An unexpected error occurred during key comparison: {e}")
        return False

def get_user_mode(license_key: str):
    """
    Verifies license key against secrets.toml and returns license tier.
    """
    try:
        # FIX 1 (Already discussed): Correctly access the nested secret section
        license_tiers = st.secrets["psa"]["license_tiers"]
    except KeyError as e:
        # Catch specific error if the secrets are not configured as expected
        st.error(f"License validation failed: Section '[psa.license_tiers]' not found in secrets.toml. Please ensure it is configured correctly. Details: {e}")
        return "invalid"
    except Exception as e:
        # Catch any other unexpected errors during secret access
        st.error(f"License validation failed: An unexpected error occurred during secret access: {e}")
        return "invalid"

    # FIX 2: Removed the premature 'return' statement from here
    # The original problematic line: return license_tiers.get(license_key.strip(), None)

    # First, verify if the key is generally valid (exists in our list of known keys)
    # Pass the loaded license_tiers dictionary to verify_license_key
    # Also, ensure 'license_key' (the function argument) is passed, not a generic 'key'
    if not verify_license_key(license_key, license_tiers):
        return "invalid" # If verify_license_key returns False, the key is not valid or not recognized

    # Now, determine the specific tier based on prefixes
    # (Assuming prefixes are consistent, e.g., "PSA-ENT-", "PSA-PRO-", "PSA-FREE-")
    # Ensure 'license_key' is used here, not a generic 'key'
    normalized_key = license_key.strip().upper() # Normalize for consistent prefix checking

    if normalized_key.startswith("PSA-ENT-"):
        return "enterprise"
    elif normalized_key.startswith("PSA-PRO-"):
        return "pro"
    elif normalized_key.startswith("PSA-FREE-"): # Explicitly check for FREE keys
        return "freemium"
    else:
        # If the key is valid (passed verify_license_key) but its prefix
        # doesn't match predefined tiers, or if the exact key isn't in the dict,
        # return 'freemium' as a fallback.
        # This part assumes license_tiers.get(normalized_key) would return None if not matched
        tier_from_dict = license_tiers.get(normalized_key)
        if tier_from_dict:
            return tier_from_dict # Return exact tier if found in dict
        else:
            st.warning(f"License key '{license_key}' recognized but specific tier mapping not found by prefix. Defaulting to freemium.")
            return "freemium"
