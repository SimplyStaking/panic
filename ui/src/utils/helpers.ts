/**
 * Checks whether two arrays are equal. This includes the order of the
 * elements within the array since arrays are not sorted beforehand.
 * @returns true if arrays are equal, false if not.
 */
export function arrayEquals(a: any[], b: any[]) {
    return a.length === b.length &&
        a.every((val, index) => val === b[index]);
}