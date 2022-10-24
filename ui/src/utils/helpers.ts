import {API_URL, BASE_CHAIN_FULL_NAMES} from "./constants";
import {ColorType} from "@simply-vc/uikit/dist/types/types/color";
import {ChipType} from "@simply-vc/uikit/dist/types/types/chip";
import {Router} from "stencil-router-v2";
import {SelectOptionType} from "@simply-vc/uikit/dist/types/types/select";
import {Generic} from "../../../entities/ts/Generic";
import {RepositorySubconfig} from "../../../entities/ts/RepositorySubconfig";
import {Channel} from "../../../entities/ts/channels/AbstractChannel";

export const HelperAPI = {
    arrayEquals: arrayEquals,
    addTitleToSVCSelect: addTitleToSVCSelect,
    updateTextSVCSelect: updateTextSVCSelect,
    dateTimeStringToTimestamp: dateTimeStringToTimestamp,
    getCurrentTimestamp: getCurrentTimestamp,
    formatBytes: formatBytes,
    logFetchError: logFetchError,
    isFirstInstall: isFirstInstall,
    saveLocalStorage: saveLocalStorage,
    getLocalStorage: getLocalStorage,
    emitEvent: emitEvent,
    raiseToast: raiseToast,
    getBaseChainFullName: getBaseChainFullName,
    extractChipTypeArrayFromCommaSeparatedString: extractChipTypeArrayFromCommaSeparatedString,
    extractStringArrayFromObjectProperties: extractStringArrayFromObjectProperties,
    isFromInstaller: isFromInstaller,
    isFromSettings: isFromSettings,
    isFromSettingsNew: isFromSettingsNew,
    generateSelectOptionTypeOptions: generateSelectOptionTypeOptions,
    getUrlPrefix: getUrlPrefix,
    changePage: changePage,
    executeWithFailureFeedback: executeWithFailureFeedback,
    isDockerhub: isDockerhub,
    isTruthy: isTruthy,
    isDuplicateName: isDuplicateName,
    isConfigEnabledOnChannel: isConfigEnabledOnChannel,
    differenceBetweenTwoObjects: differenceBetweenTwoObjects,
    isFromSettingsEdit: isFromSettingsEdit
}

/**
 * Checks whether two arrays are equal. This includes the order of the
 * elements within the array since arrays are not sorted beforehand.
 * @param array1 first array to compare
 * @param array2 second array to compare
 * @returns true if arrays are equal, false if not.
 */
function arrayEquals(array1: any[], array2: any[]) {
    return array1.length === array2.length && array1.every(
        (val, index) => val === array2[index]);
}

/**
 * Adds a title to the right-hand side of an svc-select element.
 * @param id id of svc-select element to be updated.
 * @param title title to be added to specified svc-select.
 */
function addTitleToSVCSelect(id: string, title: string): void {
    const select = document.querySelector(`#${id} ion-select`);
    if (select) {
        const shadow = select.shadowRoot;
        const selectText = shadow.querySelector('.select-text');
        const selectIcon = shadow.querySelector('.select-icon');
        const selectTextTitle = selectText.cloneNode() as Element;
        selectTextTitle.classList.remove('select-text');
        selectTextTitle.classList.add('select-text-title');
        selectTextTitle.setAttribute('part', 'text-title');
        selectTextTitle.textContent = title;
        shadow.insertBefore(selectTextTitle, selectIcon);
    }
}

/**
 * Updates the select text of an svc-select element.
 * @param id id of svc-select element to be updated.
 * @param allSelected whether to set text to all or to the values selected.
 */
function updateTextSVCSelect(id: string, allSelected: boolean): void {
    const select = document.querySelector(`#${id} ion-select`);
    if (select) {
        const shadow = select.shadowRoot;
        const selectText = shadow.querySelector('.select-text');

        if (allSelected) {
            selectText.textContent = 'All';
        } else {
            const label = shadow.querySelector('label');
            selectText.textContent = label.textContent;
        }
    }
}

/**
 * Converts a date time string into a timestamp (in seconds).
 * @param dateTime data time string to be converted.
 * @returns unix timestamp.
 */
function dateTimeStringToTimestamp(dateTime: string): number {
    return Math.round(Date.parse(dateTime) / 1000);
}

/**
 * Returns the current timestamp (in seconds).
 * @returns current unix timestamp.
 */
function getCurrentTimestamp(): number {
    return Math.round(Date.now() / 1000);
}

/**
 * Formats a given string which contains a value in bytes into a string with
 * the correct size unit (KB/MB/GB..), i.e. a human readable string.
 * @param value string with bytes value.
 * @param decimals the number of decimal points of the returned value.
 * @returns formatted string.
 */
function formatBytes(value: string, decimals: number = 2): string {
    const bytes: number = parseFloat(value);
    if (isNaN(bytes)) return null;
    if (bytes === 0) return '0 Bytes';

    return formatBytesToString(bytes, decimals);
}

/**
 * Formats bytes value into a string with the correct size unit (KB/MB/GB..),
 * i.e. a human readable string.
 * @param bytes bytes value.
 * @param decimals the number of decimal points of the returned value.
 * @returns formatted string.
 */
function formatBytesToString(bytes: number, decimals: number): string {
    const sizes: string[] = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];

    const i: number = calculateI(bytes);

    return `${parseFloat((bytes / Math.pow(1024, i)).toFixed(decimals))} ${sizes[i]}`
}

/**
 * Calculates I, which is a value from 0 to 8 where each number represents
 * a multiple-byte unit (Bytes/KB/MB/GB/TB/PB/EB/ZB/YB).
 * @param bytes bytes value.
 * @returns I value where 0 = Bytes, 1 = KB, 2 = MB...
 */
function calculateI(bytes: number): number {
    return Math.floor(Math.log(bytes) / Math.log(1024));
}

/**
 * Logs fetch errors given the result in JSON and the component name.
 * @param result JSON object return from fetch request.
 * @param component name of the component.
 */
function logFetchError(result: any, component: string) {
    if ('error' in result) {
        console.error(`Error getting ${component} - ${result['error']}`);
    } else {
        console.error(`Error getting ${component} - ${result}`);
    }
}

/**
 * Checks if PANIC is running for the first time.
 *
 * @returns `true` if it's the first run, otherwise `false`
 */
async function isFirstInstall(): Promise<any> {
    try {
        const result: Response = await fetch(
            `${API_URL}v1/installation/is-first`);
        const isFirstInstall = await result.json();
        return isFirstInstall['result'];
    } catch (error: any) {
        console.error('Error when detecting PANIC first installation - ', error);
    }
}

/**
 * This function will `stringify` the `value` param and save it in the index defined by `key` in the local storage (browser cache).
 *
 * @param key name of the key where the value will be saved
 * @param value the value to be "stringfied" and saved
 */
function saveLocalStorage(key: string, value: any): void {
    try {
        const _value: string = JSON.stringify(value);

        if (window && window.localStorage) {
            localStorage.setItem(key, _value);
        }
    } catch (error) {
        console.error("Error while calling 'saveLocalStorage()' function", error);
    }
}

/**
 * Returns a previously value saved in the browser local storage at the index referred by `key` param.
 *
 * @param key name of the key that represents the value to be returned
 * @returns any value that has been previously stringfied
 */
function getLocalStorage(key: string): any {
    try {
        if (window && window.localStorage) {
            return JSON.parse(localStorage.getItem(key));
        }
    } catch (error) {
        console.error("Error while calling 'getLocalStorage()' function", error);
    }
}

/**
 * It broadcasts an event called `eventName` from {@link window} passing `data` as argument.
 *
 * @param eventName The event's name.
 * @param data The argument passed with the event.
 */
function emitEvent(eventName: string, data?: any): void {
    const ev: CustomEvent = new CustomEvent(eventName, { detail: data });
    window.dispatchEvent(ev);
}

/**
 * Creates a toast notification via the svc-toast component.
 *
 * @param message The message to be displayed in the toast.
 * @param duration The duration of the toast notification in milliseconds, default is 2000ms.
 * @param color The color of the toast, default is success.
 */
export function raiseToast(message: string, duration: number = 2000, color: ColorType = "success"): void {
    const toast = document.createElement("svc-toast");
    toast.message = message;
    toast.duration = duration;
    toast.color = color;
    document.getElementsByTagName("body")[0].appendChild(toast);
}

/**
 * Gets the full name of the base chain based on the name-value object pair.
 * @returns a string representing the full base chain name.
 */
function getBaseChainFullName(baseChain: string): string {
    return BASE_CHAIN_FULL_NAMES[baseChain.toLowerCase()];
}

/**
 * Extracts various values from a comma separated string into an array of {@link ChipType} objects.
 *
 * @param commaSeparatedString The comma separated string which contains the properties to be extracted.
 * @param chipOutline What the outline property of the {@link ChipType} object should be set to.
 *
 * @returns populated array of {@link ChipType} objects
 */
function extractChipTypeArrayFromCommaSeparatedString(commaSeparatedString: string, chipOutline: boolean=false): ChipType[] {
    const chips: ChipType[] = []

    if (commaSeparatedString !== "")
        commaSeparatedString?.split(',').forEach((value) => {
            chips.push({
                label: value,
                value: value,
                outline: chipOutline
            });
        });

    return chips;
}

/**
 * Extracts various object properties with a given prefix into an array of strings.
 *
 * @param propertyPrefix The prefix of the properties to be extracted.
 * @param object The object which contains the properties to be extracted.
 */
function extractStringArrayFromObjectProperties(propertyPrefix: string, object: object): string[] {
    const strings: string[] = []
    let index = 0;

    while (object) {
        const propertyKey = `${propertyPrefix}_${index}`;
        if (propertyKey in object) {
            const value = object[propertyKey];
            strings.push(value);
        } else {
            break;
        }
        index++;
    }

    return strings;
}

/**
 * Any installer component is shared between three diff routes:
 * - During the installer (/installer) journey
 * - When adding a new sub-chain (/settings/new)
 * - When editing any sub-chain (/settings)
 *
 * This function determines where the navigation is coming from.
 *
 * @returns a string representing the prefix of the URL (since the last part
 * changes on every component)
 */
function getUrlPrefix(): string {
    if (HelperAPI.isFromSettingsNew()){
        return "/settings/new"
    } else if (HelperAPI.isFromInstaller()) {
        return "/installer"
    } else if (HelperAPI.isFromSettings()) {
        return "/settings/edit"
    } else {
        return "/"
    }
}

/**
 * Checks if the action using the component came from
 * `Settings > Chains > Add a Subchain`.
 *
 * @returns `true` when navigating to this component coming from
 * `Settings > Chains > Add new Subchain`, otherwise `false`.
 */
function isFromSettingsNew() {
    return window.location.pathname.indexOf("settings/new/") !== -1;
}

/**
 * Checks if the action using the component came from `Settings > Chains`.
 *
 * @returns `true` when navigating to this component coming from
 * `Settings > Chains`, otherwise `false`.
 */
function isFromSettings() {
    return window.location.pathname.indexOf("settings/") !== -1;
}

/**
 * Checks if the action using the component came from the installer journey.
 *
 * @returns `true` when navigating to this component coming from the installer,
 * otherwise `false`.
 */
function isFromInstaller() {
    return window.location.pathname.indexOf("installer/") !== -1;
}

/**
 * Uses the Stencil Router {@link Router} to navigate to a webpage.
 */
function changePage(router: Router, pageToNavigateTo: string): void{
    router.push(pageToNavigateTo);
}

/**
 * This function will execute the 'callback' if 'condition' is true. Otherwise,
 * it will raise a 'toastMsg' for 'toastDuration' with 'toastColor' color
 * @param condition The test condition
 * @param callback The function to execute if 'condition' is true
 * @param toastMsg The toast msg
 * @param toastDuration The toast duration
 * @param toastColor The toast color
 */
async function executeWithFailureFeedback(
    condition: boolean, callback: Function, toastMsg: string,
    toastDuration: number, toastColor: ColorType | undefined): Promise<void> {

    if (condition) {
        await callback()
    } else {
        raiseToast(toastMsg, toastDuration, toastColor)
    }
}

/**
 * Generate SelectOptionType for a given array of a generic object.
 * @returns SelectOptionType to be rendered in the svc-select.
 */
function generateSelectOptionTypeOptions(dataToMap: Array<Generic>): SelectOptionType{
    return dataToMap.map(entity => ({
        value: entity.id,
        label: entity.name,
    }))
}

/**
 * Whether the repository is of the type DockerHub.
 * @param repository the RepositorySubconfig containing the object
 * @returns boolean
 */
function isDockerhub(repository: RepositorySubconfig): boolean {
    return repository.type.value === 'dockerhub';
}

/**
 * Checks whether a given value is truthy (`"true"` or `true`).
 * @param value The value to be checked
 * @returns `true` if truthy, `false` if value not undefined, else `null`
 */
function isTruthy(value: any): boolean{
    return value !== undefined ? value === "true" || value === true : null;
}

/**
 * Check whether the API response indicates a duplicate name.
 * @param response The Response object
 * @returns boolean
 */
function isDuplicateName(response: Response): boolean {
    return response.status === 409
}

/**
 * Check whether the config is enabled on a channel.
 * @param channel The channel to test
 * @param configId The configuration id
 * @returns boolean
 */
function isConfigEnabledOnChannel(channel: Channel, configId: string): boolean {
    return channel.configs.some(
      (enabledConfig) => configId === enabledConfig.id);
}

/**
 * Obtain the key-value pairs between objects which have identical keys,
 * but may have altering corresponding values.
 * @param object1 The channel to test
 * @param object2 The configuration id
 * @returns object difference containing string key-value pairs
 */
function differenceBetweenTwoObjects(object1: object, object2: object): object {
    const difference = {};
    Object.keys(object1).forEach(key => {
        if(!Object.keys(object2).includes(key) || object1[key] !== object2[key]){
            difference[key] = object1[key];
        }
    });
    return difference;
}

/**
 * Check if the user is currently accessing the chain's settings in "edit mode".
 * 
 * @returns `true` when in "edit mode", otherwise `false`.
 */
function isFromSettingsEdit(): boolean {
    return window.location.pathname.indexOf("/settings/edit") !== -1;
}