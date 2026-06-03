# Security Policy

## Supported Versions

Security fixes are handled on the current main branch.

## Reporting A Vulnerability

Please report suspected vulnerabilities by opening a private security advisory on GitHub if available, or by contacting the project maintainers directly.

Do not include real API keys, private map data, private CSV files, or other sensitive material in public issues. If a report needs sample inputs, use synthetic or redacted data.

## API Keys

Fixopleth expects users to provide their own OpenRouter API key in the interface. The application should not commit, log, or persist API keys. Keep local secrets in `.env`, which is ignored by git.

## Uploaded Data

Maps and optional CSV files are processed for analysis and may be sent to OpenRouter. Users should not upload confidential or sensitive data unless they have reviewed the relevant provider policies and have permission to process that data.
