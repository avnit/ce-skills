## 2. Setup and Requirements

Duration: 05:00

### Self-paced environment setup

1.  Sign-in to the [Google Cloud Console](https://console.cloud.google.com/) and create a new project or reuse an existing one. (If you don't already have a Gmail or Google Workspace account, you will need to [create one](https://accounts.google.com/SignUp).)

    - The **Project name** is the display name for this project's participants. It is a character string not used by Google APIs. You can update it at any time.
    - The **Project ID** is unique across all Google Cloud projects and is immutable (cannot be changed after it has been set). The Cloud Console auto-generates a unique string; usually you don't care what it is. In most codelabs, you'll need to reference the Project ID (it's typically identified as `PROJECT_ID`). If you don't like the generated ID, you may generate another random one. Alternatively, you can try your own, and see if it's available. It cannot be changed after this step and remains for the duration of the project.
    - For your information, there is a third value, a **Project Number**, which some APIs use. Learn more about all three of these values in the [documentation](https://cloud.google.com/resource-manager/docs/creating-managing-projects#identifying_projects).

2.  Next, you'll need to enable billing in the Cloud Console to use Cloud resources/APIs. Running through this codelab shouldn't cost much, if anything at all. To shut down resources to avoid incurring billing beyond this tutorial, you can delete the resources you created or delete the whole project. New users of Google Cloud are eligible for the [$300 USD Free Trial](https://cloud.google.com/free) program.

### Activate Cloud Shell

1.  From the Cloud Console, click **Activate Cloud Shell** ![Cloud Shell Icon](img/cloud-shell-icon.png).

2.  If you've never started Cloud Shell before, you're presented with an intermediate screen describing what it is. If that's the case, click **Continue**.

3.  It should only take a few moments to provision and connect to Cloud Shell.

    The virtual machine is loaded with all the development tools you'll need. It offers a persistent 5GB home directory, and runs on the Google Cloud, greatly enhancing network performance and authentication. All of your work in this codelab can be done within the browser.

4.  Once connected to Cloud Shell, you should see that you are already authenticated and that the project is set to your `PROJECT_ID`.

    ```bash
    gcloud auth list
    ```

    **Command output**

    ```console
    Credentialed accounts:
     - <myaccount>@<mydomain>.com (active)
    ```

    ```bash
    gcloud config list project
    ```

    **Command output**

    ```console
    [core]
    project = <PROJECT_ID>
    ```

    **Note:** If the project is not set, you can set it with this command:

    ```bash
    gcloud config set project <PROJECT_ID>
    ```
