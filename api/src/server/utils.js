"use strict";
// These functions wrap a result or an error as an object
Object.defineProperty(exports, "__esModule", { value: true });
exports.Severities = exports.ERR_STATUS = exports.SUCCESS_STATUS = exports.allElementsInListHaveTypeString = exports.getElementsNotInList = exports.allElementsInList = exports.missingValues = exports.toBool = exports.errorJson = exports.resultJson = void 0;
var resultJson = function (result) { return ({ result: result }); };
exports.resultJson = resultJson;
var errorJson = function (error) { return ({ error: error }); };
exports.errorJson = errorJson;
// Transforms a string representing a boolean as a boolean
var toBool = function (boolStr) { return ['true', 'yes', 'y'].some(function (element) { return boolStr.toLowerCase().includes(element); }); };
exports.toBool = toBool;
// Checks which keys have values which are missing (null, undefined) in
// a given object and returns an array of keys having missing values.
var missingValues = function (object) {
    var missingValuesList = [];
    Object.keys(object).forEach(function (key) {
        if (object[key] == null) {
            missingValuesList.push(key);
        }
    });
    return missingValuesList;
};
exports.missingValues = missingValues;
var allElementsInList = function (elements, list) {
    var resultList = elements.map(function (element) {
        return list.includes(element);
    });
    return resultList.every(Boolean);
};
exports.allElementsInList = allElementsInList;
var getElementsNotInList = function (elements, list) {
    return elements.filter(function (element) { return !list.includes(element); });
};
exports.getElementsNotInList = getElementsNotInList;
var allElementsInListHaveTypeString = function (list) {
    return list.every(function (item) { return typeof (item) === "string"; });
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
