import logging
import re
from datetime import datetime, timezone
import copy


def camel_to_snake(name: str) -> str:
    # Insert underscore before uppercase letters and convert to lowercase
    name = re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()
    # Replace non-alphanumeric characters with underscore
    name = re.sub(r"[^a-z0-9_]", "_", name)
    # Replace multiple consecutive underscores with a single one
    name = re.sub(r"_{2,}", "_", name)
    # Remove trailing underscore
    name = name.rstrip("_")
    return name


def standardize_date(date_str):
    """
    Convert any ISO 8601 date string to a datetime object with consistent timezone.
    Handles various precision levels and timezone indicators.
    All returned datetime objects will have seconds precision without microseconds
    and will include UTC timezone information.

    Args:
        date_str: An ISO 8601 formatted date string

    Returns:
        datetime: A timezone-aware datetime object in UTC
    """
    if not isinstance(date_str, str):
        return date_str

    if not re.match(r"\d{4}-\d{2}-\d{2}", date_str):
        return date_str

    original = date_str  # Keep original date for logging

    try:
        # First, determine if there's timezone information in the string
        has_timezone = (
            "Z" in date_str
            or "+" in date_str
            or (date_str.count("-") > 2 and "T" in date_str)
        )

        # Handle date-only format (YYYY-MM-DD)
        if re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
            # Create datetime with UTC timezone
            base_dt = datetime.strptime(date_str, "%Y-%m-%d")
            result = base_dt.replace(microsecond=0, tzinfo=timezone.utc)
            logging.info(f"Date parsed: '{original}' -> '{result}'")
            return result

        # Handle format with Z timezone (YYYY-MM-DDTHH:MM:SSZ)
        if "Z" in date_str:
            # Remove Z and any microseconds
            clean_str = date_str.replace("Z", "")
            if "." in clean_str:
                clean_str = clean_str.split(".")[0]

            # Parse and add UTC timezone
            base_dt = datetime.strptime(clean_str, "%Y-%m-%dT%H:%M:%S")
            result = base_dt.replace(tzinfo=timezone.utc)
            logging.info(f"Date parsed: '{original}' -> '{result}'")
            return result

        # For dates with timezone information, use fromisoformat
        if has_timezone:
            # Replace 'Z' with +00:00 for fromisoformat compatibility
            iso_str = date_str.replace("Z", "+00:00")

            # Parse with timezone and remove microseconds
            dt = datetime.fromisoformat(iso_str)
            result = dt.replace(microsecond=0)
            logging.info(f"Date parsed: '{original}' -> '{result}'")
            return result

        # For dates without timezone (but with time), add UTC timezone
        if "T" in date_str:
            # Strip microseconds if present
            if "." in date_str:
                clean_str = date_str.split(".")[0]
            else:
                clean_str = date_str

            # Parse and add UTC timezone
            base_dt = datetime.strptime(clean_str, "%Y-%m-%dT%H:%M:%S")
            result = base_dt.replace(tzinfo=timezone.utc)
            logging.info(f"Date parsed: '{original}' -> '{result}'")
            return result

        # If we reach here, try a flexible approach as last resort
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        result = dt.replace(microsecond=0)
        logging.info(f"Date parsed: '{original}' -> '{result}'")
        return result

    except Exception as e:
        logging.warning(f"Error parsing date '{date_str}': {str(e)}")
        return date_str


def format_mac_address(value):
    """
    Format MAC address to the standard format with colons (xx:xx:xx:xx:xx:xx).
    Handles various input formats like 0a-9a-0e-ba-3f-d9 or 0a9a0eba3fd9.
    """
    if not isinstance(value, str):
        return value

    # Remove any separators and check if we have 12 hex characters
    mac_clean = re.sub(r"[^0-9a-fA-F]", "", value)
    if len(mac_clean) != 12:
        return value

    formatted = ":".join(mac_clean[i : i + 2] for i in range(0, 12, 2))

    if formatted != value:
        logging.info(f"MAC address reformatted: '{value}' -> '{formatted}'")

    return formatted.lower()


def process_value(value, path=""):
    """Process a value, handling nested structures and converting dates."""
    if isinstance(value, dict):
        # Handle MongoDB date format
        if "$date" in value and len(value) == 1:
            date_val = value["$date"]
            if isinstance(date_val, str):
                result = standardize_date(date_val)
                logging.debug(f"MongoDB date at {path}: {date_val} -> {result}")
                return result
            elif isinstance(date_val, (int, float)):
                # Convert timestamp (milliseconds) to ISO date
                dt = datetime.fromtimestamp(date_val / 1000)
                iso_date = dt.isoformat()
                result = standardize_date(iso_date)
                logging.debug(f"MongoDB timestamp at {path}: {date_val} -> {result}")
                return result
            return date_val

        elif "$numberLong" in value and len(value) == 1:
            try:
                result = int(value["$numberLong"])
                logging.debug(
                    f"MongoDB numberLong at {path}: {value['$numberLong']} -> {result}"
                )
                return result
            except (ValueError, TypeError):
                logging.debug(
                    f"Could not convert numberLong at {path}: {value['$numberLong']}"
                )
                return value["$numberLong"]

        logging.debug(f"Processing dictionary at {path}")
        processed_dict = {}

        for k, v in value.items():
            snake_k = camel_to_snake(k)

            processed_v = process_value(v, f"{path}.{k}" if path else k)

            # Special handling for MAC address fields
            if any(
                mac_field in snake_k.lower()
                for mac_field in ["mac_address", "macaddress"]
            ):
                processed_v = format_mac_address(processed_v)

            processed_dict[snake_k] = processed_v

        return processed_dict

    elif isinstance(value, list):
        logging.debug(f"Processing list at {path} with {len(value)} items")
        processed_list = []

        for i, item in enumerate(value):
            processed_item = process_value(item, f"{path}[{i}]")

            # If list item is a string that looks like a MAC address
            if isinstance(processed_item, str) and (
                "mac" in path.lower() or "address" in path.lower()
            ):
                processed_item = format_mac_address(processed_item)

            processed_list.append(processed_item)

        return processed_list

    elif isinstance(value, str):
        # Check if this is a date string
        if re.match(r"\d{4}-\d{2}-\d{2}T", value):
            result = standardize_date(value)
            if value != result:
                logging.debug(f"Date string at {path}: '{value}' -> '{result}'")
            return result

        # Check if this is a MAC address based on the field name
        if any(mac_field in path.lower() for mac_field in ["mac", "address"]):
            result = format_mac_address(value)
            return result

        return value

    return value


def find_duplicates(obj1, obj2, path=""):
    """
    Find duplicate values between two objects.
    Returns a list of paths and values that are duplicates.
    """
    duplicates = []

    if isinstance(obj1, dict) and isinstance(obj2, dict):
        for key2, value2 in obj2.items():
            current_path = f"{path}.{key2}" if path else key2

            # If simple value and matches something in obj1, it's a duplicate
            if isinstance(value2, (str, int, float, bool)) or value2 is None:
                for key1, value1 in obj1.items():
                    if value2 == value1 and key1 != key2:
                        duplicates.append(
                            (
                                current_path,
                                str(value2),
                                f"{path}.{key1}" if path else key1,
                            )
                        )
                        logging.info(
                            f"Duplicate found: '{current_path}' and '{path}.{key1 if path else key1}' both "
                            f"have value '{str(value2)}'"
                        )

            # Recursively check nested objects and arrays
            elif isinstance(value2, dict) or isinstance(value2, list):
                for key1, value1 in obj1.items():
                    if isinstance(value1, type(value2)):
                        sub_duplicates = find_duplicates(value1, value2, current_path)
                        duplicates.extend(sub_duplicates)

    elif isinstance(obj1, list) and isinstance(obj2, list):
        for i, item2 in enumerate(obj2):
            current_path = f"{path}[{i}]"

            if isinstance(item2, (str, int, float, bool)) or item2 is None:
                for j, item1 in enumerate(obj1):
                    if item2 == item1 and i != j:
                        duplicates.append((current_path, str(item2), f"{path}[{j}]"))
                        logging.info(
                            f"Duplicate found in list: '{current_path}' and '{path}[{j}]' "
                            f"both have value '{str(item2)}'"
                        )

            elif isinstance(item2, (dict, list)):
                for j, item1 in enumerate(obj1):
                    if isinstance(item1, type(item2)):
                        sub_duplicates = find_duplicates(item1, item2, current_path)
                        duplicates.extend(sub_duplicates)

    return duplicates


def merge_data(qualys_data, crowdstrike_data):
    """
    Merge the two datasets, with standardized date formats and no duplicates.
    """
    logging.info("Starting data merge process")

    if isinstance(qualys_data, list) and qualys_data:
        logging.info(f"Processing Qualys data (list with {len(qualys_data)} items)")
        processed_qualys = process_value(qualys_data[0], "qualys")
    else:
        logging.info("Processing Qualys data (dictionary)")
        processed_qualys = process_value(qualys_data, "qualys")

    if isinstance(crowdstrike_data, list) and crowdstrike_data:
        logging.info(
            f"Processing CrowdStrike data (list with {len(crowdstrike_data)} items)"
        )
        processed_crowdstrike = process_value(crowdstrike_data[0], "crowdstrike")
    else:
        logging.info("Processing CrowdStrike data (dictionary)")
        processed_crowdstrike = process_value(crowdstrike_data, "crowdstrike")

    logging.info("Finding duplicates between datasets")
    duplicates = find_duplicates(processed_qualys, processed_crowdstrike)
    duplicate_paths = {path: orig_path for path, _, orig_path in duplicates}

    logging.info(f"Found {len(duplicate_paths)} duplicate paths")

    merged = copy.deepcopy(processed_qualys)

    def recursive_merge(target, source, base_path=""):
        """Recursively merge source into target, avoiding duplicates."""
        if not isinstance(source, dict):
            return

        for key, value in source.items():
            current_path = f"{base_path}.{key}" if base_path else key

            if current_path in duplicate_paths:
                logging.info(
                    f"Skipping duplicate value at '{current_path}', same as '{duplicate_paths[current_path]}'"
                )
                continue

            if key not in target:
                logging.info(f"Adding new key-value: '{current_path}' = {value}")
                target[key] = value
                continue

            if isinstance(value, dict) and isinstance(target[key], dict):
                logging.debug(f"Recursively merging dictionaries at '{current_path}'")
                recursive_merge(target[key], value, current_path)
                continue

            logging.debug(f"Keeping existing value at '{current_path}': {target[key]}")

    logging.info("Merging datasets")
    recursive_merge(merged, processed_crowdstrike)

    logging.info("Merge completed successfully")
    return merged
