# Command Recipes

Follow these steps to validate and submit your Markdown codelab.

## Environment Setup

Always start with authentication and sourcing the DevSite aliases:

```bash
gcert
# source /google/src/head/depot/google3/devsite/two/tools/aliases.sh # Google-internal only
```

## Local Validation (claat)

Use `claat` to verify the rendering of your `.lab.md` files:

-   **`claat export -f html index.lab.md`**: Run this inside the codelab directory. It will generate an `index.html` and other assets. Check the stdout for parsing errors.
-   **`claat serve`**: Start a local web server (defaults to port 9090). This renders the codelab in a browser just as it would appear on DevSite.

## PIPER/CL Lifecycle (hg/fig)

As Markdown codelabs are source code, use the standard Piper commands:

-   **`hg citc {workspace_name}`**: Create a workspace.
-   **`hg add index.lab.md OWNERS`**: Add new files.
-   **`hg upload`**: Create the CL and upload to Piper.

## DevSite Staging (devsite2)

Wait for the CL to be uploaded, then stage it for a live preview:

```bash
devsite2 stage --cl {cl_number}
```

This command will output a staging URL (e.g., `https://{user}-staging.corp.google.com/codelabs/{id}`). Review the staged content to ensure formatting and images are correct.
