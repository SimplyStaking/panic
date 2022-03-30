export const HelperAPI = {
    arrayEquals: arrayEquals,
    addTitleToSVCSelect: addTitleToSVCSelect,
    updateTextSVCSelect: updateTextSVCSelect,
    dateTimeStringToTimestamp: dateTimeStringToTimestamp,
    getCurrentTimestamp: getCurrentTimestamp,
    formatBytes: formatBytes,
    logFetchError: logFetchError
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
    if ('error' in result){
        console.error(`Error getting ${component} - ${result['error']}`);
    } else {
        console.error(`Error getting ${component} - ${result}`);
    }
}
