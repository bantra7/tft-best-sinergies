# TFT Best Synergies

This project helps you find the best team compositions in Teamfight Tactics (TFT) by analyzing champion synergies. It provides a Streamlit web application to filter champions and discover optimal teams, and a script to download the latest champion and trait data from tftactics.gg.

## Project Structure

```
├── .devcontainer/        # Development container configuration
├── .github/              # GitHub Actions workflows
│   └── workflows/
│       └── pylint.yml    # Pylint workflow for code analysis
├── app/                  # Main application folder
│   ├── data/             # Data files (champions and traits)
│   │   ├── champions-*.csv
│   │   └── traits-*.json
│   ├── calcul.py         # Core logic for team calculations
│   └── main.py           # Streamlit application entry point
├── .dockerignore         # Specifies intentionally untracked files that Docker should ignore
├── .gitignore            # Specifies intentionally untracked files that Git should ignore
├── .pylintrc             # Pylint configuration file
├── Dockerfile            # Dockerfile to build the application image
├── cah-champions.ipynb   # Jupyter notebook (likely for experimentation)
├── download_data.py      # Script to download/update TFT data
├── requirements.txt      # Python dependencies
└── README.md             # This file
```

## Setup

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd <repository_directory>
    ```

2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Running the Application

To launch the Streamlit application, run the following command in your terminal:

```bash
streamlit run app/main.py
```

This will open the application in your web browser. You can then use the sidebar filters to specify:
*   Champion costs
*   Team size
*   Minimum number of unlocked synergies
*   Minimum ratio of unlocked synergies to team size
*   Maximum number of teams to display

Click the "Generate" button to see the suggested teams.

## Downloading/Updating Data

The application uses champion and trait data stored in the `app/data/` directory. To download or update this data, you need to run the `download_data.py` script.

1.  **Install a WebDriver:**
    The script uses Selenium to scrape data from `https://tftactics.gg`. You'll need to have Google Chrome and the corresponding ChromeDriver installed and in your system's PATH.
    *   Download ChromeDriver from [https://chromedriver.chromium.org/downloads](https://chromedriver.chromium.org/downloads). Make sure its version matches your Chrome browser version.

2.  **Run the script:**
    ```bash
    python download_data.py
    ```
    This will fetch the latest data for the current TFT set (as defined in the script, default is Set 13) and save it as `app/data/champions-13.csv` and `app/data/traits-13.json`.

    **Note:** If you want to download data for a different set, you may need to modify the `TFT_SET_NUMBER` variable within the `download_data.py` script. Future improvements will make this configurable.

## Development Best Practices

This project aims to follow Python development best practices, including:
*   Type hinting
*   Docstrings
*   Clear variable and function naming
*   Organized imports
*   Linting with Pylint (see `.pylintrc`)
*   Automated code checks using GitHub Actions (see `.github/workflows/pylint.yml`)

## Contributing

Contributions are welcome! If you have suggestions for improvements or new features, please open an issue or submit a pull request.
```
