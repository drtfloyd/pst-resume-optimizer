import streamlit as st

def verify_license_key(key: str) -> bool:
    """
    Checks if the provided license key is in the list of valid keys
    stored in Streamlit secrets under [psa].
    """
    try:
        valid_keys = st.secrets["psa"]["valid_keys"]
        return key.strip() in valid_keys
    except KeyError:
        st.error("License validation failed: [psa] valid_keys not configured in secrets.toml.")
        return False
    except Exception as e:
        st.error(f"Unexpected error during license validation: {e}")
        return False

def get_user_mode(license_key: str) -> str:
    """
    Returns the license tier (freemium, pro, enterprise) from secrets based on license key.
    Falls back to 'invalid' if not recognized.
    """
    try:
        license_tiers = st.secrets["psa"]["license_tiers"]
        return license_tiers.get(license_key.strip(), "invalid")
    except KeyError:
        st.error("License tiers not found in secrets.toml. Check [psa] license_tiers section.")
        return "invalid"
    except Exception as e:
        st.error(f"Unexpected error while retrieving license tier: {e}")
        return "invalid"
