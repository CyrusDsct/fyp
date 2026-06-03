# Privacy Notice

Fixopleth is designed for user-provided map auditing. Users may upload map images, optional CSV files, and optional context such as target audience and map purpose.

## Data Sent To Model Providers

When analysis is run, the uploaded map image, selected CSV-derived summary information, prompt text, and user-provided context may be sent to OpenRouter for model processing.

## API Keys

Users provide their own OpenRouter API key. The Streamlit app keeps the key in session state for the current analysis flow. The key should not be committed to the repository or included in logs.

## Local Backend Storage

The optional Flask backend can write uploaded files under `uploads/` and can use MongoDB when configured. The default Streamlit Cloud path uses in-memory analysis and does not require MongoDB or persistent upload storage.

## Sensitive Data

Do not upload confidential, regulated, or sensitive map images or datasets unless you have permission to process them and have reviewed the relevant third-party provider policies.
