// These functions wrap a result or an error as an object
import Type from "module";

export const resultJson = (result: any) => ({result});
export const errorJson = (error: any) => ({error});

// Transforms a string representing a boolean as a boolean
export const toBool = (boolStr: string): boolean => ['true', 'yes', 'y'].some(
    (element) => boolStr.toLowerCase().includes(element));

// Checks which keys have values which are missing (null, undefined, '') in
// a given object and returns an array of keys having missing values.
export const missingValues = (object: { [id: string]: any }): string[] => {
    let missingValuesList: string[] = [];
    Object.keys(object).forEach((key) => {
        if (!object[key]) {
            missingValuesList.push(key);
        }
    });
    return missingValuesList;
};

export const allElementsInList = (elements: any[], list: any[]): boolean => {
    const resultList: boolean[] = elements.map((element: any): boolean => {
        return list.includes(element)
    });
    return resultList.every(Boolean);
};

export const getElementsNotInList = (elements: any[], list: any[]): any[] => {
    return elements.filter(element => !list.includes(element));
};

export const allElementsInListHaveTypeString = (list: any[]): boolean => {
    return list.every(item => typeof(item) === "string")
};

export const SUCCESS_STATUS: number = 200;
export const ERR_STATUS: number = 400;
