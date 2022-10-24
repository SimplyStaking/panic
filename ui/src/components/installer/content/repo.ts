export type RepoRequestBody = {
  id: string,
  repositories: Array<{
      id?: string,
      name: string,
      namespace: string,
      type: string,
      monitor: boolean,
    }>,
}

export const REPO_TABLE_HEADERS = [
  {
    title: "Repository Type",
    sortable: true
  },
  {
    title: "Name",
    sortable: true
  },
];
export const MORE_INFO_MESSAGES = [
  {
    title: "Repositories",
    messages: [
      "Currently, PANIC supports GitHub and DockerHub repository types.",
    ]
  },
  {
    title: "GitHub",
    messages: [
      "For Github, you will receive alerts for new releases on monitored repositories. To do so, enter the repository using a trailing forward-slash (/)." +
      "For example, https://xxxxxx/aaaaa/bbbbbb/  -  use  aaaaa/bbbbbb/ into the [name of the field] field.",
    ]
  },
  {
    title: "DockerHub",
    messages: [
      "For DockerHub, you will receive alerts for any new, modified, or deleted tag on monitored repositories. " +
      "To do so, input using the format: {repo-namespace}/{repo-name}." +
      "The 'repo-namespace' is usually the username that owns the repository. If no repo-namespace is given, then the default used will be library/{repo-name}. " +
      "For example, entering 'panic' will default to 'library/panic'.",
    ]
  },
  {
    title: "Default Settings",
    messages: [
      "The default monitoring period of both GitHub and DockerHub API is 1 hour."
    ]
  },
];
export const MAIN_TEXT = `PANIC allows you to monitor GitHub and DockerHub repositories for new releases/tags respectively.`