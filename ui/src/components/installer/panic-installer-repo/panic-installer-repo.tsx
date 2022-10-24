import {Component, h, Host, Listen, Prop, State} from '@stencil/core';
import {createAlert, createModal, dismissModal} from "@simply-vc/uikit";
import {HelperAPI} from "../../../utils/helpers";
import {MAIN_TEXT, MORE_INFO_MESSAGES, REPO_TABLE_HEADERS} from "../content/repo";
import {DataTableRowsType} from "@simply-vc/uikit/dist/types/types/datatable";
import {Config} from "../../../../../entities/ts/Config";
import {RepositorySubconfig} from "../../../../../entities/ts/RepositorySubconfig";
import {ConfigService} from "../../../services/config/config.service";
import {RepositoryType} from "../../../../../entities/ts/RepositoryType";
import {Router} from "stencil-router-v2";

@Component({
  tag: 'panic-installer-repo',
  styleUrl: 'panic-installer-repo.scss'
})
export class PanicInstallerRepo {

  /**
   * The identifier used to represent the Config.
   */
  @Prop() configId: string;

  /**
   * Stencil Router object for page navigation.
   */
  @Prop() router: Router;

  /**
   * List containing the Generic Repository Types.
   */
  @Prop() repositoryTypes: RepositoryType[];

  /**
   * The Config object being read & modified.
   */
  @State() config: Config;

  /**
   * Generates a request body to be sent via API.
   * @returns a request object containing the config id and the parsed list of
   * repositories to be sent via the API.
   */
  createRepoRequestBody(): object {
    const repositories = this.config.repositories.map(repository => {
      return {
        id: repository.id,
        name: repository.name,
        namespace: repository.namespace,
        type: repository.type.id,
        monitor: HelperAPI.isTruthy(repository.monitor),
      }
    });

    repositories.forEach(repository=>{
      if(!repository.id){
        delete repository.id;
      }
    })

    return {
      id: this.config.id,
      repositories: repositories,
    };
  }

  /**
   * Save the list of repositories within the config object via the API.
   *
   * @returns the response of the save operation via the API
   */
  async save(): Promise<Response>{
    const requestBody = this.createRepoRequestBody();

    return await ConfigService.getInstance().save(requestBody as Config);
  }

  /**
   * Deletes the repository indicated by the id.
   * @param id the id of the repository to be deleted from in the list
   * @returns the updated RepositorySubconfig[]
   */
  deleteRepositoryFromConfig(id: string): RepositorySubconfig[]{
    return this.config.repositories.filter(repository => repository.id !== id);
  }

  /**
   * Get the repository indicated by the id
   * @param id the id of the repository to be returned
   * @returns RepositorySubconfig that matches the given id
   */
  getRepositoryById(id: string): RepositorySubconfig {
    return this.config.repositories.find((repository) => repository.id === id);
  }

  /**
   * Listens to an event for when a new repo is added/edited via the repo form modal.
   * @param event The event sent by panic-repo-form-modal.
   */
  @Listen("onSave", { target: 'window' })
  async onSaveHandler(event: CustomEvent){
    const repository = event.detail.repositoryObject;
    const id = event.detail.repositoryId;

    //An id indicates that it is an edit scenario. Thus, remove the original repository object from the list.
    //The updated object will be added to this updated list, overall resulting in an update.
    if(id) {
      this.config.repositories = this.deleteRepositoryFromConfig(id);
    }
    this.config.repositories.push(repository);

    const resp = await this.save();

    if(HelperAPI.isDuplicateName(resp)) {
      HelperAPI.raiseToast(
          `A repository named '${repository.name}' already exists!`,
          2000,
          "warning");
      this.config.repositories.pop();
    } else {
      await this.getConfig();
      HelperAPI.raiseToast("Repository added");
      await dismissModal();
    }
  }

  /**
   * Listens to an event sent from the repositories data table when a user clicks an edit button.
   * @param event The event sent by svc-data-table edit functionality.
   */
  @Listen("repositoriesTableEdit", {target: "window"})
  async repositoriesTableEditHandler(event: CustomEvent){
    const repositoryId: string = event.detail.id;
    const repository: RepositorySubconfig = this.getRepositoryById(repositoryId);

    await createModal("panic-repo-form-modal", {
      repositoryTypes: this.repositoryTypes,
      repository: repository,
    }, {backdropDismiss: false});
  }

  /**
   * Listens to an event sent from the repositories data table when a user clicks a delete button.
   * @param event The event sent by svc-data-table deletion functionality.
   */
  @Listen("repositoriesTableDelete", {target: "window"})
  async repositoriesTableDeleteHandler(event: CustomEvent): Promise<void> {
    const repositoryId: string = event.detail.id;
    const repository: RepositorySubconfig = this.getRepositoryById(repositoryId);

    await createAlert({
      header: "Attention",
      message: `Are you sure you want to delete the ${repository.type.name} channel: ${repository.name}?`,
      eventName: 'deleteRepo',
      eventData: {id: repository.id}
    });
  }

  /**
   * Listens to an event sent from the alert created in {@link repositoriesTableDeleteHandler}.
   * @param event The event sent by the delete repository alert.
   */
  @Listen("deleteRepo", { target: 'window' })
  async channelDeleteHandler(event: CustomEvent){
    if(event.detail.confirmed){
      const repositoryId: string = event.detail.data.id;

      this.config.repositories = this.deleteRepositoryFromConfig(repositoryId);

      await this.save();

      await this.getConfig();

      HelperAPI.raiseToast("Repository deleted");
      await dismissModal();
    }
  }

  @Listen("previousStep", {target: "window"})
  previousStepHandler() {
    HelperAPI.changePage(this.router, `${
        HelperAPI.getUrlPrefix()}/sources/${this.configId}`);
  }

  @Listen("nextStep", {target: "window"})
  async nextStepHandler() {
    HelperAPI.changePage(this.router, `${
        HelperAPI.getUrlPrefix()}/alerts/${this.configId}`);
  }

  /**
   * Returns the full name of the repository.
   * For example, in the case of Dockerhub, it returns the namespace/name.
   * Otherwise, returns the name.
   * @param repository the RepositorySubconfig object
   * @returns string
   */
  getRepoFullName(repository: RepositorySubconfig): string {
    if(HelperAPI.isDockerhub(repository)){
      return `${repository.namespace}/${repository.name}`;
    } else {
      return repository.name;
    }
  }

  /**
   * Generates data table rows containing the repository data.
   * @returns DataTableRowsType legible by the svc-data-table.
   */
  repositoryToDataTableRowsType(): DataTableRowsType{
    return this.config.repositories.map(repository => ({
      cells: [
        {
          value: repository.type.value,
          label: repository.type.name,
        },
        {
          value: this.getRepoFullName(repository),
          label: this.getRepoFullName(repository),
        },
      ],
      id: repository.id
    }));
  }

  /**
   * Gets the config object from the API.
   */
  async getConfig() {
    this.config = await ConfigService.getInstance().getByID(this.configId);
  }

  async componentWillLoad() {
    // might be necessary
    // i.e. when the node operator opens a modal and then clicks in the browser's back button
    dismissModal();

    await this.getConfig();
  }

  render() {
    return (
      <Host>
        <panic-header showMenu={false} />

        <svc-progress-bar value={0.8} color={"tertiary"}/>

        <svc-content-container class={"panic-installer-repo__container"}>
          <svc-surface>
            <div class={"panic-installer-repo__heading"}>
              <svc-icon name={"code-slash"} size={"120px"} color={"primary"} />
              <svc-label class={"panic-installer-repo__title"}>Repository Setup for {this.config.subChain.name}</svc-label>
              <svc-label class={"panic-installer-repo__step"}>step 4/5</svc-label>
            </div>

            <div class={"panic-installer-repo__text-with-tooltip"}>
              <p>
                {MAIN_TEXT}
              </p>
              <svc-buttons-container>
                <svc-button color={"secondary"} iconName={"information-circle"} iconPosition={"icon-only"} onClick={async () => {
                  await createModal("panic-installer-more-info-modal", {
                    messages: MORE_INFO_MESSAGES,
                    class: "repo",
                  })
                }}/>
              </svc-buttons-container>
            </div>

            <div class={"panic-installer-repo__add-repo-button"}>
              <svc-button id={"add"} iconName={"add-circle"} color={"secondary"} onClick={async () => {
                await createModal("panic-repo-form-modal", {
                  repositoryTypes: this.repositoryTypes
                }, {backdropDismiss: false});
              }}>
                Add Repository
              </svc-button>
            </div>

            {
              this.config.repositories && this.config.repositories.length > 0 &&
                <div class={"panic-installer-repo__crud-data-table"}>
                  <svc-data-table
                    class={"panic-installer-repo__action_icons"}
                    mode={"crud"}
                    cols={REPO_TABLE_HEADERS}
                    noRecordsMessage={"Your configured repositories will show here."}
                    rows={this.repositoryToDataTableRowsType()}
                    editEventName={"repositoriesTableEdit"}
                    deleteEventName={"repositoriesTableDelete"}
                  />
                </div>
            }
          </svc-surface>

          <panic-installer-nav config={this.config} />

        </svc-content-container>

        <panic-footer />
      </Host>
    );
  }
}
