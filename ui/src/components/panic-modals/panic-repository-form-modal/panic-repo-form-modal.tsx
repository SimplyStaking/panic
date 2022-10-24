import {dismissModal, parseForm} from '@simply-vc/uikit';
import {Component, h, State, Prop} from '@stencil/core';
import {HelperAPI} from "../../../utils/helpers";
import {RepositorySubconfig} from "../../../../../entities/ts/RepositorySubconfig";
import {RepositoryType} from "../../../../../entities/ts/RepositoryType";
import {SelectOptionType} from "@simply-vc/uikit/dist/types/types/select";

@Component({
  tag: 'panic-repo-form-modal',
  styleUrl: 'panic-repo-form-modal.scss'
})
export class PanicRepoFormModal {

  @State() repoNameToPing: string;

  /**
   * Aids with edit functionality by giving the ability for RepositorySubconfig
   * objects to be passed to the modal, with the object data rendered in the form.
   */
  @Prop() repository: RepositorySubconfig;

  /**
   * RepositoryType list containing the generic Repository data.
   */
  @Prop() repositoryTypes: RepositoryType[];

  /**
   * Whether form submission is permitted.
   */
  @State() allowSubmit: boolean;

  /**
   * The type of repository selected.
   */
  @State() selectedRepositoryType: RepositoryType;

  updateRepoNameToPing(repoName: string): void{
    this.repoNameToPing = repoName;
  }

  /**
   * Get the RepositoryType object associated with the given id
   * @param id representing the repository
   * @returns RepositoryType
   */
  getRepositoryTypeById(id: string): RepositoryType {
    return this.repositoryTypes.find(repositoryType => repositoryType.id === id);
  }

  /**
   * Helper function for Dockerhub which extracts a namespace and name from
   * a given string.
   * @param nameAndNamespace string in these possible formats: 'namespace/name' or 'name'
   * @returns an array of strings containing the namespace and name in consecutive elements.
   */
  getDockerhubNamespaceAndName(nameAndNamespace: string): Array<string>{
    if(!nameAndNamespace.includes('/')) {
      return ['library', nameAndNamespace]
    }
    return nameAndNamespace.split('/');
  }

  /**
   * Parse the repository data from the form into a RepositorySubconfig object
   * along with the associated id
   * @param repositoryFormData the repository data submitted via the form
   * @returns RepositorySubconfig object
   * @returns the repository id being edited, if any
   */
  parseRepositoryFormData(repositoryFormData: any): [RepositorySubconfig, string] {
    const repository: RepositorySubconfig = new RepositorySubconfig();

    repository.name = repositoryFormData.name;
    repository.monitor = repositoryFormData.monitor;
    repository.type = this.getRepositoryTypeById(repositoryFormData.type);
    if(HelperAPI.isDockerhub(repository)){
      const [namespace, name] = this.getDockerhubNamespaceAndName(repositoryFormData.name);
      repository.namespace = namespace;
      repository.name = name;
    }

    return [repository, repositoryFormData.id];
  }

  onSubmitHandler(e: Event){
    e.preventDefault();

    const form = e.target as HTMLFormElement;
    const formData = parseForm(form);
    let [repository, id]: [RepositorySubconfig, string] = this.parseRepositoryFormData(formData);

    HelperAPI.emitEvent("onSave", {
      repositoryObject: repository,
      repositoryId: id,
    });
  }

  /**
   * Generate the full repo namespace/name format.
   * @returns string
   */
  generateFullRepoName(): string{
    if(HelperAPI.isDockerhub(this.repository)){
      return `${this.repository.namespace}/${this.repository.name}`
    } else {
      return this.repository.name;
    }
  }

  /**
   * Generate the SelectOptionType to be used within svc-select.
   * @returns SelectOptionType
   */
  generateSelectRepoTypeOptions(): SelectOptionType{
    return this.repositoryTypes.map(repositoryType => ({
      value: repositoryType.id,
      label: repositoryType.name,
    }))
  }

  /**
   * Setting the class of the modal based on whether the repository type is selected.
   */
  updateModalClassRepoSelected() {
    const repoSelectedClass = "panic-repo-form-modal__repo-selected";
    const ionModal = document.getElementsByTagName("ion-modal")[0];
    ionModal.classList.add(repoSelectedClass);
  }

  componentWillLoad(){
    if (this.repository) {
      this.allowSubmit = true;
      this.repoNameToPing = this.repository.name;
      this.selectedRepositoryType = this.getRepositoryTypeById(this.repository.type.id);

      this.updateModalClassRepoSelected();
    } else {
      this.allowSubmit = false;
    }
  }

  render() {
    return (
      <svc-content-container class={"panic-repo-form-modal"}>
        <form onSubmit={(e: Event) => {this.onSubmitHandler(e)}}>
          <fieldset>
            {
              this.repository &&
                <input type={'hidden'} name={'id'} value={this.repository.id}/>
            }
            <legend>
              {
                this.repository
                ? "Edit Repository"
                : "New Repository"
              }
            </legend>
            <svc-select
              name={"type"}
              id={"type"}
              withBorder={true}
              placeholder={
                this.repository
                  ? this.repository.type.name
                  : "Choose repository type..."
              }
              value={this.repository && this.repository.type.id}
              disabled={this.repository && true}
              //@ts-ignore
              required={!this.repository && true}
              header={!this.repository && "Repository Type"}
              options={!this.repository && this.generateSelectRepoTypeOptions()}
              onIonChange={(e: CustomEvent) => {
                if(!this.repository){
                  this.allowSubmit = true;
                  this.selectedRepositoryType = this.getRepositoryTypeById(e.detail.value);
                  this.updateModalClassRepoSelected();
                }
              }}
            />
            {
              this.repository &&
                <input type={"hidden"} value={this.repository.type.id} name={"type"}/>
            }

            <svc-input
              name={"name"}
              label={"Repository Name"}
              lines={"full"}
              required={true}
              placeholder={"simply/panic"}
              value={this.repository && this.generateFullRepoName()}
              // @ts-ignore
              onInput={(event) => this.updateRepoNameToPing(event.target.value)}
              pattern={"^[0-9a-zA-Z-_.]+$|^[0-9a-zA-Z-_.]+(\\/[0-9a-zA-Z-_.]+)$"}
              title={this.selectedRepositoryType?.value === 'dockerhub'
                ? "For Dockerhub, input must be in the format 'namespace/name' (for example SimplyVC/panic) " +
                  "or 'name' (panic). In the latter case, the 'namespace' will default to 'library' (for example " +
                  "library/panic)."
                : "For GitHub, input must be in the format 'namespace/name' (for example SimplyVC/panic) " +
                "or 'name' (panic)."
              }
            />

            <svc-toggle
              name={'monitor'}
              value={true}
              label={'Monitor'}
              lines={'none'}
              checked={this.repository ? this.repository.monitor : true}
              id={'monitor'}
            />

            {
              this.selectedRepositoryType &&
              <panic-installer-test-button
                // @ts-ignore
                service={this.selectedRepositoryType.value}
                pingProperties={
                  {
                    'name':
                      this.selectedRepositoryType.value === 'dockerhub' && this.repoNameToPing
                    ? this.getDockerhubNamespaceAndName(this.repoNameToPing).join('/')
                    : this.repoNameToPing}
                }
                identifier={this.repoNameToPing}
              />
            }

            <div class={"panic-repo-form-modal__buttons-container"}>
              <svc-button iconName='checkmark' color={"primary"} disabled={!this.allowSubmit} type='submit'>Submit</svc-button>
              <svc-button iconName='close' color={"primary"} role={"cancel"} onClick={() => {dismissModal()}}>Cancel</svc-button>
            </div>
          </fieldset>
        </form>
      </svc-content-container>
    );
  }
}