# MAPEL: A Framework for Part 11 Compliance

**MAPEL (My Attempt at Part ELeven)** is a versatile framework specifically designed to address the FDA’s 21 CFR Part 11 compliance requirements. Independent of application-specific functionality, MAPEL serves as a minimal, reproducible example of Part 11 compliance, focusing entirely on regulatory standards. This unique approach makes MAPEL a modular, "plug-and-play" solution for developers aiming to incorporate compliance into their software systems.

Part 11 compliance governs the use of electronic records and signatures in regulated industries, emphasizing data integrity, security, and traceability. MAPEL’s modular architecture enables independent validation of individual components, streamlining updates, and reducing revalidation costs. By combining compliance with scalability and adaptability, MAPEL is suitable for diverse applications.

------------------------------------------------------------------------

## Features

### Part 11 Compliance

MAPEL includes core functionalities that ensure adherence to 21 CFR Part 11 requirements: - **Comprehensive Audit Trails**: - Tracks all system and user actions. - Facilitates review and accountability for regulatory purposes.

<img src=images/Screenshot%202025-01-05%20125434.png width="800"  />

-   **Secure User Authentication and Access Control**:
    -   Password policies enforce a minimum of eight characters, including letters, digits, and special characters.
    -   Passwords are securely hashed using the PBKDF2-HMAC algorithm and never stored in plain text.
    -   Access is restricted to authorized users, with role-based permissions.
    -   Failed login attempts are logged, and account lockout mechanisms prevent brute-force attacks.
-   **Digital Signatures with Verification**:
    -   Each user has an RSA key pair, derived from their hashed password and securely stored in an encrypted format.
    -   Private keys are decrypted only during signature operations after prompting for the user’s password.
    -   Any data modification invalidates previous signatures, ensuring data integrity.
    -   Public keys are accessible for signature verification.
-   **Efficient Data Storage**:
    -   Data, audit trails, and signature logs are compressed and saved in HDF5 format, ensuring efficient storage and retrieval.

------------------------------------------------------------------------

### Modular Design

MAPEL employs a modular architecture that simplifies compliance management: - Developers can create custom modules for specific tasks. - Each module must include: - `analyze()` for processing data. - `tabulate()` for summarizing results. - Missing functions default to displaying raw images or data. - Numeric `__init__` variables automatically generate dynamic controller windows, enabling users to adjust parameters in real-time.

This modular approach enhances customization and reduces system-wide validation complexity, allowing updates to individual components without affecting overall compliance.

------------------------------------------------------------------------

## Getting Started

### Prerequisites

Ensure you have the following: - Python 3.9+ - PyQt5 5.15.11+ - NumPy - Cryptography - h5py 3.12.1+

### Installation

Clone the repository and install dependencies:

``` bash
git clone https://github.com/username/mapel.git
cd mapel
pip install -r requirements.txt
```

### Running MAPEL

Start the application with:

``` bash
python main.py
```

The GUI provides tools for user authentication, audit trails, and more.

------------------------------------------------------------------------

## How It Works

### System Architecture

<img src=Icons/Mapel%20Workflow.png width="1000"  />

### Login Procedure

-   On first launch, an admin username and password are generated automatically. Credentials are displayed in a pop-up window and logged in the session file. Changing default credentials after the initial login is recommended.

<img src=images/Screenshot%202025-01-01%20135016.png width="500"  />

-   For subsequent logins, users must provide their credentials.

<img src=images/Screenshot%202025-01-05%20110632.png width="200"  />

### User Interface

The UI is minimalistic, modeled after **ImageJ**, featuring a file menu and toolbar. Additional functionalities open in separate windows, allowing multiple tools to run simultaneously.

<img src=images/Screenshot%202025-01-05%20111124.png width="400"  />

#### Toolbar Functions

-   <img src=Icons/new_file.png width="24"  /> **Create File**: Create new .mapel file

-   <img src=Icons/open_file.png width="24"  /> **Open**: Open previously saves .mapel file

-   <img src=Icons/save_file.png width="24"  /> **Save**: Save current .mapel file

-   <img src=Icons/import_file.png width="24"  /> **Import**: Import raw data; currently only accepts image data.

-   <img src=Icons/tabular.png width="24"  /> **View Results**: View table of results.

-   <img src=Icons/imager.png width="24"  /> **View Image**: View Image output.

-   <img src=Icons/run.png width="24"  /> **Run All**: Run current analysis using current setting on all data.

-   <img src=Icons/audit_logo.png width="24"  /> **View Audit Trail**: Audit trails are specific to each .mapel file or login session.

-   <img src=Icons/signature_logo.png width="24"  /> **Sign Data**: Sign results using private keys.

------------------------------------------------------------------------

### Importing Raw Data

The **File Manager** provides a list of imported files and navigation controls for viewing individual images. It can be accessed via **Analyze \> File Manager**.

<img src=images/Screenshot%202025-01-05%20113107.png width="200"  />

------------------------------------------------------------------------

### Running a Module

Custom modules stored in the `Modules` directory must: - Include `analyze()` and `tabulate()` methods. - Define any numeric parameters in `__init__` for dynamic controllers.

Example:

``` python
class NewClass(ImageViewer):
    def __init__(self, image_paths=None, index=0, logger=None, diameter=100):
        self.diameter = diameter
        super().__init__(image_paths=image_paths, index=index, logger=logger)

    def analyze(self, image_path):
        # Perform analysis
        self.masks[image_path] = output_image
        return output_image

    def tabulate(self):
        headers = ["Custom_Output"]
        table_data = []
        return headers, table_data
```

------------------------------------------------------------------------

### Viewing Results

Select **View Results** to see tabular data summarizing analysis output.

------------------------------------------------------------------------

### Saving and Loading Data

Data is stored as compressed `.mapel` files containing raw data, analyzed results, audit logs, and signatures.

------------------------------------------------------------------------

## Use Cases

### Cellpose Particle Segmentation

I integrated [Cellpose](https://github.com/MouseLand/cellpose) into a custom MAPEL module. Leveraging its robust cell segmentation capabilities, I applied its general-purpose algorithms to particle images from the [EMPS](https://github.com/by256/emps) dataset. This demonstrated the adaptability of Cellpose for segmenting diverse particle types, extending its typical use in cellular biology.

<img src=images/Screen%20Recording%202025-01-05%20014816.gif width="500"  />

Output example:

<img src=images/Screenshot%202025-01-05%20174910.png width="800"  />

------------------------------------------------------------------------

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE.md) file for details.

------------------------------------------------------------------------
