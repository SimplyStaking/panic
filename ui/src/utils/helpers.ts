/**
 * Checks whether two arrays are equal. This includes the order of the
 * elements within the array since arrays are not sorted beforehand.
 * @returns true if arrays are equal, false if not.
 */
export function arrayEquals(a: any[], b: any[]) {
    return a.length === b.length &&
        a.every((val, index) => val === b[index]);
}

/**
 * Adds a title to the right-hand side of an svc-select element.
 * @param id id of svc-select element to be updated.
 * @param title title to be added to specified svc-select.
 */
export function addTitleToSVCSelect(id: string, title: string): void {
    const shadow = document.querySelector(`#${id} ion-select`).shadowRoot;
    const selectText = shadow.querySelector('.select-text');
    const selectIcon = shadow.querySelector('.select-icon');
    const selectTextTitle = selectText.cloneNode() as Element;
    selectTextTitle.classList.remove('select-text');
    selectTextTitle.classList.add('select-text-title');
    selectTextTitle.setAttribute('part', 'text-title');
    selectTextTitle.textContent = title;
    shadow.insertBefore(selectTextTitle, selectIcon);
}
