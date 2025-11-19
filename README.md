# gcp-profiles

A simple command-line interface (CLI) tool for managing and switching between multiple **Google Cloud Platform (GCP)** authentication profiles via a central vault. `gcp-profiles` manages google cloud's application default credentials and gcloud credentials and keeps them in sync.

---

## Features

- **Create** new GCP authentication profiles.
- **List** all existing profiles in the vault.
- **Activate** a specific profile to change the active GCP configuration.
- **Delete** profiles when they are no longer needed.

---

## Installation

You can install `gcp-profiles` using `pip`.

```bash
pip install gcp-profiles
```

---

## Prerequisites

Google Cloud CLI (`gcloud`): The `gcloud` command-line tool must be installed and accessible in your system's `PATH`. This tool is essential as `gcp-profiles` relies on it for profile management and authentication.

---

## Usage

The main command is gcp-profiles. Below are the available subcommands and their usage.

### 1. Creating a Profile

Registers a new authentication profile in the vault. If the profile already exists, you must use the `--force` option to overwrite it.

```bash
gcp-profiles create my-new-profile --force
```

Now a new `gcloud` configuration and new application default credentials have been stored as the `my-new-profile` profile.

### 2. Listing Profiles

Displays the names of all profiles currently stored in the vault.

```bash
gcp-profiles list
```

### 3. Activating a Profile
Sets the specified profile as the active GCP configuration, making it the one used by subsequent `gcloud` commands and application authentication.

```bash
gcp-profiles activate my-new-profile
```

### 4. Deleting a Profile
Permanently removes a profile from the vault.

```Bash
gcp-profiles delete my-new-profile
```