import json
import os


# ----------------------------
# Utility: Load JSON file
# ----------------------------
def load_json(path):
    """
    Loads a JSON file and returns a Python dict.
    Provides friendly error messages if something goes wrong.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"JSON file not found: {path}")

    try:
        with open(path, "r") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Error parsing JSON in {path}: {e}")


# ----------------------------
# Load astro types
# ----------------------------
def load_astro_types(data_dir):
    path = os.path.join(data_dir, "astro_types.json")
    return load_json(path)
    """
    Loads astro_types.json and returns:
        {
          "Arid": {
             "metal": 2,
             "gas": 2,
             ...
          },
          ...
        }
    """
    path = os.path.join(data_dir, "astro_types.json")
    return load_json(path)


# ----------------------------
# Load structure definitions
# ----------------------------
def load_structures(data_dir):
    path = os.path.join(data_dir, "structures.json")
    return load_json(path)
    """
    Loads structures.json and returns a dict:
        {
           "Urban Structures": {
               "area": -1,
               "energy": 0,
               "population": 1,
               ...
           },
           ...
        }
    """
    path = os.path.join(data_dir, "structures.json")
    return load_json(path)


# ----------------------------
# Full loader (recommended)
# ----------------------------
def load_all_data(data_dir=None):
    # Always resolve paths from the location of THIS file
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    if data_dir is None:
        data_dir = os.path.join(base_dir, "data")

    astro_types = load_astro_types(data_dir)
    structures = load_structures(data_dir)

    return {
        "astro_types": astro_types,
        "structures": structures
    }

# ----------------------------
# Manual test
# ----------------------------
if __name__ == "__main__":
    data = load_all_data()
    print("Loaded astro types:", list(data["astro_types"].keys()))
    print("Loaded structures:", len(data["structures"]))