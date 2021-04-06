"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Severities = exports.ERR_STATUS = exports.SUCCESS_STATUS = exports.allElementsInListHaveTypeString = exports.getElementsNotInList = exports.allElementsInList = exports.missingValues = exports.toBool = exports.errorJson = exports.resultJson = void 0;
const resultJson = (result) => ({ result });
exports.resultJson = resultJson;
const errorJson = (error) => ({ error });
exports.errorJson = errorJson;
// Transforms a string representing a boolean as a boolean
const toBool = (boolStr) => ['true', 'yes', 'y'].some((element) => boolStr.toLowerCase().includes(element));
exports.toBool = toBool;
// Checks which keys have values which are missing (null, undefined, '') in
// a given object and returns an array of keys having missing values.
const missingValues = (object) => {
    let missingValuesList = [];
    Object.keys(object).forEach((key) => {
        if (!object[key]) {
            missingValuesList.push(key);
        }
    });
    return missingValuesList;
};
exports.missingValues = missingValues;
const allElementsInList = (elements, list) => {
    const resultList = elements.map((element) => {
        return list.includes(element);
    });
    return resultList.every(Boolean);
};
exports.allElementsInList = allElementsInList;
const getElementsNotInList = (elements, list) => {
    return elements.filter(element => !list.includes(element));
};
exports.getElementsNotInList = getElementsNotInList;
const allElementsInListHaveTypeString = (list) => {
    return list.every(item => typeof (item) === "string");
};
exports.allElementsInListHaveTypeString = allElementsInListHaveTypeString;
exports.SUCCESS_STATUS = 200;
exports.ERR_STATUS = 400;
var Severities;
(function (Severities) {
    Severities["INFO"] = "INFO";
    Severities["WARNING"] = "WARNING";
    Severities["CRITICAL"] = "CRITICAL";
    Severities["ERROR"] = "ERROR";
})(Severities = exports.Severities || (exports.Severities = {}));
